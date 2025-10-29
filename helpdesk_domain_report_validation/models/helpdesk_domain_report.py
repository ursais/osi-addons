# Copyright (C) 2025 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class HelpdeskDomainReport(models.Model):
    """Model to track and validate domain-based reports from email security services."""

    _name = "helpdesk.domain.report"
    _description = "Helpdesk Domain Report"
    _order = "create_date desc"
    _rec_name = "domain"

    domain = fields.Char(
        string="Domain",
        required=True,
        index=True,
        help="The domain that is being reported (e.g., opensourceintegrators.com)",
    )
    submitter = fields.Char(
        string="Submitter",
        required=True,
        index=True,
        help="The entity submitting the report (e.g., mimecast.org)",
    )
    report_id = fields.Char(
        string="Report ID",
        index=True,
        help="Unique identifier for the report",
    )
    validation_status = fields.Selection(
        [
            ("pending", "Pending Validation"),
            ("valid", "Valid Report"),
            ("false_positive", "False Positive"),
            ("whitelisted", "Whitelisted"),
        ],
        string="Validation Status",
        default="pending",
        required=True,
        index=True,
        help="Status of the domain report validation",
    )
    notes = fields.Text(
        string="Notes",
        help="Additional notes about this domain report",
    )
    ticket_ids = fields.One2many(
        "helpdesk.ticket",
        "domain_report_id",
        string="Related Tickets",
        help="Tickets created from this domain report",
    )
    ticket_count = fields.Integer(
        string="Ticket Count",
        compute="_compute_ticket_count",
        store=True,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to False to archive the report",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        (
            "unique_report_id",
            "UNIQUE(report_id)",
            "A domain report with this Report ID already exists!",
        ),
    ]

    @api.depends("ticket_ids")
    def _compute_ticket_count(self):
        """Compute the number of tickets related to this domain report."""
        for record in self:
            record.ticket_count = len(record.ticket_ids)

    @api.constrains("domain")
    def _check_domain_format(self):
        """Validate that the domain format is reasonable."""
        for record in self:
            if record.domain and " " in record.domain:
                raise ValidationError(
                    _("Domain name should not contain spaces: %s") % record.domain
                )

    def action_mark_false_positive(self):
        """Mark this domain report as a false positive."""
        self.ensure_one()
        self.validation_status = "false_positive"
        return True

    def action_mark_valid(self):
        """Mark this domain report as valid."""
        self.ensure_one()
        self.validation_status = "valid"
        return True

    def action_whitelist(self):
        """Whitelist this domain to prevent future false positives."""
        self.ensure_one()
        self.validation_status = "whitelisted"
        return True

    def action_view_tickets(self):
        """Open a view showing all tickets related to this domain report."""
        self.ensure_one()
        action = self.env.ref("helpdesk.helpdesk_ticket_action_main_tree").read()[0]
        action["domain"] = [("domain_report_id", "=", self.id)]
        action["context"] = dict(self.env.context, default_domain_report_id=self.id)
        return action

    @api.model
    def is_whitelisted(self, domain, submitter):
        """
        Check if a domain/submitter combination is whitelisted.

        :param domain: Domain name to check
        :param submitter: Submitter to check
        :return: True if whitelisted, False otherwise
        """
        return bool(
            self.search_count(
                [
                    ("domain", "=", domain),
                    ("submitter", "=", submitter),
                    ("validation_status", "=", "whitelisted"),
                ]
            )
        )

    @api.model
    def is_false_positive(self, domain, submitter):
        """
        Check if a domain/submitter combination is marked as false positive.

        :param domain: Domain name to check
        :param submitter: Submitter to check
        :return: True if false positive, False otherwise
        """
        return bool(
            self.search_count(
                [
                    ("domain", "=", domain),
                    ("submitter", "=", submitter),
                    ("validation_status", "=", "false_positive"),
                ]
            )
        )
