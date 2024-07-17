# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AttributeAttribute(models.Model):
    _inherit = "attribute.attribute"

    def _get_attribute_set_allowed_model(self):
        res = super()._get_attribute_set_allowed_model()
        if self.model_id.model == "product.product":
            res |= self.env["ir.model"].search([("model", "=", "product.template")])
        return res
