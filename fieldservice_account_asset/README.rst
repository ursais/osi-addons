===================
Field Service Asset
===================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-ursais%2Fosi--addons-lightgray.png?logo=github
    :target: https://github.com/ursais/osi-addons/tree/12.0/sale_subscription_brand
    :alt: ursais/osi-addons

|badge1| |badge2| |badge3|

This module aims to link the FSM equipment with its accounting asset and allow tracking of its depreciation.

**Table of contents**

.. contents::
   :local:

Configuration
=============

Accounting
----------

* Go to Accounting > Configuration > Asset Types
* Create an asset type
* Go to Accounting > Customers > Products
* Create or select a product
* In the Accounting tab, set the the asset type

Inventory
---------

* Go to Inventory > Configuration > Warehouse Management > Locations
* Remove the filter to search for "Asset Location"
* Open the location and set the accounting information:

  * Stock Valuation Account (Incoming): Same account as the asset account on the asset type
  * Stock Valuation Account (Outgoing): Same account as the expense account on the asset type

Field Service
-------------

* Go to Field Service > Configuration > Settings
* Set the Asset Location
* Go to Field Service > Configuration > Stages
* Open the stages related to Equipment
* Select a stage where the asset is created by selecting "Creation" in "Asset Action"
* Select a stage where the asset is recovered/disposed by selecting "Recovery" in "Asset Action"

Usage
=====

* Go to Field Service > Master Data > Equipments
* Create an equipment and select a product with the asset type
* Move the stage to create the asset:

  * a new asset is created based on the information from the category and the product
  * the equipment is moved from its current location to the asset location

* Move the stage to recover the asset:

  * its related asset is disposed
  * the equipment is moved from the asset location to where it was when the asset was created

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/ursais/osi-addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/ursais/osi-addons/issues/new?body=module:%20fieldservice_account_asset%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Roadmap
=======

* The current version of the module stores all assets in one location per company.
  Future versions will allow to define the inventory location on the asset type.
  If you are interested to sponsor this feature, please create an issue on the
  `GitHub project <https://github.com/ursais/osi-addons/issues>`_.

Credits
=======

Contributors
------------

* `Open Source Integrators <https://www.opensourceintegrators.com>`_:

  * Maxime Chambreuil <mchambreuil@opensourceintegrators.com>

* `Serpent Consulting Services <https://www.serpentcs.com>`_:

  * Murtuza Saleh <murtuzasaleh@serpentcs.com>

Maintainers
-----------

This module is maintained by Open Source Integrators.

.. image:: https://github.com/ursais.png
   :target: https://www.opensourceintegrators.com
   :alt: Open Source Integrators

Open Source Integrators™ (OSI) provides customers a unique combination of
open source business process consulting and implementations.

.. |maintainer-max3903| image:: https://github.com/max3903.png?size=40px
    :target: https://github.com/max3903
    :alt: Maxime Chambreuil

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-max3903|

This module is part of the `OSI Odoo Addons <https://github.com/ursais/osi-addons/tree/12.0/fieldservice_account_asset>`_ project on GitHub.

You are welcome to contribute. To learn how, please visit https://odoo-community.org/page/Contribute.
