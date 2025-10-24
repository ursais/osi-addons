# Copyright (C) 2025 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
import requests
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ShipstationMonitor(models.Model):
    """
    Shipstation Integration Monitoring System
    
    This model provides comprehensive monitoring and health checking
    for Shipstation integration to detect outages and system issues.
    """
    _name = 'shipstation.monitor'
    _description = 'Shipstation Integration Monitor'
    _order = 'last_check desc'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(
        string='Monitor Name',
        required=True,
        default='Shipstation Health Check',
        help='Name of the monitoring instance'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Computed display name for the monitor'
    )
    
    # Status Fields
    status = fields.Selection([
        ('healthy', 'Healthy'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
        ('unknown', 'Unknown'),
    ], string='Status', default='unknown', required=True, tracking=True)
    
    last_check = fields.Datetime(
        string='Last Check',
        default=fields.Datetime.now,
        help='Timestamp of the last health check'
    )
    next_check = fields.Datetime(
        string='Next Check',
        compute='_compute_next_check',
        store=True,
        help='Scheduled time for the next health check'
    )
    
    # Configuration
    api_url = fields.Char(
        string='API URL',
        default='https://ssapi.shipstation.com',
        required=True,
        help='Shipstation API base URL'
    )
    api_key = fields.Char(
        string='API Key',
        required=True,
        help='Shipstation API key for authentication'
    )
    api_secret = fields.Char(
        string='API Secret',
        required=True,
        help='Shipstation API secret for authentication'
    )
    
    # Monitoring Settings
    check_interval = fields.Integer(
        string='Check Interval (minutes)',
        default=15,
        help='Interval between health checks in minutes'
    )
    timeout_seconds = fields.Integer(
        string='Timeout (seconds)',
        default=30,
        help='Request timeout in seconds'
    )
    retry_attempts = fields.Integer(
        string='Retry Attempts',
        default=3,
        help='Number of retry attempts on failure'
    )
    
    # Health Check Results
    response_time = fields.Float(
        string='Response Time (ms)',
        help='Last response time in milliseconds'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Last error message if any'
    )
    http_status = fields.Integer(
        string='HTTP Status',
        help='Last HTTP response status code'
    )
    
    # Alerting
    alert_enabled = fields.Boolean(
        string='Enable Alerts',
        default=True,
        help='Enable email alerts for critical issues'
    )
    alert_email = fields.Char(
        string='Alert Email',
        help='Email address for critical alerts'
    )
    last_alert = fields.Datetime(
        string='Last Alert Sent',
        help='Timestamp of the last alert sent'
    )
    
    # Statistics
    total_checks = fields.Integer(
        string='Total Checks',
        default=0,
        help='Total number of health checks performed'
    )
    successful_checks = fields.Integer(
        string='Successful Checks',
        default=0,
        help='Number of successful health checks'
    )
    failed_checks = fields.Integer(
        string='Failed Checks',
        default=0,
        help='Number of failed health checks'
    )
    uptime_percentage = fields.Float(
        string='Uptime %',
        compute='_compute_uptime_percentage',
        store=True,
        help='Percentage of successful checks'
    )

    @api.depends('name', 'status', 'last_check')
    def _compute_display_name(self):
        """Compute display name for the monitor"""
        for record in self:
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'unknown': '❓'
            }.get(record.status, '❓')
            
            last_check_str = ''
            if record.last_check:
                last_check_str = f" ({record.last_check.strftime('%Y-%m-%d %H:%M')})"
            
            record.display_name = f"{status_icon} {record.name}{last_check_str}"

    @api.depends('last_check', 'check_interval')
    def _compute_next_check(self):
        """Compute next check time based on interval"""
        for record in self:
            if record.last_check and record.check_interval:
                record.next_check = record.last_check + timedelta(minutes=record.check_interval)
            else:
                record.next_check = fields.Datetime.now()

    @api.depends('total_checks', 'successful_checks')
    def _compute_uptime_percentage(self):
        """Compute uptime percentage"""
        for record in self:
            if record.total_checks > 0:
                record.uptime_percentage = (record.successful_checks / record.total_checks) * 100
            else:
                record.uptime_percentage = 0.0

    def perform_health_check(self):
        """
        Perform a health check against Shipstation API
        
        Returns:
            dict: Health check results
        """
        self.ensure_one()
        
        if not self.api_key or not self.api_secret:
            raise ValidationError(_("API Key and Secret are required for health checks"))
        
        start_time = datetime.now()
        result = {
            'status': 'unknown',
            'response_time': 0,
            'error_message': '',
            'http_status': 0
        }
        
        try:
            # Prepare authentication
            auth = (self.api_key, self.api_secret)
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Odoo-Shipstation-Monitor/1.0'
            }
            
            # Test API connectivity with a simple endpoint
            test_url = f"{self.api_url}/stores"
            
            _logger.info(f"Performing Shipstation health check for monitor {self.name}")
            
            response = requests.get(
                test_url,
                auth=auth,
                headers=headers,
                timeout=self.timeout_seconds
            )
            
            # Calculate response time
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            result['response_time'] = response_time
            result['http_status'] = response.status_code
            
            if response.status_code == 200:
                result['status'] = 'healthy'
                result['error_message'] = ''
                _logger.info(f"Shipstation health check successful: {response_time:.2f}ms")
            elif response.status_code == 401:
                result['status'] = 'critical'
                result['error_message'] = 'Authentication failed - check API credentials'
                _logger.error("Shipstation authentication failed")
            elif response.status_code == 403:
                result['status'] = 'critical'
                result['error_message'] = 'Access forbidden - check API permissions'
                _logger.error("Shipstation access forbidden")
            elif response.status_code >= 500:
                result['status'] = 'critical'
                result['error_message'] = f'Server error: HTTP {response.status_code}'
                _logger.error(f"Shipstation server error: {response.status_code}")
            else:
                result['status'] = 'warning'
                result['error_message'] = f'Unexpected response: HTTP {response.status_code}'
                _logger.warning(f"Shipstation unexpected response: {response.status_code}")
                
        except requests.exceptions.Timeout:
            result['status'] = 'critical'
            result['error_message'] = f'Request timeout after {self.timeout_seconds} seconds'
            _logger.error(f"Shipstation health check timeout: {self.timeout_seconds}s")
        except requests.exceptions.ConnectionError:
            result['status'] = 'critical'
            result['error_message'] = 'Connection error - check network connectivity'
            _logger.error("Shipstation connection error")
        except requests.exceptions.RequestException as e:
            result['status'] = 'critical'
            result['error_message'] = f'Request error: {str(e)}'
            _logger.error(f"Shipstation request error: {e}")
        except Exception as e:
            result['status'] = 'critical'
            result['error_message'] = f'Unexpected error: {str(e)}'
            _logger.error(f"Shipstation health check unexpected error: {e}")
        
        return result

    def update_health_status(self, health_result):
        """
        Update monitor status based on health check results
        
        Args:
            health_result (dict): Results from health check
        """
        self.ensure_one()
        
        # Update status fields
        self.status = health_result['status']
        self.last_check = fields.Datetime.now()
        self.response_time = health_result['response_time']
        self.error_message = health_result['error_message']
        self.http_status = health_result['http_status']
        
        # Update statistics
        self.total_checks += 1
        if health_result['status'] == 'healthy':
            self.successful_checks += 1
        else:
            self.failed_checks += 1
        
        # Send alert if critical and alerts enabled
        if (health_result['status'] == 'critical' and 
            self.alert_enabled and 
            self.alert_email):
            self._send_critical_alert(health_result)
        
        _logger.info(f"Updated Shipstation monitor {self.name}: {health_result['status']}")

    def _send_critical_alert(self, health_result):
        """
        Send critical alert email
        
        Args:
            health_result (dict): Health check results
        """
        self.ensure_one()
        
        # Prevent spam - only send one alert per hour
        if (self.last_alert and 
            fields.Datetime.now() - self.last_alert < timedelta(hours=1)):
            return
        
        try:
            mail_template = self.env.ref('osi_helpdesk_sale.shipstation_critical_alert_template')
            mail_template.send_mail(self.id, force_send=True)
            self.last_alert = fields.Datetime.now()
            _logger.info(f"Sent critical alert for Shipstation monitor {self.name}")
        except Exception as e:
            _logger.error(f"Failed to send critical alert: {e}")

    def run_health_check(self):
        """Run health check and update status"""
        self.ensure_one()
        
        try:
            health_result = self.perform_health_check()
            self.update_health_status(health_result)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Health Check Complete'),
                    'message': _('Shipstation status: %s') % health_result['status'].title(),
                    'type': 'success' if health_result['status'] == 'healthy' else 'warning',
                }
            }
        except Exception as e:
            _logger.error(f"Health check failed for {self.name}: {e}")
            raise UserError(_('Health check failed: %s') % str(e))

    def action_view_health_history(self):
        """Open health check history view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Health Check History'),
            'res_model': 'shipstation.health.log',
            'view_mode': 'tree,form',
            'domain': [('monitor_id', '=', self.id)],
            'context': {'default_monitor_id': self.id},
        }

    @api.model
    def run_scheduled_checks(self):
        """
        Run scheduled health checks for all active monitors
        This method is called by the cron job
        """
        monitors = self.search([
            ('next_check', '<=', fields.Datetime.now())
        ])
        
        for monitor in monitors:
            try:
                health_result = monitor.perform_health_check()
                monitor.update_health_status(health_result)
            except Exception as e:
                _logger.error(f"Scheduled health check failed for {monitor.name}: {e}")
                # Update status to critical on exception
                monitor.write({
                    'status': 'critical',
                    'error_message': f'Scheduled check failed: {str(e)}',
                    'last_check': fields.Datetime.now(),
                    'total_checks': monitor.total_checks + 1,
                    'failed_checks': monitor.failed_checks + 1,
                })

    @api.model
    def create_default_monitor(self):
        """Create default monitor if none exists"""
        if not self.search([]):
            return self.create({
                'name': 'Default Shipstation Monitor',
                'api_url': 'https://ssapi.shipstation.com',
                'check_interval': 15,
                'alert_enabled': True,
            })
        return self.search([], limit=1)
