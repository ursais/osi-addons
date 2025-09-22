# Import Odoo libs
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # COLUMNS #####

    payment_preference = fields.Many2one(
        comodel_name="res.paypref",
        string="Payment Preference",
        company_dependent=True,
    )
    net_terms_allowed = fields.Boolean(
        string="Net Terms Allowed",
        compute="_compute_net_terms_allowed",
        store=True,
    )
    net_terms_active = fields.Boolean(
        string="Front End Net Terms Active",
    )
    sale_payment_method_id = fields.Many2one(
        comodel_name="payment.method",
        string="Customer Preferred Payment Method",
    )
    debit_limit = fields.Float(
        string="Vendor Credit Limit",
        company_dependent=True,
    )
    no_followup_contacts = fields.Boolean(
        string="No Followup Contacts",
        compute="_compute_followup_contacts",
        help="Helper field used to flag followups that have no contacts to send to.",
    )
    followup_contact_ids = fields.One2many(
        comodel_name="res.partner",
        compute="_compute_followup_contacts",
        help="Helper field to be used by followup communications.",
    )

    # END #########
    # Method #########

    def _compute_followup_contacts(self):
        for partner in self:
            followup_partners = partner.commercial_partner_id.child_ids.filtered(
                "followup"
            )
            if followup_partners:
                partner.no_followup_contacts = False
                partner.followup_contact_ids = [
                    fields.Command.set(followup_partners.ids)
                ]
            else:
                partner.no_followup_contacts = True
                partner.followup_contact_ids = [fields.Command.clear()]

    # Override method to check followup bool
    def _get_all_followup_contacts(self):
        """Returns every contact of the commercial entity where followup is True.
        If no followup contacts are found, use the billing address
        and default to contact if there isn't any for invoice.
        """
        self.ensure_one()
        commercial_entity = self.commercial_partner_id

        # Find all child contacts marked for followup
        followup_contacts = self.search(
            [("id", "child_of", commercial_entity.id), ("followup", "=", True)]
        )
        if not followup_contacts:
            # Fallback: use billing address (invoice)
            followup_contacts = self.env["res.partner"].browse(
                commercial_entity.address_get(["invoice"])["invoice"]
            )

        return followup_contacts

    def _execute_followup_partner(self, options=None):
        """Override: skip or block followups if no followup contacts exist.

        - If triggered automatically (cron), and partner.no_followup_contacts = True → skip.
        - If triggered manually, and partner.no_followup_contacts = True → raise UserError.
        """
        self.ensure_one()

        # Default options
        if options is None:
            options = {}

        # If no followup contacts are configured
        if self.no_followup_contacts:
            if options.get("manual_followup", False):
                # Manual execution → block and show error
                raise UserError(
                    _(
                        "The Partner’s company does not have any contacts set to receive "
                        "Followup emails. Please enable followups on any contact for the "
                        "company and try again."
                    )
                )
            else:
                # Automatic (cron) execution → skip silently
                return False

        # Normal logic continues here
        if options.get("manual_followup", self.followup_status == "in_need_of_action"):
            followup_line = self.followup_line_id or self._get_first_followup_level()

            if followup_line.create_activity:
                self.activity_schedule(
                    activity_type_id=followup_line.activity_type_id
                    and followup_line.activity_type_id.id
                    or self._default_activity_type().id,
                    note=followup_line.activity_note,
                    summary=followup_line.activity_summary,
                    user_id=(self._get_followup_responsible()).id,
                )

            self._update_next_followup_action_date(followup_line)

            if not options.get("join_invoices", followup_line.join_invoices):
                options["attachment_ids"] = []

            self._send_followup(options={"followup_line": followup_line, **options})
            return True

        return False

    @api.depends("commercial_partner_id.property_payment_term_id")
    def _compute_net_terms_allowed(self):
        """
        Determines whether the partner is allowed to use net terms.
        This is only Used on Frontend eCommerce.
        """
        for partner in self:
            partner.net_terms_allowed = bool(
                partner.commercial_partner_id.property_payment_term_id
            )

    def _commercial_fields(self):
        fields = super()._commercial_fields()
        fields.append("sale_payment_method_id")
        return fields

    # END #########
