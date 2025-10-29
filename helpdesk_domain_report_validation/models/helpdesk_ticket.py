# Copyright (C) 2025 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models


class HelpdeskTicket(models.Model):
    """Extend helpdesk ticket to support domain report validation."""

    _inherit = "helpdesk.ticket"

    domain_report_id = fields.Many2one(
        "helpdesk.domain.report",
        string="Domain Report",
        index=True,
        help="Associated domain report if this ticket was created from a domain report",
    )
    is_domain_report = fields.Boolean(
        string="Is Domain Report",
        compute="_compute_is_domain_report",
        store=True,
        help="Indicates if this ticket is related to a domain report",
    )
    domain_validation_status = fields.Selection(
        related="domain_report_id.validation_status",
        string="Report Validation Status",
        readonly=True,
        store=True,
    )

    @api.depends("domain_report_id")
    def _compute_is_domain_report(self):
        """Compute whether this ticket is related to a domain report."""
        for ticket in self:
            ticket.is_domain_report = bool(ticket.domain_report_id)

    @api.model
    def create(self, vals):
        """
        Override create to validate domain reports and prevent creation of
        tickets from false positives or whitelisted reports.
        """
        # Check if this ticket is being created with domain report information
        if vals.get("domain_report_id"):
            domain_report = self.env["helpdesk.domain.report"].browse(
                vals["domain_report_id"]
            )
            if domain_report.validation_status in ["false_positive", "whitelisted"]:
                # Log a warning but allow creation if forced
                if not self.env.context.get("force_create_from_false_positive"):
                    # Add a note to the description about the validation status
                    description = vals.get("description", "")
                    warning_msg = _(
                        "\n\nWARNING: This ticket is related to a domain report "
                        "marked as '%s'. Please review before proceeding."
                    ) % dict(
                        domain_report._fields["validation_status"].selection
                    ).get(
                        domain_report.validation_status
                    )
                    vals["description"] = description + warning_msg

        return super().create(vals)

    def action_view_domain_report(self):
        """Open the related domain report."""
        self.ensure_one()
        if not self.domain_report_id:
            return False

        return {
            "name": _("Domain Report"),
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.domain.report",
            "views": [[False, "form"]],
            "res_id": self.domain_report_id.id,
        }

    def action_mark_report_false_positive(self):
        """Mark the related domain report as a false positive."""
        self.ensure_one()
        if self.domain_report_id:
            self.domain_report_id.action_mark_false_positive()
        return True
