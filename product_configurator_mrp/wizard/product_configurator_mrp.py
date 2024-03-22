# Copyright (C) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ProductConfiguratorMrp(models.TransientModel):
    _name = "product.configurator.mrp"
    _inherit = "product.configurator"
    _description = "Product Configurator MRP"

    order_id = fields.Many2one(
        comodel_name="mrp.production", string="Manufacturing Order"
    )

    domain_attr_ids = fields.Many2many(
        "product.attribute.value",
        "domain_attrs_mrp_configurator_rel",
        "wiz_id",
        "attribute_id",
        string="Domain",
    )

    domain_attr_2_ids = fields.Many2many(
        "product.attribute.value",
        "domain_attrs_mrp_configurator_2_rel",
        "wiz_id",
        "attribute_id",
        string="Domain 2",
    )

    def get_mrp_production_action(self):
        mrp_action = self.env.ref("mrp.mrp_production_action").read()
        if mrp_action:
            mrp_action = mrp_action[0]
            context = safe_eval(
                mrp_action["context"], self.env.context.copy(), nocopy=True
            )
            context.update(self.env.context)
            mrp_action.update(
                {
                    "view_mode": "form",
                    "context": context,
                    "views": [(False, "form")],
                }
            )
        else:
            mrp_action = {
                "type": "ir.actions.act_window",
                "res_model": "mrp.production",
                "name": "Manufacturing Order",
                "view_mode": "form",
                "context": self.env.context,
                "views": [(False, "form")],
            }
        return mrp_action

    def _get_order_vals(self, product_id):
        """Hook to allow custom line values to be put on the newly
        created or edited lines."""
        product = self.env["product.product"].browse(product_id)
        bom = self.config_session_id.create_get_bom(
            variant=product,
        )
        line_vals = {
            "bom_id": bom.id,
            "product_uom_id": product.uom_id.id,
            "config_session_id": self.config_session_id.id,
        }
        return line_vals

    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""
        res = super().action_config_done()
        if res.get("res_model") == self._name:
            return res
        model_name = "mrp.production"
        line_vals = self._get_order_vals(res["res_id"])
        mrpProduction = self.env[model_name]
        cfg_session = self.config_session_id
        specs = cfg_session.get_onchange_specifications(model=model_name)
        # updates = mrpProduction.onchange(line_vals, ["bom_id"], specs)
        # values = updates.get("value", {})
        # values = cfg_session.get_vals_to_write(values=values, model=model_name)
        # values.update(line_vals)
        if not line_vals.get("bom_id"):
            raise ValidationError(
                _(
                    "There is no BOM associated with selected product. "
                    "Please inform to administrator/manager. [Product: %s]"
                    % (self.env["product.product"].browse(res["res_id"]).display_name)
                )
            )

        if self.order_id:
            self.order_id.write(line_vals)
            mrp_order = self.order_id
        else:
            mrp_order = self.order_id.create(line_vals)
        mrp_action = self.get_mrp_production_action()
        mrp_action.update({"res_id": mrp_order.id})
        return mrp_action
