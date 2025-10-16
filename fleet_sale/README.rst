.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

================
Fleet Sales
================

This module extends the fleet management functionality by integrating it with the sales module, allowing users to associate sale orders with fleet vehicles and track sales performance by vehicle.

Features
========

* **Vehicle-Sale Order Integration**: Link sale orders to specific fleet vehicles
* **Sale Order Tracking**: View and count sale orders associated with each vehicle
* **Quick Access**: Navigate from vehicle records to related sale orders
* **Audit Trail**: Track changes to vehicle assignments on sale orders
* **User-Friendly Interface**: Intuitive buttons and fields for easy navigation

Installation
============

1. Install the module dependencies:
   - fleet (Fleet Management)
   - sale_management (Sales Management)

2. Install the module through the Odoo Apps interface or by running:
   .. code-block:: bash
   
       odoo-bin -d your_database -i fleet_sale

Configuration
=============

1. **Fleet Management Setup**: Ensure you have vehicles configured in Fleet > Configuration > Vehicles
2. **Sales Team Access**: Users need sales team permissions to view sale order counts on vehicles
3. **Fleet User Access**: Users need fleet user permissions to see the vehicle field on sale orders

Usage
=====

**From Fleet Vehicles:**
1. Go to Fleet > Fleet > Vehicles
2. Open any vehicle record
3. Click the "Sale Orders" button to view associated sale orders
4. The button shows the count of sale orders for that vehicle

**From Sale Orders:**
1. Go to Sales > Sales > Quotations or Sales > Sales > Orders
2. Create or edit a sale order
3. Select a vehicle from the "Vehicle" field (appears after Payment Terms)
4. The vehicle selection is tracked for audit purposes

**Reporting:**
- Filter sale orders by vehicle using the vehicle field
- Use the vehicle sale count for performance analysis
- Track vehicle utilization through sale order history

Technical Details
=================

**Models Extended:**
- ``fleet.vehicle``: Added sale order relationships and count functionality
- ``sale.order``: Added vehicle field for linking to fleet vehicles

**Key Features:**
- One2many relationship from vehicles to sale orders
- Computed field for sale order count (not stored for performance)
- Many2one relationship from sale orders to vehicles
- Proper field tracking and audit capabilities
- User group-based visibility controls

**Performance Considerations:**
- Sale order count is computed on-demand (not stored)
- Proper indexing on vehicle_id field for efficient queries
- Minimal impact on existing functionality

Known Issues / Roadmap
======================

* No known issues
* Future enhancements may include:
  - Vehicle performance analytics
  - Revenue tracking by vehicle
  - Maintenance scheduling based on sales activity

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/partner-contact/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Authors
~~~~~~~

* Open Source Integrators

Maintainers
~~~~~~~~~~~

This module is maintained by Open Source Integrators.

.. image:: https://opensourceintegrators.com/logo.png
   :alt: Open Source Integrators
   :target: https://opensourceintegrators.com

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org
