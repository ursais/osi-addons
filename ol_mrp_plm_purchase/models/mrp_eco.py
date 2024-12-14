# Import Odoo libs
from odoo import api, fields, models


class MRPEco(models.Model):
    """
    Inherit MRP Eco for Method Overriding.
    """

    _inherit = "mrp.eco"

    # COLUMNS ##########

    purchase_ids = fields.One2many(
        "purchase.order",
        "eco_id",
        string="Purchase Orders",
    )
    purchase_count = fields.Integer(
        string="Purchase Count",
        compute="_compute_purchase_count",
    )
    purchase_expected_date = fields.Datetime(
        string="PO Expected Date",
        compute="_compute_purchase_expected_date",
        store=True,
    )

    # END #########
    # METHODS ##########

    @api.depends("purchase_ids")
    def _compute_purchase_count(self):
        """Standard count method to count related PO's for smart button."""
        for eco in self:
            eco.purchase_count = len(eco.purchase_ids)

    @api.depends(
        "purchase_ids.date_planned",
        "purchase_ids.state",
    )
    def _compute_purchase_expected_date(self):
        for eco in self:
            # Filter purchase orders with status 'purchase'
            valid_purchase_orders = eco.purchase_ids.filtered(
                lambda po: po.state == "purchase"
            )
            # Extract the planned dates from valid purchase orders
            planned_dates = valid_purchase_orders.mapped("date_planned")
            # Check if there are any dates, and assign the earliest one if available
            eco.purchase_expected_date = min(planned_dates) if planned_dates else False

    def action_view_purchase(self):
        """Smart button action to open the PO or list of PO's if more than one."""
        purchases = self.purchase_ids
        action = self.env.ref("purchase.purchase_rfq").read()[0]

        if len(purchases) == 1:
            # Open the single PO in form view
            action["views"] = [
                (self.env.ref("purchase.purchase_order_form").id, "form"),
            ]
            action["res_id"] = purchases.id
        else:
            # Open the list view with a fallback to form view for individual records
            action["views"] = [
                (self.env.ref("purchase.purchase_order_kpis_tree").id, "tree"),
                (self.env.ref("purchase.purchase_order_form").id, "form"),
            ]
            action["domain"] = [("id", "in", purchases.ids)]
            action["context"] = dict(self.env.context)  # Preserve context if needed

        return action

    def open_purchase_creation_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.creation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_product_id": self.product_tmpl_id.product_variant_id.id,
            },
        }

    def action_create_purchase(self, partner, product):
        """Action called via button to create a new prototype product."""
        # Create RFQ
        new_purchase = self.env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "eco_id": self.id,
            }
        )
        # Create purchase order line
        self.env["purchase.order.line"].create(
            {
                "order_id": new_purchase.id,
                "product_id": product.id,
                "product_qty": 1,
                "price_unit": product.lst_price,
            }
        )
        # Show the created RFQ
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": new_purchase.id,
            "target": "current",
        }

    # END #########
