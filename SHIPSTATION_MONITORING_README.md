# Shipstation Integration Monitoring System

## Overview

This solution implements a comprehensive monitoring and health checking system for Shipstation integration within the OSI Helpdesk Sale module. The system provides real-time monitoring, automated health checks, alerting, and detailed logging to ensure Shipstation integration reliability.

## Features

### 🔍 Real-time Monitoring
- Continuous health checks of Shipstation API connectivity
- Response time monitoring and performance tracking
- Status tracking (Healthy, Warning, Critical, Unknown, Not Configured)
- Uptime percentage calculation

### 🚨 Automated Alerting
- Email alerts for critical issues
- Configurable alert thresholds
- Spam prevention (max 1 alert per hour)
- Detailed error reporting

### 📊 Dashboard & Analytics
- Visual dashboard with status indicators
- Health check history and logs
- Performance metrics and statistics
- Filterable views and search capabilities

### ⚙️ Configuration Management
- System-wide configuration settings
- Default monitor creation
- API credential management
- Customizable check intervals and timeouts

## Components

### Models

1. **ShipstationMonitor** (`shipstation.monitor`)
   - Main monitoring model
   - Handles health checks and status tracking
   - Manages API credentials and configuration

2. **ShipstationHealthLog** (`shipstation.health.log`)
   - Stores health check history
   - Provides audit trail and analysis
   - Automatic cleanup of old logs

3. **HelpdeskTicket** (Enhanced)
   - Added Shipstation status fields
   - Integration with monitoring system
   - Quick status check functionality

4. **ResConfigSettings** (Enhanced)
   - System-wide configuration
   - Default settings management
   - Connection testing

### Views

1. **Monitor Dashboard**
   - Tree, form, and kanban views
   - Real-time status display
   - Action buttons for health checks

2. **Health Logs**
   - Detailed log history
   - Error tracking and analysis
   - Performance metrics

3. **Helpdesk Ticket Integration**
   - Shipstation status in ticket views
   - Quick status check buttons
   - Error message display

4. **Configuration Settings**
   - System settings interface
   - Connection testing
   - Default monitor creation

### Automated Processes

1. **Scheduled Health Checks**
   - Runs every 15 minutes (configurable)
   - Automatic status updates
   - Error detection and alerting

2. **Log Cleanup**
   - Daily cleanup of old logs
   - Configurable retention period
   - Database maintenance

## Installation & Setup

### Prerequisites
- Odoo 18.0+
- Python `requests` library
- Valid Shipstation API credentials

### Installation Steps

1. **Install the Module**
   ```bash
   # The module will be automatically installed when the addon is loaded
   ```

2. **Configure Shipstation Settings**
   - Go to Settings > Shipstation Integration
   - Enable monitoring system
   - Set default API URL and credentials
   - Configure alert email addresses

3. **Create Monitor Instance**
   - Navigate to Shipstation Monitoring > Monitors
   - Create a new monitor with your API credentials
   - Configure check intervals and alerting

4. **Test Connection**
   - Use the "Test Connection" button in settings
   - Verify API credentials and connectivity
   - Check initial health status

## Usage

### Monitoring Dashboard

1. **View Status**
   - Navigate to Shipstation Monitoring > Monitors
   - View real-time status of all monitors
   - Check response times and uptime percentages

2. **Manual Health Check**
   - Click "Run Health Check" button
   - View immediate status update
   - Check for any errors or warnings

3. **View History**
   - Click "View History" to see health check logs
   - Analyze performance trends
   - Review error details

### Helpdesk Integration

1. **Ticket Status**
   - Shipstation status is displayed in ticket views
   - Color-coded status indicators
   - Quick access to monitor dashboard

2. **Quick Status Check**
   - Use "Check Status" button in tickets
   - Get immediate status update
   - View error messages if any

### Configuration

1. **System Settings**
   - Configure default API URL
   - Set check intervals and timeouts
   - Manage global alert settings

2. **Monitor Management**
   - Create multiple monitors for different environments
   - Configure individual alert settings
   - Manage API credentials securely

## API Integration

### Health Check Process

1. **Authentication**
   - Uses HTTP Basic Auth with API key and secret
   - Validates credentials before each check

2. **Endpoint Testing**
   - Tests `/stores` endpoint for basic connectivity
   - Measures response time
   - Captures HTTP status codes

3. **Error Handling**
   - Timeout detection
   - Connection error handling
   - HTTP error code interpretation
   - Authentication failure detection

### Status Classification

- **Healthy**: API responds with 200 status
- **Warning**: Unexpected response (4xx client errors)
- **Critical**: Server errors (5xx), timeouts, connection failures
- **Unknown**: Initial state or configuration issues
- **Not Configured**: Missing API credentials

## Alerting System

### Email Templates

1. **Critical Alert**
   - Immediate notification for critical issues
   - Detailed error information
   - Action recommendations

2. **Warning Alert**
   - Notification for warning conditions
   - Monitoring recommendations
   - Escalation guidance

### Alert Configuration

- Configurable email addresses
- Spam prevention (max 1 alert per hour)
- Detailed error reporting
- Direct links to monitor dashboard

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Verify API key and secret
   - Check credential format
   - Ensure proper permissions

2. **Connection Timeouts**
   - Check network connectivity
   - Verify API URL
   - Adjust timeout settings

3. **False Alerts**
   - Review check intervals
   - Adjust timeout values
   - Check for temporary issues

### Log Analysis

1. **Health Logs**
   - Review error messages
   - Check response times
   - Analyze failure patterns

2. **System Logs**
   - Check Odoo logs for detailed errors
   - Monitor cron job execution
   - Verify email delivery

## Maintenance

### Regular Tasks

1. **Monitor Review**
   - Check monitor status regularly
   - Review alert configurations
   - Update API credentials as needed

2. **Log Cleanup**
   - Automatic cleanup of old logs
   - Manual cleanup if needed
   - Archive important logs

3. **Performance Monitoring**
   - Review response times
   - Check uptime percentages
   - Optimize check intervals

## Security Considerations

1. **API Credentials**
   - Store credentials securely
   - Use environment variables when possible
   - Regular credential rotation

2. **Access Control**
   - Restrict monitor access to authorized users
   - Use appropriate security groups
   - Audit access logs

3. **Data Protection**
   - Secure transmission of health check data
   - Protect log data from unauthorized access
   - Regular security reviews

## Support

For technical support or questions about the Shipstation monitoring system:

1. Check the health logs for error details
2. Review system configuration
3. Test API connectivity manually
4. Contact system administrator for assistance

## Version History

- **18.0.1.0.0**: Initial release with comprehensive monitoring features
  - Real-time health checking
  - Automated alerting system
  - Dashboard and analytics
  - Helpdesk integration
  - Configuration management
