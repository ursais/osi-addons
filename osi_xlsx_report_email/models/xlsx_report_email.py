from odoo import api, fields, models
import json
import logging
from datetime import date
from uuid import uuid4
import requests
import os

_logger = logging.getLogger(__name__)


class XLSXReportEmail(models.Model):
    _name = 'xlsx.report.email'

    model_id = fields.Many2one('ir.model')
    email = fields.Char(string='Email To send to')
    report_fields = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="xlsx_report_email_ir_model_fields_report_fields_rel",
        column1="xlsx_report_email_report_field_id",
        column2="report_field_id",
        string='Required Fields'
    )
    groupby_fields = fields.Many2many(
        comodel_name="ir.model.fields",
        relation="xlsx_report_email_ir_model_fields_domain_fields_rel",
        column1="xlsx_report_email_domain_field_id",
        column2="domain_field_id",
        string='Group By Fields',
        domain="[('model_id', '=', model_id)]"
    )
    domain_expr = fields.Text(string="Domain")

    report_name = fields.Char()
    new_field_ids = fields.Many2many()

    @api.onchange('model_id')
    def _onchange_model_set_domain(self):
        return {
            'domain':
                {
                    'report_fields': [('model_id', '=', self.model_id.id)],
                    'domain_fields': [('model_id', '=', self.model_id.id)]

                }
        }

    def _get_db_user_info(self):
        password = os.environ.get("ODOO_ADMIN_USER_PASSWORD") or 'admin'
        db = self.env.cr.dbname
        admin_user_login = self.env.ref("base.user_admin").login or 'admin'
        return admin_user_login, db, password

    def _build_payload(self, params=None):
        """
        Helper to properly build jsonrpc payload
        """
        vals = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": str(uuid4()),
            "params": params if params else {},
        }
        return vals

    def _get_host_infor(self):
        HOST = str(
            self.env["ir.config_parameter"]
            .search([("key", "=", "web.base.url")], limit=1)
            .value
        )
        https = HOST.find("https")
        http = HOST.find("http")
        if https == -1 and http != -1:
            HOST = HOST.replace("http", "https")
        return HOST

    def _get_request_response(self, session, host, endpoint, payload, headers=None, cookies=None):
        if not endpoint:
            return None
        else:
            url = "{}{}".format(host, endpoint)
            response = session.post(url, json=payload, headers=headers, cookies=cookies)
            return response

    def _get_payload_fields_data(self, report_fields):
        # fields_list = report_fields.mapped('name')
        data_list = []
        for field in report_fields:
            data_dict = {}

            data_dict.update({
                "name": field.name,
                "label": field.field_description,
                "store": field.store,
                "type": field.ttype,
            })
            data_list.append(data_dict)
        return data_list

    def _get_groupby_fields(self, groupby_fields):
        res = []
        for f in groupby_fields:
            res.append(f.name)
        return res

    def _evaluate_domain_expr(self, domain_expr):
        dom = eval(domain_expr) if domain_expr else []
        return dom

    def _create_export_payload_data(self):
        data = {
            "model": self.model_id.model,
            "fields": self._get_payload_fields_data(self.report_fields),
            "ids": False,
            "import_compat": False,
            "groupby": self._get_groupby_fields(self.groupby_fields),
            "domain": self._evaluate_domain_expr(self.domain_expr),
        }
        payload = {

            "data": data,
            "token": "dummy-because-api-expects-one",
            "csrf_token": "",
        }
        return payload


    def send_report_daily_email(self):
        recs = self.env['xlsx.report.email'].search([])
        session = requests.Session()
        HOST = self._get_host_infor()
        for rec in recs:
            login, db, password = rec._get_db_user_info()
            auth_dict = {'login': login, 'db': db, 'password': password}
            payload = self._build_payload(auth_dict)
            auth_endpoint = "/web/session/authenticate"
            auth_headers = {"Content-Type": "application/json"}

            auth_response = self._get_request_response(session, HOST, auth_endpoint, payload=json.loads(json.dumps(payload)),
                                                       headers=auth_headers)
            auth_cookies = auth_response.cookies
            # print(" AUTH RESPONSE:   ", auth_response.json())
            export_endpoint = "/web/export/custom/xlsx"
            export_headers = {"Content-Type": "application/json"}
            export_report_data = rec._create_export_payload_data()
            payload = self._build_payload(export_report_data)
            export_response = self._get_request_response(session, HOST, export_endpoint, payload=payload,
                                                         headers=export_headers, cookies=auth_cookies)
            response_data = export_response.json()
            attachment_rec = None
            try:
                b_data_content = response_data.get("result").get("output").get("data")
                attachment_rec = rec.create_attachment_for_email(b_data_content)
            except Exception as e:
                _logger.info(
                    "Failed to get attachment record for sending out Inventory Valuation: %s",
                    str(e),
                )

            if attachment_rec:
                email_values = rec.get_email_values()
                rec.send_email_with_attachment(attachment_rec, email_values)



    def create_attachment_for_email(self, content):
        today = str(date.today())
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "datas": content,
                    "name": self.report_name  + today + ".xlsx",
                    "type": "binary",
                    "mimetype": "application/vnd.openxmlformats"
                                "-officedocument.spreadsheetml.sheet",
                    "res_model": self.model_id.model,
                }
            )
        )
        return attachment

    def get_email_values(self):
        email_values = {}
        email_values["email_from"] = self.env.company.email
        email_values["email_to"] = self.email
        return email_values

    def send_email_with_attachment(self, attachment, email_data):
        try:
            email_to = email_data.get("email_to", False)
            email_from = email_data.get("email_from", False)
            email_template_id = self.env.ref("osi_xlsx_report_email.email_template").id
            email_template = self.env["mail.template"].browse(email_template_id)

            email_template.write({"attachment_ids": [(6, 0, [attachment.id])]})
            email_values = {"email_to": email_to, "email_from": email_from}

            email_template.sudo().send_mail(
                self.id, email_values=email_values, force_send=True
            )
            email_template.attachment_ids = [(3, attachment.id, 0)]
            return True
        except Exception as e:
            _logger.info(
                "Sending Email Failed for {} : {}".format(self.report_name, str(e))
            )
        return False
