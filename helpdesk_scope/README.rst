.. image:: https://img.shields.io/badge/licence-LGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
   :alt: License: LGPL-3

==============
Helpdesk Scope
==============

Odoo Helpdesk App provides 2 ways to categorize tickets: the type (question or issue) and tags. 
Tags are defined by the user and a ticket can have multiple tags. The SLA are related to the type of a ticket.

For some organizations, the type and its SLA depends on the scope of the ticket: for example a ticket related to an outage 
(type) needs to be solved within 2 days (SLA) if it impacts a single home (smaller scope) or 4 hours if it 
impacts a street (larger scope). The SLA differs based on the scope.

This module allows you to manage scopes and their types and SLA, as well as define the scope on the ticket. 

=====
Usage
=====


* Create a ticket
* Select the helpdesk team. The scope list will be filtered based on the team.
* Select the scope. The type will be filtered based on the scope.

=======
Credits
=======

* Steven Campbell <scampbell@opensourceintegrators.com>

Contributors
------------

* Open Source Integrators <contact@opensourceintegrators.com>
