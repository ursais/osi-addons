================
Expense Extended
================

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-ursais%2Fosi--addons-lightgray.png?logo=github
    :target: https://github.com/ursais/osi-addons/tree/12.0/sale_subscription_brand
    :alt: ursais/osi-addons

|badge1| |badge2| |badge3|

This module ensures that the account on the expense matches the expense
account for the product. User can not approve own expense reports.

**Table of contents**

.. contents::
   :local:

Usage
=====

* Create an expense. The journal id should have moved to below the Company.
* Submit expense to manager and approve it.
* System will restrict to approve it, if expense requestor and expense manager
  are same.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/ursais/osi-addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/ursais/osi-addons/issues/new?body=module:%20expense_extended%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Roadmap
=======

* Find a better module name to explain how expenses are extended.

Credits
=======

Contributors
------------

* Open Source Integrators <https://www.opensourceintegrators.com>

  * Balaji Kannan <bkannan@opensourceintegrators.com>
  * Sudarshan Kadalazhi <skadalazhi@opensourceintegrators.com>
  * Bhavesh Odedra <bodedra@opensourceintegrators.com>
  * Sandip Mangukiya <smangukiya@opensourceintegrators.com>

Maintainers
-----------

This module is maintained by Open Source Integrators.

.. image:: https://github.com/ursais.png
   :target: https://www.opensourceintegrators.com
   :alt: Open Source Integrators

Open Source Integrators™ (OSI) provides customers a unique combination of
open source business process consulting and implementations.

.. |maintainer-b-kannan| image:: https://github.com/b-kannan.png?size=40px
    :target: https://github.com/b-kannan
    :alt: Balaji Kannan

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-b-kannan|

This module is part of the `OSI Odoo Addons <https://github.com/ursais/osi-addons>`_ project on GitHub.

You are welcome to contribute. To learn how, please visit https://odoo-community.org/page/Contribute.
