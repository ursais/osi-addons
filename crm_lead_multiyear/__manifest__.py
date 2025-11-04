# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "CRM Lead Multi-Year Fields",
    "version": "12.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Add Multi-Year and Number of Years fields to CRM Lead",
    "description": """
        This module adds two new fields to CRM Leads:
        - Multi-Year: Yes/No selection
        - Number of Years: Numeric value from 1 to 20
        
        These fields are conditionally visible and required based on project type
        (Monitoring, Test and Inspection, or Renew - Test and Inspection).
    """,
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "crm",
    ],
    "data": [
        'views/crm_lead_views.xml',
    ],
    "application": False,
    "development_status": "Stable",
    "maintainers": [
        "osi-addons",
    ],
}
