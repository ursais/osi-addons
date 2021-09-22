.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

======================
OSI EDI INFRASTRUCTURE
======================

This module will have basic infrastructure for EDI setup to process
a. EDI 850 (Purchase Order)
b. EDI 810 (Invoice)
c. EDI 856 (Advance Shipment Notice)

Configuration
=============
* Add permissions to administrator for EDI configuration
* Define EDI Provider
* Set the EDI Provider for use on the company record
* Define EDI Supported Document (mapping rules)
* Define EDI Partner code on customer, warehouse and route on customer
* Enable Cron for FTP and EDI Processors

Usage
=====

* CRON: Automated FTP and Processing
* Manual Upload: Perform Get Documents
* Manual Processing: Select multiple messages in queue and run
  Process EDI Documents from Action menu OR process each document

Credits
=======

* Open Source Integrators <http://www.opensourceintegrators.com>

Contributors
============

* Balaji Kannan <bkannan@opensourceintegrators.com>
* Daniel Reis <dreis@opensourceintegrators.com>
* Mayank Gosai <mgosai@opensourceintegrators.com>