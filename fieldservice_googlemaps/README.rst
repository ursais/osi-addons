.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
Field Service - Google Maps
===========================

This module adds address auto-completition to Field Service Locations.
It also adds logic to create and sync PostGIS geometries between 
FSM Locations and FSM Orders associated with that location.

Installation
============

To install Field Service and have the mapping features, you need to install GeoEngine.

Please refer to the installation instructions available at:
https://github.com/OCA/geospatial/tree/11.0/base_geoengine

Usage
=====

* Go to Field Service > Master Data > Locations
* Create a new location and start typing the address.
  The address will be auto-completed.
* Go to Field Service > Operations > Orders
* Edit an existing order to modify the location.
  The geometry of the order will be updated accordingly.

Credits
=======

* Michael Allen <mallen@opensourceintegrators.com>


Contributors
------------

* Open Source Integrators <http://www.opensourceintegrators.com>
