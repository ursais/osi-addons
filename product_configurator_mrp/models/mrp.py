# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    config_ok = fields.Boolean(
        related="product_id.config_ok",
        store=True,
        string="Configurable",
        readonly=True,
    )
    config_session_id = fields.Many2one(
        comodel_name="product.config.session", string="Config Session"
    )
    custom_value_ids = fields.One2many(
        comodel_name="product.config.session.custom.value",
        inverse_name="cfg_session_id",
        related="config_session_id.custom_value_ids",
        string="Custom Values",
    )

    @api.model
    def action_config_start(self):
        """Return action to start configuration wizard"""
        configurator_obj = self.env["product.configurator.mrp"]
        ctx = dict(
            self.env.context,
            wizard_id=None,
            wizard_model="product.configurator.mrp",
            allow_preset_selection=True,
        )
        return configurator_obj.with_context(**ctx).get_wizard_action()

    def reconfigure_product(self):
        """Creates and launches a product configurator wizard with a linked
        template and variant in order to re-configure a existing product. It is
        esetially a shortcut to pre-fill configuration data of a variant"""
        wizard_model = "product.configurator.mrp"
        extra_vals = {"order_id": self.id, "product_id": self.product_id.id}
        self = self.with_context(default_order_id=self.id)
        return self.product_id.product_tmpl_id.create_config_wizard(
            model_name=wizard_model, extra_vals=extra_vals
        )


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    config_ok = fields.Boolean(
        related="product_tmpl_id.config_ok",
        store=True,
        string="Configurable",
        readonly=True,
    )
    scaffolding_bom = fields.Boolean(
        string="Scaffolding BoM",
        help="When checked, this BoM will serve as the main BoM used by the configurator to "
        "create the product variant BoM’s. Only one BoM per product can be set as a Scaffolding BoM. "
        "If no scaffolding BoM exists, the configurator will then look for a BoM that doesn’t have a "
        "Product Variant to use.",
    )
    existing_scaffolding_bom = fields.Boolean(
        string="Existing Scaffolding BoM",
        compute="_compute_existing_scaffolding_bom",
        store=True,
    )

    @api.model
    def default_get(self, val_list):
        result = super().default_get(val_list)
        if result.get("product_tmpl_id"):
            product_tmpl_id = self.env["product.template"].browse(
                result.get("product_tmpl_id")
            )
            result["company_id"] = (
                product_tmpl_id and product_tmpl_id.company_id.id or False
            )
        return result

    @api.constrains("product_tmpl_id", "scaffolding_bom")
    def _check_product_tmpl_scaffolding_bom(self):
        """Constraint ensures only one scaffolding BoM exists per product template"""
        for rec in self:
            if (
                self.search_count(
                    [
                        ("scaffolding_bom", "=", True),
                        ("product_tmpl_id", "=", rec.product_tmpl_id.id),
                    ]
                )
                > 1
            ):
                raise exceptions.ValidationError(
                    _(
                        "You can only have one unarchived Scaffolding BOM for a configurable product."
                    )
                )

    @api.depends("scaffolding_bom", "active", "product_tmpl_id")
    def _compute_existing_scaffolding_bom(self):
        for rec in self:
            if (
                self.search_count(
                    [
                        ("scaffolding_bom", "=", True),
                        ("active", "=", True),
                        ("product_tmpl_id", "=", rec.product_tmpl_id.id),
                        ("product_id", "=", False),
                    ]
                )
                >= 1
            ):
                rec.existing_scaffolding_bom = True
            else:
                rec.existing_scaffolding_bom = False

    @api.onchange("product_id")
    def onchange_scaffolding_bom_product_id(self):
        """onchange method to automatically set 'scaffolding_bom'
        based on 'product_id'."""
        if self.product_id:
            self.scaffolding_bom = False
        else:
            self.scaffolding_bom = True


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    config_set_id = fields.Many2one(
        comodel_name="mrp.bom.line.configuration.set",
        string="Configuration Set",
    )


class MrpBomLineConfigurationSet(models.Model):
    _name = "mrp.bom.line.configuration.set"
    _description = "Mrp Bom Line Configuration Set"

    name = fields.Char(string="Configuration", required=True)
    configuration_ids = fields.One2many(
        comodel_name="mrp.bom.line.configuration",
        inverse_name="config_set_id",
        string="Configurations",
    )
    bom_line_ids = fields.One2many(
        comodel_name="mrp.bom.line",
        inverse_name="config_set_id",
        string="BoM Lines",
        readonly=True,
    )


class MrpBomLineConfiguration(models.Model):
    _name = "mrp.bom.line.configuration"
    _description = "Mrp Bom Line Configuration"

    config_set_id = fields.Many2one(
        comodel_name="mrp.bom.line.configuration.set",
        ondelete="cascade",
        required=True,
    )
    value_ids = fields.Many2many(
        string="Attribute Values",
        comodel_name="product.attribute.value",
        required=True,
    )
