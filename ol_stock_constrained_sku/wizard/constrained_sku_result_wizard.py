# Import Python libs
import logging

_logger = logging.getLogger(__name__)

# Import Odoo libs
from odoo import api, fields, models


class ConstrainedSkuResultWizard(models.TransientModel):
    _name = "constrained.sku.result.wizard"
    _description = "Constrained SKU Result Wizard"

    # COLUMNS #####

    component_ids = fields.Many2many(
        string="SKUs",
        comodel_name="product.product",
        relation="constrained_sku_result_wizard_products_rel",
        column1="wizard_id",
        column2="product_id",
    )
    processed_line_ids = fields.One2many(
        string="Processed Lines",
        comodel_name="constrained.sku.result.wizard.line",
        compute="_compute_line_ids",
        inverse_name="wizard_id",
        domain="[('rolled_up_and_hidden', '=', 'processed')]",
    )
    skipped_line_ids = fields.One2many(
        string="Skipped Lines",
        comodel_name="constrained.sku.result.wizard.line",
        compute="_compute_line_ids",
        inverse_name="wizard_id",
        domain="[('rolled_up_and_hidden', '=', 'skipped')]",
    )
    allocate = fields.Boolean(string="Allocate")

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
                "processed_line_ids": [
                    (0, 0, v) for v in self.env.context.get("processed_lines", [])
                ],
                "skipped_line_ids": [
                    (0, 0, v) for v in self.env.context.get("skipped_lines", [])
                ],
                "allocate": self.env.context.get("allocate", False),
            }
        )
        return res


class ConstrainedSkuResultWizardLine(models.TransientModel):
    _name = "constrained.sku.result.wizard.line"
    _description = "Constrained SKU Result Wizard Line"

    wizard_id = fields.Many2one(comodel_name="constrained.sku.result.wizard")
    sale_order_id = fields.Many2one(
        string="Sale Order",
        comodel_name="sale.order",
        domain="[('state', 'not in', ['done', 'draft', 'cancel'])]",
    )
    picking_id = fields.Many2one(
        string="Transfer",
        comodel_name="stock.picking",
    )
    product_id = fields.Many2one(
        string="Component",
        comodel_name="product.product",
    )
    change_indicator = fields.Char(
        string="Stock change status",
    )
    type = fields.Selection(
        [("processed", "Processed"), ("skipped", "Skipped")],
        string="Type",
        default="search",
        help="Type of the result line",
    )
    skip_reason = fields.Char(string="Skip Reason")

    # END #########
