.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============================
PO Approval Process & Routings
==============================

PO Approval process that allows routing of POs for approval based on amount.
There are two types of parts inventory and non-inventory. These module will
restrict PO creator to approves own non inventory items. Based on approval and
co-approval amount and PO type, PO approval process will move forward and send
email to higher level appoval & co-approval based on configuration.

Configuration
=============

* Purchases > Configuration > Purchase Approvals
* Create purchase approvals 'Employee, PO Type, Approval amount, Co-Approval 
  amount' with 'Employee A, Inventory/Non-Iventory, 100.0, 500.0'
* Create purchase approvals 'Employee, PO Type, Approval amount, Co-Approval 
  amount' with 'Employee B, Inventory/Non-Iventory, 1000.0, 1500.0'

Usage
=====

* Go to Purchases > Purchase > Requests for Quotation
* Create a new one with amount 700.0.
* Users who have 'Approve Purchase Requests' access right, can validate request
* After validate request, PO will check approval configuration.
* As per our above configuration, it will send email to 'Employee B' for
  approve and co-approve.
* 'Employee B' will approve, co-approve and confirm it.

Credits
=======

* Bhavesh Odedra <bodedra@opensourceintegrators.com>

Contributors
------------

* Open Source Integrators <http://www.opensourceintegrators.com>
