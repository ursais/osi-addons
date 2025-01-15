from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    website_tmpl_id = fields.Many2one(
        comodel_name="ir.ui.view",
        string="Website Template",
        domain=lambda s: [
            (
                "inherit_id",
                "=",
                s.env.ref("website_product_configurator.config_form_base").id,
            )
        ],
        config_parameter="product_configurator.default_configuration_step_website_view_id",
    )
