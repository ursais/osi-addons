.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

========
Overview
========

This module simply reorder's BoM's to place non-variant BoM's below variants.
This is useful as many times Odoo's methods look at the first BoM it finds,
 so the variant specific BoM's sometimes get missed.

Configuration
=============

* None

Usage
=====

* Each time a BoM is created, it's sequence is set to make sure variant BoM's are listed first.

Credits
=======

Contributors
------------

* OSI Dev Team <contact@opensourceintegrators.com>
