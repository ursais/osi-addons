# Import Odoo libs
from odoo import _, api, fields, models


class SaleOrder(models.Model):
    """
    Inherit Sale Order to add Credit Limit functionality.

    Adds:
      - Credit hold status per order
      - Uninvoiced balance calculation
      - Override flag for credit hold
    """

    _inherit = "sale.order"

    # COLUMNS #####

    credit_hold = fields.Boolean(
        string="Credit Hold",
        compute="_compute_credit_hold",
        store=True,
    )
    uninvoiced_balance = fields.Monetary(
        string="Uninvoiced Balance",
        compute="_compute_uninvoiced_balance",
        store=True,
    )
    override_credit_limit_hold = fields.Boolean("Override Credit Limit Hold")

    # END #########
    # METHODS #####

    def _get_open_sale_order(self, partner_ids):
        """
        Fetch open Sale Orders for given partners.

        Criteria:
          - Partner matches
          - Not fully invoiced
          - Not cancelled or draft

        Returns a recordset of sale orders.
        """
        so_obj = self.env["sale.order"]
        if not partner_ids:
            return so_obj
        # Normalize partner_ids to a list of IDs
        if hasattr(partner_ids, "ids"):
            p_ids = tuple(partner_ids.ids) or (0,)
        else:
            p_ids = tuple(partner_ids) or (0,)
        query = """
            SELECT id
            FROM sale_order
            WHERE partner_id IN %s
            AND invoice_status != 'invoiced'
            AND state not in ('cancel','draft')
        """
        self.env.cr.execute(query, (p_ids,))
        so_list = [so[0] for so in self.env.cr.fetchall()]
        return so_obj.browse(so_list)

    @api.depends(
        "partner_id.partner_rollup_id",
        "partner_id.remaining_credit",
        "override_credit_limit_hold",
    )
    def _compute_credit_hold(self):
        """
        Simple credit hold computation:
        - Find the top roll up partner from SO partner_id
        - If remaining_credit <= 0, set credit_hold = True
        """
        if not self:
            return

        for order in self:
            partner = order.partner_id
            
            # Find the top roll up partner by traversing up the partner_rollup_id chain
            # Go up the chain until we find the top most rollup partner
            current_partner = partner
            while current_partner.partner_rollup_id:
                current_partner = current_partner.partner_rollup_id
            
            # Check if the top roll up partner's remaining credit is less than or equal to 0
            if current_partner.remaining_credit <= 0:
                order.credit_hold = True
            else:
                order.credit_hold = False

    @api.depends(
        "amount_total",
        "invoice_ids",
        "invoice_ids.amount_total"
    )
    def _compute_uninvoiced_balance(self):
        """
        Compute the uninvoiced balance:
        - If not fully invoiced, equal to order total.
        - Otherwise zero.
        """
        for order in self:
            invoice_ids = order.invoice_ids
            out_invoice_ids = invoice_ids.filtered(lambda l: l.state not in ('draft','cancel') and l.move_type == 'out_invoice')
            refund_ids = invoice_ids.filtered(lambda l: l.state not in ('draft','cancel') and l.move_type == 'out_refund')
            total = sum(out_invoice_ids.mapped('amount_total'))
            refunds = sum(refund_ids.mapped('amount_total'))
            invoice_amount = order.amount_total + refunds - total
            order.uninvoiced_balance = invoice_amount or 0.0


    @api.depends(
        "company_id",
        "partner_id",
        "amount_total",
    )
    def _compute_partner_credit_warning(self):
        """
        Placeholder: Compute partner credit warning message for SO.
        Currently sets an empty string (extend as needed).
        """
        for order in self:
            order.partner_credit_warning = ""
