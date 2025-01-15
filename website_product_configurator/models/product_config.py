from datetime import timedelta

from odoo import api, fields, models


class ProductConfigStepLine(models.Model):
    _inherit = "product.config.step.line"

    website_tmpl_id = fields.Many2one(
        string="Website Template",
        comodel_name="ir.ui.view",
        domain=lambda s: [
            (
                "inherit_id",
                "=",
                s.env.ref("website_product_configurator.config_form_base").id,
            )
        ],
    )

    def get_website_template(self):
        """Return the external id of the qweb template linked to this step"""
        if self.website_tmpl_id:
            xml_id_dict = self.website_tmpl_id.get_external_id()
            view_id = xml_id_dict.get(self.website_tmpl_id.id)
        else:
            view_id = self.env[
                "product.config.session"
            ].get_config_form_website_template()
        return view_id


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    def remove_inactive_config_sessions(self):
        check_date = fields.Datetime.now() - timedelta(days=3)
        sessions_to_remove = self.search(
            [
                ("write_date", "<", check_date),
                ("state", "=", "draft"),
            ]
        )
        if sessions_to_remove:
            sessions_to_remove.unlink()

    @api.model
    def get_config_form_website_template(self):
        ICPSudo = self.env["ir.config_parameter"].sudo()
        default_tmpl_xml_id = "website_product_configurator.config_form_select"
        xml_id = ICPSudo.get_param(
            "product_configurator.default_configuration_step_website_view_id"
        )
        if not xml_id or not xml_id.isdigit():
            return default_tmpl_xml_id
        return self.env["ir.ui.view"].browse(int(xml_id)).xml_id
