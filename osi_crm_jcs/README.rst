OSI CRM Job Costing Integration
=================================

This module extends CRM leads/opportunities to add job costing data points that flow to the Job Costing System (JCS) when creating job costing records from opportunities.

Features
--------

* Adds job costing related fields to CRM opportunities:
  - Budget Amount
  - Estimated Cost
  - Job Type
  - Expected Start Date
  - Expected End Date
  - Expected Duration (Days) - computed field
  - Job Costing Notes
  - Requires Job Costing flag

* Conditional visibility based on "Requires Job Costing" flag

* Automatic data flow to JCS when creating job costing records from opportunities

* Integration hooks for extending functionality

Usage
-----

1. Open any CRM opportunity
2. Go to the "Job Costing" tab
3. Check "Requires Job Costing" to enable job costing fields
4. Fill in the job costing information
5. Click "Create Job Costing" button to create a job costing record with data from the opportunity

Technical Details
-----------------

* Module inherits from `crm.lead` model
* Uses computed fields for duration calculation
* Provides `_prepare_jcs_values()` method for extensibility
* Integration point: `action_new_job_costing()` method

Dependencies
------------

* crm
* sale_crm

Credits
-------

* Open Source Integrators

License
-------

LGPL-3
