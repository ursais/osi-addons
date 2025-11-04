# Import Odoo libs
from odoo import fields, models


class Warehouse(models.Model):
    """Inherit Warehouse to add repair operation."""

    _inherit = "stock.warehouse"

    # COLUMNS ###

    rma_repair_in_type_id = fields.Many2one(
        comodel_name="stock.picking.type",
        string="RMA Repairs Incoming Picking Type",
        check_company=True,
        copy=False,
        domain="[('code', '=', 'incoming')]",
        help="Picking type used for parts returned from customers for repair.",
    )

    # END #######
