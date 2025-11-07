# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
import logging

from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    """Extends helpdesk.ticket to add fleet vehicle integration.
    
    This model adds the ability to link a fleet vehicle to a helpdesk ticket,
    enabling support teams to track vehicle-related issues and maintenance
    requests through the helpdesk system.
    
    Additionally, this model includes domain validation logic for handling
    domain-based reports, ensuring proper processing of automated reports
    that include domain information in their titles or descriptions.
    """
    
    _inherit = "helpdesk.ticket"

    # Relational Fields
    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string="Vehicle",
        copy=False,
        help="The fleet vehicle associated with this helpdesk ticket. "
             "Use this to link vehicle maintenance or issue requests to tickets."
    )
    
    # Domain-related Fields
    report_domain = fields.Char(
        string="Report Domain",
        compute="_compute_report_domain",
        store=True,
        help="Extracted domain from report title or description. "
             "Used for domain-based report validation and processing."
    )
    
    report_submitter = fields.Char(
        string="Report Submitter",
        compute="_compute_report_metadata",
        store=True,
        help="Extracted submitter information from report title or description."
    )
    
    report_id = fields.Char(
        string="Report ID",
        compute="_compute_report_metadata",
        store=True,
        help="Extracted report ID from report title or description."
    )
    
    domain_validated = fields.Boolean(
        string="Domain Validated",
        compute="_compute_domain_validated",
        store=True,
        help="Indicates whether the domain has been successfully validated."
    )

    @api.depends("name", "description")
    def _compute_report_domain(self):
        """Extract domain from ticket title or description.
        
        Handles formats like:
        - "Report domain: example.com Submitter: ..."
        - "Domain: example.com"
        """
        for ticket in self:
            domain = None
            if ticket.name:
                domain = self._extract_domain_from_text(ticket.name)
            if not domain and ticket.description:
                domain = self._extract_domain_from_text(ticket.description)
            ticket.report_domain = domain

    @api.depends("name", "description")
    def _compute_report_metadata(self):
        """Extract submitter and report ID from ticket title or description.
        
        Handles formats like:
        - "Report domain: example.com Submitter: submitter.org Report-ID: abc123"
        """
        for ticket in self:
            submitter = None
            report_id = None
            text = ticket.name or ""
            if ticket.description and ticket.description is not False:
                # Handle boolean False or string "False"
                desc_str = str(ticket.description)
                if desc_str.strip().lower() != 'false':
                    text += " " + desc_str
            
            # Extract submitter
            submitter_match = re.search(
                r"Submitter:\s*([^\s]+)", text, re.IGNORECASE
            )
            if submitter_match:
                submitter = submitter_match.group(1).strip()
            
            # Extract report ID
            report_id_match = re.search(
                r"Report-ID:\s*([^\s]+)", text, re.IGNORECASE
            )
            if report_id_match:
                report_id = report_id_match.group(1).strip()
            
            ticket.report_submitter = submitter
            ticket.report_id = report_id

    @api.depends("report_domain")
    def _compute_domain_validated(self):
        """Validate the extracted domain.
        
        Returns True if domain is valid, False otherwise.
        Handles edge cases like empty domains, invalid formats, etc.
        """
        for ticket in self:
            if not ticket.report_domain:
                ticket.domain_validated = False
                continue
            
            try:
                ticket.domain_validated = self._validate_domain(ticket.report_domain)
            except Exception as e:
                _logger.warning(
                    "Domain validation failed for ticket %s (ID: %s): %s",
                    ticket.name,
                    ticket.id,
                    str(e)
                )
                ticket.domain_validated = False

    def _extract_domain_from_text(self, text):
        """Extract domain from text using pattern matching.
        
        Args:
            text (str): Text to extract domain from
            
        Returns:
            str: Extracted domain or None if not found
        """
        # Handle None, empty, boolean False, or string "False"
        if not text or text is False:
            return None
        
        # Handle string "False"
        if isinstance(text, str) and text.strip().lower() == 'false':
            return None
        
        text = str(text)
        
        # Pattern 1: "Report domain: example.com"
        pattern1 = re.search(
            r"Report\s+domain:\s*([^\s]+)", text, re.IGNORECASE
        )
        if pattern1:
            domain = pattern1.group(1).strip()
            if self._is_valid_domain_format(domain):
                return domain
        
        # Pattern 2: "Domain: example.com"
        pattern2 = re.search(
            r"Domain:\s*([^\s]+)", text, re.IGNORECASE
        )
        if pattern2:
            domain = pattern2.group(1).strip()
            if self._is_valid_domain_format(domain):
                return domain
        
        return None

    def _is_valid_domain_format(self, domain):
        """Check if a string has a valid domain format.
        
        Args:
            domain (str): Domain string to validate
            
        Returns:
            bool: True if format is valid, False otherwise
        """
        if not domain or not isinstance(domain, str):
            return False
        
        domain = domain.strip()
        
        # Basic domain format validation
        # Domain should contain at least one dot and valid characters
        domain_pattern = re.compile(
            r"^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )
        
        # Also allow IP addresses if needed (optional)
        ip_pattern = re.compile(
            r"^(\d{1,3}\.){3}\d{1,3}$"
        )
        
        return bool(domain_pattern.match(domain) or ip_pattern.match(domain))

    def _validate_domain(self, domain):
        """Validate domain using comprehensive checks.
        
        Args:
            domain (str): Domain to validate
            
        Returns:
            bool: True if domain is valid, False otherwise
            
        Raises:
            ValidationError: If domain format is invalid
        """
        if not domain:
            return False
        
        domain = str(domain).strip().lower()
        
        # Check basic format
        if not self._is_valid_domain_format(domain):
            return False
        
        # Additional validation: check for common issues
        # Remove trailing dots/spaces
        domain = domain.rstrip('. ')
        
        # Check length (max 253 characters for FQDN)
        if len(domain) > 253:
            return False
        
        # Check for valid TLD (at least 2 characters)
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        
        tld = parts[-1]
        if len(tld) < 2:
            return False
        
        # Check each part length (max 63 characters per label)
        for part in parts:
            if len(part) > 63:
                return False
            if len(part) == 0:
                return False
        
        return True

    @api.model
    def create(self, vals):
        """Override create to handle domain validation for new tickets.
        
        Ensures that domain-based reports are properly processed and validated.
        """
        # Extract and validate domain if present in title or description
        if 'name' in vals or 'description' in vals:
            # Create a temporary record to compute domain fields
            temp_ticket = self.new(vals)
            temp_ticket._compute_report_domain()
            temp_ticket._compute_report_metadata()
            temp_ticket._compute_domain_validated()
            
            # Store computed values
            if temp_ticket.report_domain:
                vals['report_domain'] = temp_ticket.report_domain
            if temp_ticket.report_submitter:
                vals['report_submitter'] = temp_ticket.report_submitter
            if temp_ticket.report_id:
                vals['report_id'] = temp_ticket.report_id
            vals['domain_validated'] = temp_ticket.domain_validated
            # Log domain validation results for debugging
            if temp_ticket.report_domain:
                _logger.info(
                    "Domain report detected - Domain: %s, Validated: %s, "
                    "Ticket: %s",
                    temp_ticket.report_domain,
                    temp_ticket.domain_validated,
                    vals.get('name', 'New Ticket')
                )
        
        return super(HelpdeskTicket, self).create(vals)

    def write(self, vals):
        """Override write to handle domain validation on updates.
        
        Re-validates domain when title or description changes.
        """
        result = super(HelpdeskTicket, self).write(vals)
        
        # Recompute domain fields if title or description changed
        if 'name' in vals or 'description' in vals:
            self._compute_report_domain()
            self._compute_report_metadata()
            self._compute_domain_validated()
        
        return result
