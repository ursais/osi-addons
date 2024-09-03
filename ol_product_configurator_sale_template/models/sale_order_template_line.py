# Import Odoo libs
from odoo import Command, api, fields, models


class SaleOrderTemplateLine(models.Model):
    """
    Add new Fields and methods to Sale Order Template Line
    """

    _inherit = "sale.order.template.line"

    # COLUMNS #####

    custom_value_ids = fields.One2many(
        comodel_name="product.config.session.custom.value",
        inverse_name="cfg_session_id",
        related="config_session_id.custom_value_ids",
        string="Configurator Custom Values",
    )
    config_ok = fields.Boolean(
        related="product_id.config_ok", string="Configurable", readonly=True
    )
    config_session_id = fields.Many2one(
        comodel_name="product.config.session", string="Config Session"
    )
    bom_id = fields.Many2one(
        "mrp.bom",
        string="BoM",
        readonly=True,
    )

    # END #########

    # METHODS ##########

    def reconfigure_product(self):
        """Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""
        wizard_model = "product.configurator.sale.order.temp"

        extra_vals = {
            "order_id": self.sale_order_template_id.id,
            "order_line_id": self.id,
            "product_id": self.product_id.id,
        }
        self = self.with_context(
            default_order_id=self.sale_order_template_id.id,
            default_order_line_id=self.id,
        )
        return self.product_id.product_tmpl_id.create_config_wizard(
            model_name=wizard_model, extra_vals=extra_vals
        )

    @api.depends("product_id")
    def _compute_name(self):
        for line in self:
            name = ""
            custom_values = line.custom_value_ids
            if custom_values:
                name += "\n" + "\n".join(
                    [f"{cv.display_name}: {cv.value}" for cv in custom_values]
                )
            else:
                if not line.product_id:
                    continue
                name = self.product_id.get_product_multiline_description_sale()
            line.name = name

    def _prepare_order_line_values(self):
        values = super()._prepare_order_line_values()
        values.update(
            {
                "config_ok": self.config_ok,
                "config_session_id": self.config_session_id.id,
                "custom_value_ids": [Command.set(self.custom_value_ids.ids)],
                "bom_id": self.bom_id.id,
            }
        )
        return values

    # END ##########
