from dateutil import tz
import os
import logging
from odoo import models, api, fields, exceptions
import requests
import time
import datetime

from ..controllers.frepplexml import encode_jwt
from .quote import Quote

logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # This field is used to hide/display the quote button
    # in the "Other info" tab of the sales order
    _without_quote = fields.Boolean(
        compute="_compute_without_quote", store=False, default=False
    )

    def _compute_without_quote(self):
        groups = self.env["res.groups"].search([("name", "=", "frePPLe quoting user")])
        if not groups:
            enable_quoting_module = False
        else:
            enable_quoting_module = self.user_id.id in groups.users.ids
        for order in self:
            order._without_quote = order.state != "draft" or not enable_quoting_module

    def use_product_short_names(self):
        # Check if we can use short names
        # To use short names, the internal reference (or the name when no internal reference is defined)
        # needs to be unique
        use_short_names = True

        self.env.cr.execute(
            """
            select count(*) from
            (
            select coalesce(product_product.default_code,
            product_template.name->>%s,
            product_template.name->>'en_US'), count(*)
            from product_product
            inner join product_template on product_product.product_tmpl_id = product_template.id
            where product_template.type not in ('service', 'consu')
            group by coalesce(product_product.default_code,
            product_template.name->>%s,
            product_template.name->>'en_US')
            having count(*) > 1
            ) t
                """,
            (self.env.user.lang, self.env.user.lang),
        )
        for i in self.env.cr.fetchall():
            if i[0] > 0:
                use_short_names = False
                break
        return use_short_names

    def getfrePPLeItemName(self, product, use_short_names):
        if product.code:
            name = (
                (("[%s] %s" % (product.code, product.name))[:300])
                if not use_short_names
                else product.code[:300]
            )
        # product is a variant and has no internal reference
        # we use the product id as code
        elif product.product_template_attribute_value_ids:
            name = ("[%s] %s" % (product.id, product.name))[:300]
        else:
            name = product.name[:300]
        return name

    def action_frepple_quote(self):

        use_short_names = self.use_product_short_names()

        for sale_order in self:

            # -----[ BUILD THE REQUEST BODY ]-----
            request_body = {"demands": []}
            for line in sale_order.order_line:
                if line.product_id.type == "product":
                    product_name = self.getfrePPLeItemName(
                        line.product_id, use_short_names
                    )

                    # Get the due date: commitment date if set or now, in the user timezone
                    sale_order_utc = (
                        sale_order.commitment_date or datetime.datetime.now()
                    ).replace(tzinfo=tz.gettz("UTC"))
                    sale_order_user_tz = sale_order_utc.astimezone(
                        tz.gettz(self.env.user.tz)
                    ).replace(tzinfo=None)

                    due_date = sale_order_user_tz.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

                    request_body["demands"].append(
                        {
                            "name": "%s %s" % (sale_order.name, line.id),
                            "quantity": int(line.product_uom_qty),
                            "description": "",
                            "due": due_date,
                            "item": {"name": product_name},
                            "location": {"name": sale_order.warehouse_id.name},
                            "customer": {
                                "name": "%s %s"
                                % (
                                    sale_order.partner_id.name,
                                    sale_order.partner_id.id,
                                )
                            },
                            "minshipment": int(line.product_uom_qty),
                            "maxlateness": 86400000,
                            "priority": 20,
                            "policy": (
                                "independent"
                                if sale_order.picking_policy == "direct"
                                else "alltogether"
                            ),
                            "owner": (
                                None
                                if sale_order.picking_policy == "direct"
                                else sale_order.name
                            ),
                        }
                    )

            # -----[ CREATE AUTH TOKEN ]-----
            encode_params = dict(
                exp=round(time.time()) + 600, user=sale_order.env.user.login
            )
            user_company_webtoken = sale_order.env.user.company_id.webtoken_key
            if not user_company_webtoken:
                raise exceptions.UserError("FrePPLe company web token not configured")

            base_url = sale_order.env.user.company_id.frepple_server
            if not base_url.endswith("/"):
                base_url += "/"
            if not base_url:
                raise exceptions.UserError("frePPLe web server not configured")

            webtoken = encode_jwt(encode_params, user_company_webtoken)
            if not isinstance(webtoken, str):
                webtoken = webtoken.decode("ascii")

            # -----[ PERFORM THE REQUEST ]-----

            headers = {
                "Authorization": "Bearer " + str(webtoken),
                "Content-Type": "application/json",
            }

            # Choose between quote or inquiry.
            action = "quote"
            # action = "inquiry"

            scenario_url = base_url[:-1].rsplit("/", 1)
            is_scenario = "scenario" in scenario_url[-1].lower()

            if is_scenario:
                base_url = scenario_url[0] + "/"
                scenario = scenario_url[-1]
            else:
                scenario = "default"

            try:
                base_url = base_url.replace("localhost", "host.docker.internal")
                frepple_response = requests.post(
                    (
                        ("%ssvc/%s/quote/%s/" % (base_url, scenario, action))
                        if "8000" not in base_url
                        else (
                            "%squote/%s/"
                            % (
                                base_url.replace("8000", "8002"),
                                action,
                            )
                        )  # Rather ugly logic to recognize development layouts
                    ),
                    headers=headers,
                    json=request_body,
                )
            except Exception:
                raise exceptions.UserError(
                    "The connection with the frePPLe quoting module could not be established"
                )

            response_status_code = frepple_response.status_code
            if response_status_code == 401:
                raise exceptions.UserError("User is not authorized to use FrePPLe")

            try:
                response_json = frepple_response.json()
            except Exception:
                raise exceptions.UserError("Invalid response from frePPLe")
            if not response_json.get("demands"):
                raise exceptions.UserError(
                    "FrePPLe was unable to plan the sales order line(s)"
                )

            html_response = Quote.generate_html(response_json)
            sale_order.message_post(body=html_response, body_is_html=True)

            # If multiple lines, we need to get the furthest in time
            furthest_end_date = None

            for demand in response_json["demands"]:
                try:
                    end_date_object = datetime.datetime.strptime(
                        demand["pegging"][0]["operationplan"]["end"],
                        "%Y-%m-%dT%H:%M:%S",
                    )
                    if furthest_end_date is None or end_date_object > furthest_end_date:
                        furthest_end_date = end_date_object
                except Exception as e:
                    pass

            # update the demand expected date
            # the date is received in the user time zone
            # it needs to be converted to UTC before writing it to the odoo db
            if furthest_end_date:
                furthest_end_date_user_tz = (furthest_end_date).replace(
                    tzinfo=tz.gettz(self.env.user.tz)
                )
                furthest_end_date_utc = furthest_end_date_user_tz.astimezone(
                    tz.gettz("UTC")
                ).replace(tzinfo=None)

                sale_order.write({"commitment_date": furthest_end_date_utc})

            if len(response_json["demands"]) < len(sale_order.order_line):
                raise exceptions.UserError(
                    "Warning: FrePPLe was unable to plan %sthe sales order line%s"
                    % (("", "") if len(sale_order.order_line) == 1 else ("all ", "s"))
                )
