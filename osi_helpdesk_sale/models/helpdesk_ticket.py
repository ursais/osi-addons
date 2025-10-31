# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    """Extends helpdesk.ticket to add sales order integration and fix email processing.

    This module extends the helpdesk ticket model to:
    - Link sales orders with helpdesk tickets
    - Create sales orders from tickets
    - Properly handle email parsing to prevent False descriptions
    """

    _inherit = "helpdesk.ticket"

    use_helpdesk_sale_orders = fields.Boolean(
        string="Sale Order activated on Team",
        related="team_id.use_sale_orders",
        readonly=True,
    )
    sale_ids = fields.Many2many(
        "sale.order",
        "sale_helpdesk_ticket_rel",
        "ticket_id",
        "sale_id",
        copy=False,
    )
    sale_count = fields.Integer(
        string="Sales Order Count", compute="_compute_sale_order_count"
    )

    def _compute_sale_order_count(self):
        """Compute the count of related sales orders."""
        for ticket in self:
            ticket.sale_count = self.env["sale.order"].search_count(
                [("helpdesk_ticket_ids", "in", ticket.id)]
            )

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Override message_new to properly handle email parsing.

        This method ensures that ticket descriptions are never set to False
        and properly extracts subject and body from incoming emails, even
        when dealing with unusual email formats like automated reports from
        email security services (e.g., Mimecast).

        The fix addresses issues where emails from specific domains result in
        tickets with False as the description due to failed email parsing.

        Args:
            msg_dict (dict): Dictionary containing message details from email gateway.
                Expected keys: 'subject', 'body', 'email_from', etc.
            custom_values (dict, optional): Custom values to set on the ticket.
                Can contain 'description', 'name', etc.

        Returns:
            recordset: Newly created helpdesk ticket

        Raises:
            None: Errors are logged but don't prevent ticket creation
        """
        custom_values = custom_values or {}

        # Extract email content
        subject = msg_dict.get("subject") or ""
        body = msg_dict.get("body") or ""
        email_from = msg_dict.get("email_from", "")

        # Get description from custom_values first (if provided by parent logic)
        original_desc = custom_values.get("description")
        description = original_desc

        # If description is not provided or is False, extract from email
        if not description or description is False:
            # Prefer body over subject for description
            if body and body.strip():
                description = body
            elif subject and subject.strip():
                # Use subject as description if no body available
                description = subject
            else:
                # Fallback to empty string instead of False
                description = ""

        # Ensure description is never False - convert to empty string
        if description is False:
            description = ""

        # Ensure description is a string type
        if not isinstance(description, str):
            description = str(description) if description else ""

        # Clean up whitespace
        description = description.strip() if description else ""

        # Update custom_values with properly processed description
        custom_values["description"] = description

        # Log warning if we had to fix problematic email parsing (False description)
        if original_desc is False:
            _logger.warning(
                "Helpdesk ticket email processing: Fixed missing or False description. "
                "Subject: %s, Email From: %s",
                subject[:100] if subject else "No subject",
                email_from[:100] if email_from else "Unknown",
            )

        return super().message_new(msg_dict, custom_values=custom_values)

    def create_sale_order(self):
        """Create a sales order from this helpdesk ticket.

        Returns:
            dict: Action dictionary to open the created sales order form view

        Raises:
            ValidationError: If partner has a blocking sales warning
        """
        self.ensure_one()
        if self.partner_id.sale_warn == "block":
            msg = "Warning for Partner {}\n\n{}".format(
                self.partner_id.name, self.partner_id.sale_warn_msg
            )
            raise ValidationError(_(msg))
        order_id = self.env["sale.order"].create(
            {
                "partner_id": self.partner_id.id,
                "user_id": self.user_id.id,
                "note": self.description,
            }
        )
        order_id.helpdesk_ticket_ids = [(6, 0, self.ids)]
        return {
            "name": _("Create Sales Order"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": order_id.id,
        }

    def action_view_sale_order(self):
        """Open a view showing all sales orders related to this ticket.

        Returns:
            dict: Action dictionary to open sales order list/form view
        """
        for helpdesk_ticket_id in self:
            sale_order_ids = self.env["sale.order"].search(
                [("helpdesk_ticket_ids", "in", helpdesk_ticket_id.ids)]
            )
            action = self.env.ref("sale.action_orders").read()[0]
            action["context"] = {}
            if len(sale_order_ids) == 1:
                action["views"] = [(self.env.ref("sale.view_order_form").id, "form")]
                action["res_id"] = sale_order_ids.ids[0]
            else:
                action["domain"] = [("id", "in", sale_order_ids.ids)]
            return action
