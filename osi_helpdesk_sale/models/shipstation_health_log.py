# Copyright (C) 2025 Open Source Integrators
import logging
from datetime import timedelta
_logger = logging.getLogger(__name__)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class ShipstationHealthLog(models.Model):
    """
    Health Check Log for Shipstation Monitoring
    
    This model stores the history of all health checks performed
    by the Shipstation monitoring system for audit and analysis.
    """
    _name = 'shipstation.health.log'
    _description = 'Shipstation Health Check Log'
    _order = 'check_time desc'
    _rec_name = 'display_name'

    # Basic Information
    monitor_id = fields.Many2one(
        'shipstation.monitor',
        string='Monitor',
        required=True,
        ondelete='cascade',
        help='Associated monitor instance'
    )
    display_name = fields.Char(
        string='Log Entry',
        compute='_compute_display_name',
        store=True,
        help='Computed display name for the log entry'
    )
    
    # Check Details
    check_time = fields.Datetime(
        string='Check Time',
        default=fields.Datetime.now,
        required=True,
        help='Timestamp when the health check was performed'
    )
    status = fields.Selection([
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('unknown', 'Unknown'),
    ], string='Status', required=True, help='Health check result status')
    
    # Performance Metrics
    response_time = fields.Float(
        string='Response Time (ms)',
        help='Response time in milliseconds'
    )
    http_status = fields.Integer(
        string='HTTP Status',
        help='HTTP response status code'
    )
    
    # Error Information
    error_message = fields.Text(
        string='Error Message',
        help='Error message if the check failed'
    )
    error_type = fields.Char(
        string='Error Type',
        help='Type of error that occurred'
    )
    
    # Additional Details
    request_url = fields.Char(
        string='Request URL',
        help='URL that was tested'
    )
    user_agent = fields.Char(
        string='User Agent',
        help='User agent used in the request'
    )
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        help='Number of retries attempted'
    )

    @api.depends('monitor_id', 'check_time', 'status')
    def _compute_display_name(self):
        """Compute display name for the log entry"""
        for record in self:
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'unknown': '❓'
            }.get(record.status, '❓')
            
            monitor_name = record.monitor_id.name if record.monitor_id else 'Unknown'
            check_time_str = record.check_time.strftime('%Y-%m-%d %H:%M:%S') if record.check_time else 'Unknown'
            
            record.display_name = f"{status_icon} {monitor_name} - {check_time_str}"

    @api.model
    def create_log_entry(self, monitor_id, health_result):
        """
        Create a new health log entry
        
        Args:
            monitor_id (int): ID of the monitor
            health_result (dict): Health check results
        """
        return self.create({
            'monitor_id': monitor_id,
            'check_time': fields.Datetime.now(),
            'status': health_result.get('status', 'unknown'),
            'response_time': health_result.get('response_time', 0),
            'http_status': health_result.get('http_status', 0),
            'error_message': health_result.get('error_message', ''),
            'error_type': health_result.get('error_type', ''),
            'request_url': health_result.get('request_url', ''),
            'user_agent': health_result.get('user_agent', ''),
            'retry_count': health_result.get('retry_count', 0),
        })

    def action_view_monitor(self):
        """Open the associated monitor"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Monitor Details'),
            'res_model': 'shipstation.monitor',
            'view_mode': 'form',
            'res_id': self.monitor_id.id,
        }

    @api.model
    def cleanup_old_logs(self, days_to_keep=30):
        """
        Clean up old log entries to prevent database bloat
        
        Args:
            days_to_keep (int): Number of days to keep logs
        """
        cutoff_date = fields.Datetime.now() - timedelta(days=days_to_keep)
        old_logs = self.search([
            ('check_time', '<', cutoff_date)
        ])
        
        if old_logs:
            old_logs.unlink()
            _logger.info(f"Cleaned up {len(old_logs)} old Shipstation health log entries")
