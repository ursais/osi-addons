========================
PLM Tier Validation
========================

This module extends the functionality of PLM Engineering Change Orders (ECO) to support a
tier validation process.

**Table of contents**

.. contents::
   :local:

Installation
============

This module depends on ``base_tier_validation``. You can find it at
`OCA/server-ux <https://github.com/OCA/server-ux>`__

Configuration
=============

To configure this module, you need to:

1. Go to *Settings > Technical > Tier Validations > Tier Definition*.
2. Create as many tiers as you want for PLM ECO model.
3. Set the 'state' on the ECO stages as tier validation is only checked on state changes. (eg. in progress -> approved)

Usage
=====

To use this module, you need to:

1. Create a ECO triggering at least one "Tier Definition".
2. Click on *Request Validation* button.
3. Under the tab *Reviews* have a look to pending reviews and their
   statuses.
4. Once all reviews are validated click on *Confirm Order*.

Additional features:

-  You can filter the ECOs requesting your review through the filter
   *Needs my Review*.
-  User with rights to confirm the ECO (validate all tiers that would be
   generated) can directly do the operation, this is, there is no need
   for her/him to request a validation.
