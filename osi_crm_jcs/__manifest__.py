# Copyright (C) 2024 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "OSI CRM Job Costing Integration",
    "version": "12.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Add data points to opportunities that flow to JCS on create",
    "description": """
        DCFI-924: New data points on opportunities and to flow to JCS on create from opportunity
        
        This module adds new fields to CRM leads/opportunities for job costing integration.
        These fields include budget information, job type, and other relevant data points
        that need to flow to the Job Costing System (JCS) when creating a job costing
        record from an opportunity.
        
        Features:
        - Adds job costing related fields to CRM opportunities
        - Conditional visibility based on lead type
        - Data flow to JCS when creating from opportunity
    """,
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "http://www.opensourceintegrators.com",
    "category": "CRM",
    "depends": [
        'crm',
        'sale_crm',
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/crm_lead_views.xml",
    ],
    "installable": True,
    "application": False,
}
