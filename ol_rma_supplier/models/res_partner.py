from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    rma_supplier_order_count = fields.Integer(
        compute="_compute_rma_supplier_order_count",
        string="Supplier RMA Count",
    )
    rma_supplier_order_ids = fields.One2many(
        "rma.supplier.order", "partner_id", string="Supplier RMA's"
    )

    def _compute_rma_supplier_order_count(self):
        """Standard count method to count related RMA's for smart button."""
        for partner in self:
            partner.rma_supplier_order_count = len(partner.rma_supplier_order_ids)

    def action_view_rma_supplier_orders(self):
        """Smart button action to open the supplier RMA or list of RMA's if more than one."""
        rma_order_ids = self.rma_supplier_order_ids
        action = self.env.ref("ol_rma_supplier.action_rma_supplier").read()[0]

        if len(rma_order_ids) == 1:
            # Open the single RMA in form view
            action["views"] = [
                (self.env.ref("ol_rma_supplier.view_rma_supplier_form").id, "form"),
            ]
            action["res_id"] = rma_order_ids.id
        else:
            # Open the list view with a fallback to form view for individual records
            action["views"] = [
                (self.env.ref("ol_rma_supplier.view_rma_supplier_tree").id, "tree"),
                (self.env.ref("ol_rma_supplier.view_rma_supplier_form").id, "form"),
            ]
            action["domain"] = [("id", "in", rma_order_ids.ids)]
            action["context"] = dict(self.env.context)  # Preserve context if needed

        return action
