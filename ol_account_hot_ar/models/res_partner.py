# Import Odoo Libs
from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####

    hot_ar = fields.Boolean(
        string="Hot AR",
        compute="_compute_check_hot_ar",
        store=True,
        recursive=True,
        help="""Customer has one or more invoices that are
         overdue and past the grace period.""",
    )
    override_hot_ar = fields.Boolean(
        string="Override Hot AR",
        help="""ustomer has one or more invoices that are overdue and
         past the grace period.""",
        groups="account.group_account_invoice",
    )

    # END #########
    # METHODS #####

    @api.depends(
        "invoice_ids.hot_ar",
        "invoice_ids.payment_state",
        "invoice_ids.override_hot_ar",
        "override_hot_ar",
        "child_ids.hot_ar",
    )
    def _compute_check_hot_ar(self):
        for partner in self:
            # Skip if partner isn't created yet.
            if not partner.id or isinstance(partner.id, models.NewId):
                continue

            if partner.override_hot_ar:
                partner.hot_ar = False
            else:
                # Modified compute logic to update hot_ar field via PSQL query instead of ORM to reduce the execution time.
                invoices = self.env["account.move"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("payment_state", "not in", ("in_payment", "paid", "reversed")),
                        (
                            "move_type",
                            "in",
                            ("out_invoice", "in_invoice", "out_refund", "in_refund"),
                        ),
                        ("hot_ar", "=", True),
                        ("override_hot_ar", "=", False),
                        ("state", "=", "posted"),
                        ("company_id.hot_ar_grace_period", ">", 0),
                    ]
                )
                # Write to partner (with sudo since this is done systematically)
                # Using write to trigger
                partner.sudo().write({"hot_ar": bool(invoices)})
            #            Now update commercial partner based on children
            if (
                partner.commercial_partner_id
                and partner != partner.commercial_partner_id
            ):
                commercial_partner = partner.commercial_partner_id
                # Modified compute logic to update hot_ar field via PSQL query instead of ORM to reduce the execution time.
                # This will ensure the commercial partner is "hot" if any child is
                if not self._context.get("commercial_partner"):
                   commercial_partner.sudo().write(
                        {
                            "hot_ar": any(
                                child.with_context(commercial_partner=True).hot_ar
                                and not child.override_hot_ar
                                for child in commercial_partner.child_ids
                            )
                        }
                    )

    # END #########
