.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

========================
Helpdesk - Parent Ticket
========================

Odoo Helpdesk does not allow to relate tickets with each others.

Helpdesk teams need a way to track several individual issues under one parent
ticket. This type of ticket is usually created during troubleshooting when an
agent (Levels II and II) detects that the issue is further away from the
end-user who reported it and it is affecting or will potentially impact other
end-users or dependent products/services.

This module allows the helpdesk user to set a parent-children relationship
between helpdesk tickets.

Usage
=====

* Go to Helpdesk
* Create or select a ticket
* Set his parent
* Go to the parent to see all his children
* In the search view, use the Parents filter to get the list of tickets whose
  parent is not set. Use the Children one to get the ones whose parent is set.

Credits
=======

* Steve Campbell <scampbell@opensourceintegrators.com>


Contributors
------------

* Open Source Integrators <https://www.opensourceintegrators.com>
* Serpent Consulting Services Pvt. Ltd. <support@serpentcs.com>
