# Copyright (C) 2022 - TODAY, Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
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
    
    # Shipstation Integration Fields
    shipstation_status = fields.Selection([
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('unknown', 'Unknown'),
        ('not_configured', 'Not Configured'),
    ], string='Shipstation Status', default='unknown', tracking=True,
       help='Current status of Shipstation integration')
    
    shipstation_last_check = fields.Datetime(
        string='Last Shipstation Check',
        help='Timestamp of the last Shipstation health check'
    )
    
    shipstation_error_message = fields.Text(
        string='Shipstation Error',
        help='Last error message from Shipstation integration'
    )
    
    shipstation_response_time = fields.Float(
        string='Response Time (ms)',
        help='Last response time from Shipstation API in milliseconds'
    )
    
    shipstation_monitor_id = fields.Many2one(
        'shipstation.monitor',
        string='Shipstation Monitor',
        help='Associated Shipstation monitor instance'
    )

    def _compute_sale_order_count(self):
        for ticket in self:
            ticket.sale_count = self.env["sale.order"].search_count(
                [("helpdesk_ticket_ids", "in", ticket.id)]
            )

    def create_sale_order(self):
        self.ensure_one()
        if self.partner_id.sale_warn == "block":
            msg = "Warning for Partner {}\\n\\n{}".format(
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

    def check_shipstation_status(self):
        """
        Check the current status of Shipstation integration
        and update the ticket with the latest information
        """
        self.ensure_one()
        
        # Get the default monitor or create one if none exists
        monitor = self.env['shipstation.monitor'].create_default_monitor()
        
        if not monitor.api_key or not monitor.api_secret:
            self.write({
                'shipstation_status': 'not_configured',
                'shipstation_error_message': 'Shipstation API credentials not configured',
                'shipstation_last_check': fields.Datetime.now(),
                'shipstation_monitor_id': monitor.id,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Shipstation Check'),
                    'message': _('Shipstation API credentials not configured'),
                    'type': 'warning',
                }
            }
        
        try:
            # Perform health check
            health_result = monitor.perform_health_check()
            
            # Update ticket with results
            self.write({
                'shipstation_status': health_result['status'],
                'shipstation_last_check': fields.Datetime.now(),
                'shipstation_error_message': health_result.get('error_message', ''),
                'shipstation_response_time': health_result.get('response_time', 0),
                'shipstation_monitor_id': monitor.id,
            })
            
            # Create log entry
            self.env['shipstation.health.log'].create_log_entry(monitor.id, health_result)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Shipstation Status Check'),
                    'message': _('Status: %s') % health_result['status'].title(),
                    'type': 'success' if health_result['status'] == 'healthy' else 'warning',
                }
            }
            
        except Exception as e:
            self.write({
                'shipstation_status': 'critical',
                'shipstation_error_message': f'Check failed: {str(e)}',
                'shipstation_last_check': fields.Datetime.now(),
                'shipstation_monitor_id': monitor.id,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Shipstation Check Failed'),
                    'message': _('Error: %s') % str(e),
                    'type': 'danger',
                }
            }

    def action_view_shipstation_monitor(self):
        """Open the Shipstation monitor dashboard"""
        self.ensure_one()
        
        if not self.shipstation_monitor_id:
            # Create default monitor if none exists
            monitor = self.env['shipstation.monitor'].create_default_monitor()
            self.shipstation_monitor_id = monitor.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Shipstation Monitor'),
            'res_model': 'shipstation.monitor',
            'view_mode': 'form',
            'res_id': self.shipstation_monitor_id.id,
        }

    def action_view_shipstation_logs(self):
        """Open Shipstation health check logs"""
        self.ensure_one()
        
        if not self.shipstation_monitor_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Monitor'),
                    'message': _('No Shipstation monitor associated with this ticket'),
                    'type': 'warning',
                }
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Shipstation Health Logs'),
            'res_model': 'shipstation.health.log',
            'view_mode': 'tree,form',
            'domain': [('monitor_id', '=', self.shipstation_monitor_id.id)],
            'context': {'default_monitor_id': self.shipstation_monitor_id.id},
        }
