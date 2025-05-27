# Import Python libs

# Import Odoo libs
from odoo import models, fields, api


class SystemStockStatusResultWizard(models.TransientModel):
    _name = 'system.stock.status.result.wizard'
    _description = 'System Stock Status Wizard'

    # COLUMNS #####
    results = fields.Html(
        string='Results',
        sanitize_style=True,
        help="The details of how the System Stock Status was calculated",
    )
    # END #########

    @api.model
    def default_get(self, fields):
        """
        Pre-load fields in the wizard with existing data
        """

        res = super().default_get(fields)

        # Update the wizard from the context data
        res.update(
            {
                "results": self.env.context.get("system_stock_status_results", "")
            }
        )
        return res