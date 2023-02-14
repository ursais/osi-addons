# Copyright (C) 2018 - 2021, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime

import pytz

from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Get average purchase price of the given product
    def calc_prod_avg_purchase_price(self, product, calculate_from_date):

        if not product:
            return

        avg_price = 0
        company_id = self.env.user.company_id.id
        incoming = []

        # Run Query when Date is set.
        if calculate_from_date:

            # Get all incoming moves for this product
            self.env.cr.execute(
                """ SELECT
                        SUM(pol.price_unit * uom.factor * sm.product_qty),
                        SUM(sm.product_qty)
                    FROM stock_move sm
                        LEFT JOIN stock_picking_type sp ON (
                            sm.picking_type_id = sp.id)
                        LEFT JOIN stock_location sl ON (sm.location_id = sl.id)
                        LEFT JOIN purchase_order_line pol ON (
                            sm.purchase_line_id = pol.id)
                        LEFT JOIN uom_uom uom ON (pol.product_uom = uom.id)
                    WHERE sp.code = 'incoming'
                          AND sl.usage = 'supplier'
                          AND sm.product_id = %s
                          AND sm.company_id = %s
                          AND sm.date >= %s
                """,
                (product.id, company_id, calculate_from_date),
            )

            incoming = self.env.cr.fetchall()

            # Get all return moves for this product
            self.env.cr.execute(
                """ SELECT
                        SUM(sm.price_unit * sm.product_qty),
                        SUM(sm.product_qty)
                    FROM stock_move sm
                        LEFT JOIN stock_picking_type sp ON (
                            sm.picking_type_id = sp.id)
                        LEFT JOIN stock_location sl ON (
                            sm.location_dest_id = sl.id)
                    WHERE sp.code = 'outgoing'
                          AND sl.usage = 'supplier'
                          AND sm.product_id = %s
                          AND sm.company_id = %s
                          AND sm.date >= %s
                """,
                (product.id, company_id, calculate_from_date),
            )

            returns = self.env.cr.fetchall()

        else:
            # Get all incoming moves for this product
            self.env.cr.execute(
                """ SELECT
                        SUM(pol.price_unit * uom.factor * sm.product_qty),
                        SUM(sm.product_qty)
                    FROM stock_move sm
                        LEFT JOIN stock_picking_type sp ON (
                            sm.picking_type_id = sp.id)
                        LEFT JOIN stock_location sl ON (
                            sm.location_id = sl.id)
                        LEFT JOIN purchase_order_line pol ON (
                            sm.purchase_line_id = pol.id)
                        LEFT JOIN uom_uom uom ON (pol.product_uom = uom.id)
                    WHERE sp.code = 'incoming'
                          AND sl.usage = 'supplier'
                          AND sm.product_id = %s
                          AND sm.company_id = %s
                """,
                (product.id, company_id),
            )

            incoming = self.env.cr.fetchall()

            # Get all return moves for this product
            self.env.cr.execute(
                """ SELECT
                        SUM(sm.price_unit * sm.product_qty),
                        SUM(sm.product_qty)
                    FROM stock_move sm
                        LEFT JOIN stock_picking_type sp ON (
                            sm.picking_type_id = sp.id)
                        LEFT JOIN stock_location sl ON (
                            sm.location_dest_id = sl.id)
                    WHERE sp.code = 'outgoing'
                          AND sl.usage = 'supplier'
                          AND sm.product_id = %s
                          AND sm.company_id = %s
                """,
                (product.id, company_id),
            )

            returns = self.env.cr.fetchall()

        # Compute average price of the product
        if len(incoming) and incoming[0][0] is not None:
            (incoming_price_qty, incoming_qty) = incoming[0]

            if len(returns) and returns[0][0] is not None:

                (returns_price_qty, returns_qty) = returns[0]

                avg_price = (
                    (incoming_qty - returns_qty)
                    and (incoming_price_qty - returns_price_qty)
                    / (incoming_qty - returns_qty)
                    or 0
                )

            else:
                avg_price = incoming_qty and incoming_price_qty / incoming_qty or 0
        return avg_price

    # Get average purchase price of the given product
    def _compute_avg_price(self):

        for product in self:
            product.avg_price = product.calc_prod_avg_purchase_price(
                product, product.calculate_from_date
            )

    avg_price = fields.Float(
        compute="_compute_avg_price",
        string="Avg Price",
        readonly=True,
        digits=("Product Cost"),
    )
    reset_date = fields.Date(string="Reset Date", copy=False)
    calculate_from_date = fields.Date(string="Calculate From", copy=False)

    def datetime_to_date(self, user_date):
        """Convert datetime values expressed in UTC timezone to
        server-side UTC date while keeping date in user time zone only.
        Preserves the date from datetime, Time has to be ignored here.
        :param str userdate: datetime string in in utc timezone
        :return: UTC date string for server-side use
        """
        context = self._context
        tz_name = False

        if context and context.get("tz"):
            tz_name = context["tz"]

        if tz_name:
            utc = pytz.timezone("UTC")
            context_tz = pytz.timezone(tz_name)
            local_timestamp = user_date.replace(tzinfo=utc)
            local_timestamp = local_timestamp.astimezone(context_tz)
            return local_timestamp.strftime(DEFAULT_SERVER_DATE_FORMAT)

        return user_date.strftime(DEFAULT_SERVER_DATE_FORMAT)

    def _change_standard_price(self, new_price):

        res = super(ProductProduct, self)._change_standard_price(new_price)
        for product in self:

            dt2day = self.datetime_to_date(datetime.today())
            product.write({"reset_date": dt2day})
            product.product_tmpl_id.write({"reset_date": dt2day})

        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # Get average purchase price of the given product
    def _compute_avg_price(self):

        for product_template in self:
            product_template.avg_price = 0
            incoming = []

            if product_template.calculate_from_date:

                for product in product_template.product_variant_ids:

                    query = """
                        SELECT
                            SUM(pol.price_unit * uom.factor * sm.product_qty),
                            SUM(sm.product_qty)
                        FROM stock_move sm
                            LEFT JOIN stock_picking_type sp ON (
                                sm.picking_type_id = sp.id)
                            LEFT JOIN stock_location sl ON (
                                sm.location_id = sl.id)
                            LEFT JOIN purchase_order_line pol ON (
                                sm.purchase_line_id = pol.id)
                            LEFT JOIN uom_uom uom ON (pol.product_uom = uom.id)
                        WHERE sp.code = 'incoming'
                            AND sl.usage = 'supplier'
                            AND sm.product_id = %s
                            AND sm.company_id = %s
                            AND sm.date::date >= '%s'
                    """

                    # Get all incoming moves for this product
                    product.env.cr.execute(
                        query
                        % (
                            product.id,
                            product.env.user.company_id.id,
                            product_template.calculate_from_date,
                        )
                    )

                    incoming = product.env.cr.fetchall()

                    # Get all return moves for this product
                    product.env.cr.execute(
                        """ SELECT
                                SUM(sm.price_unit * sm.product_qty),
                                SUM(sm.product_qty)
                            FROM stock_move sm
                                LEFT JOIN stock_picking_type sp ON (
                                    sm.picking_type_id = sp.id)
                                LEFT JOIN stock_location sl ON (
                                    sm.location_dest_id = sl.id)
                            WHERE sp.code = 'outgoing'
                                  AND sl.usage = 'supplier'
                                  AND sm.product_id = %s
                                  AND sm.company_id = %s
                                  AND sm.date::date >= '%s'
                        """
                        % (
                            product.id,
                            product.env.user.company_id.id,
                            product_template.calculate_from_date,
                        )
                    )

                    returns = product.env.cr.fetchall()

            else:

                for product in product_template.product_variant_ids:

                    query = """
                        SELECT
                            SUM(pol.price_unit * uom.factor * sm.product_qty),
                            SUM(sm.product_qty)
                        FROM stock_move sm
                            LEFT JOIN stock_picking_type sp ON (
                                sm.picking_type_id = sp.id)
                            LEFT JOIN stock_location sl ON (
                                sm.location_id = sl.id)
                            LEFT JOIN purchase_order_line pol ON (
                                sm.purchase_line_id = pol.id)
                            LEFT JOIN uom_uom uom ON (pol.product_uom = uom.id)
                        WHERE sp.code = 'incoming'
                              AND sl.usage = 'supplier'
                              AND sm.product_id = %s
                              AND sm.company_id = %s
                    """
                    # Get all incoming moves for this product
                    product.env.cr.execute(
                        query % (product.id, product.env.user.company_id.id)
                    )

                    incoming = product.env.cr.fetchall()

                    # Get all return moves for this product
                    product.env.cr.execute(
                        """ SELECT
                                SUM(sm.price_unit * sm.product_qty),
                                SUM(sm.product_qty)
                            FROM stock_move sm
                                LEFT JOIN stock_picking_type sp ON (
                                    sm.picking_type_id = sp.id)
                                LEFT JOIN stock_location sl ON (
                                    sm.location_dest_id = sl.id)
                            WHERE sp.code = 'outgoing'
                                  AND sl.usage = 'supplier'
                                  AND sm.product_id = %s
                                  AND sm.company_id = %s
                            """
                        % (product.id, product.env.user.company_id.id)
                    )
                    returns = product.env.cr.fetchall()

            # Compute average price of the product
            if len(incoming) and incoming[0][0] is not None:

                (incoming_price_qty, incoming_qty) = incoming[0]

                if len(returns) and returns[0][0] is not None:

                    (returns_price_qty, returns_qty) = returns[0]

                    # Make sure no division by zero and negative values.
                    if (incoming_qty - returns_qty) > 0:
                        product_template.avg_price = (
                            incoming_price_qty - returns_price_qty
                        ) / (incoming_qty - returns_qty)
                    else:
                        product_template.avg_price = (
                            incoming_price_qty + returns_price_qty
                        ) / (incoming_qty + returns_qty)

                else:
                    product_template.avg_price = incoming_price_qty / incoming_qty

    standard_price = fields.Float(
        compute="_compute_standard_price",
        string="Cost",
        inverse="_inverse_set_standard_price",
        search="_search_standard_price",
        digits=("Product Cost"),
        groups="base.group_user",
        help="Cost used for stock valuation in standard price and as a first"
        " price to set in average/fifo. Also used as a base price for "
        "pricelists. Expressed in the default uom the product.",
    )
    avg_price = fields.Float(
        compute="_compute_avg_price", string="Avg Price", digits=("Product Cost")
    )
    reset_date = fields.Date(string="Reset Date", copy=False)
    calculate_from_date = fields.Date(string="Calculate From", copy=False)

    def _change_standard_price(self, new_price):

        res = super(ProductTemplate, self)._change_standard_price(new_price)

        for product in self.product_variant_ids:
            dt2day = product.datetime_to_date(datetime.today())
            product.write({"reset_date": dt2day})

        return res

    def _inverse_set_standard_price(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.standard_price = template.standard_price
