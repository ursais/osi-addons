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
                self.env.cr.execute(
                    """
                    UPDATE res_partner p
                    SET hot_ar = EXISTS (
                        SELECT 1
                        FROM account_move am
                        JOIN res_company rc ON rc.id = am.company_id
                        WHERE am.partner_id = p.id
                        AND am.payment_state NOT IN ('in_payment', 'paid', 'reversed')
                        AND am.move_type IN ('out_invoice', 'in_invoice', 'out_refund', 'in_refund')
                        AND am.hot_ar = TRUE
                        AND am.override_hot_ar is null
                        AND am.state = 'posted'
                        AND rc.hot_ar_grace_period > 0
                    )
                    WHERE p.id = %s
                """,
                    [partner.id],
                )
            #            Now update commercial partner based on children
            if (
                partner.commercial_partner_id
                and partner != partner.commercial_partner_id
            ):
                commercial_partner = partner.commercial_partner_id
                # Modified compute logic to update hot_ar field via PSQL query instead of ORM to reduce the execution time.
                # This will ensure the commercial partner is "hot" if any child is
                if not self._context.get("commercial_partner"):
                    commercial_partner_id = commercial_partner.id
                    self.env.cr.execute(
                        """
                        UPDATE res_partner cp
                        SET hot_ar = EXISTS (
                            SELECT 1 FROM res_partner child
                            WHERE child.parent_id = cp.id
                            AND child.hot_ar = TRUE
                            AND child.override_hot_ar is null
                        )
                        WHERE cp.id = %s
                    """,
                        [commercial_partner_id],
                    )

    # END #########
