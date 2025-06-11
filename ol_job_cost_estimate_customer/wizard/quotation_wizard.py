# Import Odoo libs
from odoo import api, fields, models


class QuotationWizard(models.TransientModel):
    _name = "quotation.wizard"
    _description = "Quotation Wizard"

    # COLUMNS #####

    estimate_id = fields.Many2one("sale.estimate.job", string="Estimate", required=True)
    product_ids = fields.Many2many(
        "product.product",
        string="Available Products",
        compute="_compute_product_ids",
        readonly=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain="[('id', 'in', product_ids)]",
    )
    qty = fields.Integer(string="Quantity", default=1)

    # END #########

    # METHODS #####

    @api.depends("estimate_id")
    def _compute_product_ids(self):
        for wizard in self:
            product_variants = self.env["product.product"].search(
                [("product_tmpl_id", "in", wizard.estimate_id.product_tmpl_ids.ids)]
            )
            wizard.product_ids = product_variants

    def create_quotation(self):
        """
        Create a quotation with the selected product and quantity.
        """
        SaleOrder = self.env["sale.order"]
        if self.product_id:
            vals = {
                "partner_id": self.estimate_id.partner_id.id,
                "origin": self.estimate_id.number,
                "analytic_account_id": self.estimate_id.analytic_id.id,
                "payment_term_id": self.estimate_id.payment_term_id.id,
                "pricelist_id": self.estimate_id.pricelist_id.id,
                "opportunity_id": self.estimate_id.opportunity_id.id,
                "estimate_id": self.estimate_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_id.id,
                            "product_uom_qty": self.qty,
                        },
                    )
                ],
            }
            quotation = SaleOrder.create(vals)

            # Set Unit Price on lines according to pricelist.
            quotation.order_line._compute_price_unit()

            self.estimate_id.write({"state": "quotesend"})
            return {
                "type": "ir.actions.act_window",
                "name": "Quotation",
                "res_model": "sale.order",
                "view_mode": "form",
                "res_id": quotation.id,
            }
        else:
            self.estimate_id.estimate_to_quotation()

    # END #########
