# Import Odoo libs
from odoo import fields, models


class BaseSubstateType(models.Model):
    """Inherit base substates to add mrp.eco model"""

    _inherit = "base.substate.type"

    # COLUMNS ##########

    model = fields.Selection(
        selection_add=[("mrp.eco", "Engineering Change Order")],
        ondelete={"mrp.eco": "cascade"},
    )


# END #########
