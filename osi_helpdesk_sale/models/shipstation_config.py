# Copyright (C) 2025 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    """
    Configuration Settings for Shipstation Integration
    
    This model provides system-wide configuration options
    for Shipstation integration monitoring and alerting.
    """
    _inherit = 'res.config.settings'

    # Shipstation Integration Settings
    shipstation_enabled = fields.Boolean(
        string='Enable Shipstation Monitoring',
        config_parameter='osi_helpdesk_sale.shipstation_enabled',
        default=True,
        help='Enable Shipstation integration monitoring system'
    )
    
    shipstation_default_api_url = fields.Char(
        string='Default API URL',
        config_parameter='osi_helpdesk_sale.shipstation_default_api_url',
        default='https://ssapi.shipstation.com',
        help='Default Shipstation API URL for new monitors'
    )
    
    shipstation_default_check_interval = fields.Integer(
        string='Default Check Interval (minutes)',
        config_parameter='osi_helpdesk_sale.shipstation_default_check_interval',
        default=15,
        help='Default health check interval in minutes'
    )
    
    shipstation_default_timeout = fields.Integer(
        string='Default Timeout (seconds)',
        config_parameter='osi_helpdesk_sale.shipstation_default_timeout',
        default=30,
        help='Default request timeout in seconds'
    )
    
    shipstation_global_alert_email = fields.Char(
        string='Global Alert Email',
        config_parameter='osi_helpdesk_sale.shipstation_global_alert_email',
        help='Global email address for Shipstation alerts'
    )
    
    shipstation_auto_create_monitor = fields.Boolean(
        string='Auto-create Monitor',
        config_parameter='osi_helpdesk_sale.shipstation_auto_create_monitor',
        default=True,
        help='Automatically create a default monitor when needed'
    )
    
    shipstation_log_retention_days = fields.Integer(
        string='Log Retention (days)',
        config_parameter='osi_helpdesk_sale.shipstation_log_retention_days',
        default=30,
        help='Number of days to keep health check logs'
    )

    @api.model
    def get_values(self):
        """Get configuration values"""
        res = super(ResConfigSettings, self).get_values()
        res.update(
            shipstation_enabled=self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_enabled', 'True'
            ) == 'True',
            shipstation_default_api_url=self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_default_api_url', 'https://ssapi.shipstation.com'
            ),
            shipstation_default_check_interval=int(self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_default_check_interval', '15'
            )),
            shipstation_default_timeout=int(self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_default_timeout', '30'
            )),
            shipstation_global_alert_email=self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_global_alert_email', ''
            ),
            shipstation_auto_create_monitor=self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_auto_create_monitor', 'True'
            ) == 'True',
            shipstation_log_retention_days=int(self.env['ir.config_parameter'].sudo().get_param(
                'osi_helpdesk_sale.shipstation_log_retention_days', '30'
            )),
        )
        return res

    def set_values(self):
        """Set configuration values"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_enabled', str(self.shipstation_enabled)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_default_api_url', self.shipstation_default_api_url
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_default_check_interval', str(self.shipstation_default_check_interval)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_default_timeout', str(self.shipstation_default_timeout)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_global_alert_email', self.shipstation_global_alert_email or ''
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_auto_create_monitor', str(self.shipstation_auto_create_monitor)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'osi_helpdesk_sale.shipstation_log_retention_days', str(self.shipstation_log_retention_days)
        )

    def action_create_default_monitor(self):
        """Create a default Shipstation monitor with current settings"""
        self.ensure_one()
        
        monitor = self.env['shipstation.monitor'].create({
            'name': 'Default Shipstation Monitor',
            'api_url': self.shipstation_default_api_url,
            'check_interval': self.shipstation_default_check_interval,
            'timeout_seconds': self.shipstation_default_timeout,
            'alert_enabled': bool(self.shipstation_global_alert_email),
            'alert_email': self.shipstation_global_alert_email,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Default Monitor Created'),
            'res_model': 'shipstation.monitor',
            'view_mode': 'form',
            'res_id': monitor.id,
            'target': 'new',
        }

    def action_test_shipstation_connection(self):
        """Test Shipstation connection with current settings"""
        self.ensure_one()
        
        if not self.shipstation_enabled:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Monitoring Disabled'),
                    'message': _('Shipstation monitoring is disabled in settings'),
                    'type': 'warning',
                }
            }
        
        # Create a temporary monitor for testing
        test_monitor = self.env['shipstation.monitor'].create({
            'name': 'Test Monitor',
            'api_url': self.shipstation_default_api_url,
            'check_interval': self.shipstation_default_check_interval,
            'timeout_seconds': self.shipstation_default_timeout,
            'alert_enabled': False,  # Don't send alerts for test
        })
        
        try:
            health_result = test_monitor.perform_health_check()
            test_monitor.unlink()  # Clean up test monitor
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Status: %s') % health_result['status'].title(),
                    'type': 'success' if health_result['status'] == 'healthy' else 'warning',
                }
            }
        except Exception as e:
            test_monitor.unlink()  # Clean up test monitor
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': _('Error: %s') % str(e),
                    'type': 'danger',
                }
            }
