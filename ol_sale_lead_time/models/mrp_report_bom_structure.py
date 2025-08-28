from odoo import api, models


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    @api.model
    def get_html(self, bom_id=False, searchQty=1, searchVariant=False):
        """Overridden to update the Default QTY base on SOL or BOL line Qty"""
        if self._context.get("default_searchQty"):
            searchQty = self._context.get("default_searchQty")
        return super().get_html(
            bom_id=bom_id, searchQty=searchQty, searchVariant=searchVariant
        )
