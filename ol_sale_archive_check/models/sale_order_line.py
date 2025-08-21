# Import Odoo libs
from odoo import api, fields, models
from odoo.addons.ol_base.tools import get_product_description


class SaleOrderLine(models.Model):
    """
    Add new fields to Sale Order Line
    """

    _inherit = "sale.order.line"

    # COLUMNS #####

    is_archived_or_bom_archived = fields.Boolean(
        compute="_compute_is_archived_or_bom_archived",
        help="Helper field to determine if line has archived BoM or Product.",
    )

    # END #########
    # METHODS #####

    @api.depends(
        "product_id.active",
        "bom_id.active",
    )
    def _compute_is_archived_or_bom_archived(self):
        for line in self:
            line.is_archived_or_bom_archived = (
                line.product_id and not line.product_id.active
            ) or (line.bom_id and not line.bom_id.active)

    # END #########
