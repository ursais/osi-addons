from odoo import fields, models


class BaseSubstateType(models.Model):
    _inherit = "base.substate.type"

    model = fields.Selection(
        selection_add=[("mrp.eco", "Engineering Change Order")],
        ondelete={"mrp.eco": "cascade"},
    )
