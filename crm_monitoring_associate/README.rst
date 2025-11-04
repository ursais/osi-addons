CRM Monitoring Sales Associate
===============================

This module adds monitoring-related fields to CRM leads:

* **monitoring_included**: Boolean field to indicate if monitoring is included
* **monitoring_sales_associate_id**: Sales associate assigned for monitoring (visible only when monitoring_included is True)

The Monitoring Sales Associate field appears conditionally on the CRM lead form based on the monitoring_included field value.

Installation
------------

Install the module from Apps menu or via command line:

.. code-block:: bash

    odoo-bin -c odoo.conf -u crm_monitoring_associate

Usage
-----

1. Open a CRM Lead/Opportunity form
2. Check the "Monitoring Included" checkbox if monitoring is included
3. The "Monitoring Sales Associate" field will appear and become required
4. Select the appropriate sales associate

Technical Details
-----------------

* Extends: crm.lead model
* Views: Inherits from crm_case_form_view_oppor and crm_case_form_view_leads
* Fields:
  - monitoring_included (Boolean)
  - monitoring_sales_associate_id (Many2one to res.users)
