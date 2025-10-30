================
Fleet Helpdesk
================

.. contents::
   :local:

Overview
========

The Fleet Helpdesk module integrates Odoo's Fleet and Helpdesk applications,
enabling users to link fleet vehicles with helpdesk tickets. This integration
facilitates tracking vehicle-related issues, maintenance requests, and support
tickets in a unified system.

**Module Technical Name:** ``fleet_helpdesk``

**Version:** 18.0.1.0.0

**License:** AGPL-3

Features
========

* **Vehicle-Ticket Linking**: Associate helpdesk tickets with specific fleet vehicles
* **Smart Button on Vehicle Form**: View all tickets related to a vehicle with a single click
* **Ticket Count Display**: See the number of open/closed tickets for each vehicle
* **Quick Navigation**: Direct access from vehicle records to their related tickets
* **Bidirectional Relationship**: Navigate from vehicles to tickets and vice versa
* **Security Groups**: Proper access control based on fleet and helpdesk user groups

Installation
============

Prerequisites
-------------

This module requires the following Odoo modules to be installed:

* ``fleet`` - Fleet Management (Odoo Community)
* ``helpdesk`` - Helpdesk (Odoo Enterprise)

Installation Steps
------------------

1. Copy the ``fleet_helpdesk`` module to your Odoo addons directory:
   
   * Recommended location: ``odoo/src/private-addons/fleet_helpdesk``

2. Update the addons list:
   
   * Navigate to **Apps** menu
   * Click on **Update Apps List**
   * Search for "Fleet Helpdesk"

3. Install the module:
   
   * Click on the **Install** button

Configuration
=============

No additional configuration is required after installation. The module works
out of the box once installed.

User Access
-----------

* **Helpdesk Users**: Can see the tickets smart button on vehicle forms
* **Fleet Users**: Can see the vehicle field on helpdesk ticket forms

To grant access:

1. Navigate to **Settings > Users & Companies > Users**
2. Select a user
3. Grant appropriate groups:
   
   * **Fleet / User** - For fleet management access
   * **Helpdesk / Helpdesk User** - For helpdesk access

Usage
=====

Linking a Vehicle to a Ticket
------------------------------

1. Open a helpdesk ticket:
   
   * Navigate to **Helpdesk > Tickets**
   * Open an existing ticket or create a new one

2. Select a vehicle:
   
   * Find the **Vehicle** field (below email_cc field)
   * Select the appropriate vehicle from the dropdown

3. Save the ticket

Viewing Tickets from a Vehicle
-------------------------------

1. Open a fleet vehicle:
   
   * Navigate to **Fleet > Fleet > Vehicles**
   * Open a vehicle record

2. Click the **Tickets** smart button:
   
   * Located in the button box at the top of the form
   * Shows the total count of tickets for this vehicle

3. The ticket list view will open, filtered to show only tickets for this vehicle

Creating a New Ticket from a Vehicle
-------------------------------------

1. Open a fleet vehicle
2. Click the **Tickets** smart button
3. Click **Create** to add a new ticket
4. The vehicle will be automatically pre-selected

Technical Details
=================

Models Extended
---------------

**fleet.vehicle**

* **New Fields:**
  
  * ``helpdesk_ticket_ids`` (One2many): List of related helpdesk tickets
  * ``ticket_count`` (Integer, Computed): Count of tickets for the vehicle

* **New Methods:**
  
  * ``_compute_ticket_count()``: Computes the number of tickets
  * ``open_fleet_helpdesk()``: Opens the ticket list view filtered by vehicle

**helpdesk.ticket**

* **New Fields:**
  
  * ``vehicle_id`` (Many2one): Link to the fleet vehicle

Views Modified
--------------

* **fleet.vehicle form view**: Added smart button for tickets
* **helpdesk.ticket form view**: Added vehicle selection field

Security
--------

* View inheritance uses proper security groups
* Fleet users can access vehicle fields on tickets
* Helpdesk users can access ticket information on vehicles

Known Issues / Roadmap
======================

Known Issues
------------

* None at this time

Roadmap
-------

Potential future enhancements:

* Add vehicle information to ticket tree view
* Create report showing tickets by vehicle
* Add filters for vehicle-related tickets in helpdesk views
* Email notifications when tickets are linked to vehicles

Bug Tracker
===========

Bugs are tracked on GitHub Issues. In case of trouble, please check there
if your issue has already been reported.

Credits
=======

Authors
-------

* Open Source Integrators

Contributors
------------

* Open Source Integrators <https://www.opensourceintegrators.com>

Maintainers
-----------

This module is maintained by Open Source Integrators.

.. image:: https://www.opensourceintegrators.com/logo.png
   :alt: Open Source Integrators
   :target: https://www.opensourceintegrators.com

This module is part of the OCA project. OCA, or the Odoo Community Association,
is a nonprofit organization whose mission is to support the collaborative
development of Odoo features and promote its widespread use.
