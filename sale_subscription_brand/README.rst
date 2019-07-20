=======================
Sale Subscription Brand
=======================

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

This module allows you to brand your subscription invoices based on the sales order.

**Table of contents**

.. contents::
   :local:

Configuration
=============

To configure this module, please refer to the documentation of
`partner_brand <https://github.com/OCA/partner-contact/blob/12.0/partner_brand/README.rst>`_.

Usage
=====

To use this module, you need to:

* Go to Sales > Quotations
* Create a quotation
* Select the brand
* Enter a subscription product in one of the line
* Print the PDF report. It uses the brand information: name, address, logo,
  phone, email, website instead of the company one.
* Confirm the quotation to generate the subscription
* Go to the subscription
* Generate the first invoice
* Go to the invoice
* Print the PDF report. It uses the brand information: name, address, logo,
  phone, email, website instead of the company one.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/ursais/osi-addons/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed
`feedback <https://github.com/ursais/osi-addons/issues/new?body=module:%20sale_subscription_brand%0Aversion:%2012.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Authors
~~~~~~~

* Open Source Integrators <https://www.opensourceintegrators.com>

Contributors
~~~~~~~~~~~~

* Raphael Lee <rlee@opensourceintegrators.com>
* Steve Campbell <scampbell@opensourceintegrators.com>
* Maxime Chambreuil <mchambreuil@opensourceintegrators.com>

Other credits
~~~~~~~~~~~~~

The development of this module has been financially supported by:

* Open Source Integrators <https://www.opensourceintegrators.com>

Maintainers
~~~~~~~~~~~

This module is maintained by Open Source Integrators.

.. image:: https://github.com/ursais.png
   :target: https://www.opensourceintegrators.com
   :alt: Open Source Integrators

Open Source Integrators™ (OSI) provides customers a unique combination of
open source business process consulting and implementations.

.. |maintainer-osi-scampbell| image:: https://github.com/osi-scampbell.png?size=40px
    :target: https://github.com/osi-scampbell
    :alt: Steve Campbell

Current `maintainer <https://odoo-community.org/page/maintainer-role>`__:

|maintainer-osi-scampbell|

This module is part of the `OSI Odoo Addons <https://github.com/ursais/osi-addons/tree/12.0/sale_subscription_brand>`_ project on GitHub.

You are welcome to contribute. To learn how, please visit https://odoo-community.org/page/Contribute.
