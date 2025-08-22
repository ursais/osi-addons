# Import Odoo libs
from odoo import fields, models


class MrpEcoType(models.Model):
    """
    Add field to PLM ECO Type to enable staging configurable product changes.
    """

    _inherit = "mrp.eco.type"

    # COLUMNS #####

    enable_staged_configuration = fields.Boolean(
        string="Enable Staged Attributes/Variants",
        default=True,
        help="If enabled, ECOs of this type will have a tab to stage attribute "
        "and value changes before Apply Changes.",
    )

    # END #########
