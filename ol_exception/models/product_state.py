# Import Odoo libs
from odoo import fields, models


class ProductState(models.Model):
    """
    Add a field to product state to allow users to configure states to either trigger
    an exception check or not if a product changes states.
    """

    _inherit = "product.state"

    # COLUMNS #####

    trigger_exception = fields.Boolean(
        string="Trigger Exception",
        help="""When enabled, moving products to and from this state will
        trigger exception checks on Sale Orders, Pickings and Manufacturing Orders.""",
    )

    # END #########
