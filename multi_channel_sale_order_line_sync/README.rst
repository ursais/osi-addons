===================================
Multi-Channel Sale Order Line Sync
===================================

Appends newly-added channel line items onto already-confirmed Sales Orders
during multi-channel order import/update.

The problem
===========

The Webkul *Odoo Multi-Channel Sale* connector imports e-commerce orders into
Odoo through the ``order.feed`` model. When a third-party app (for example
*One Click Upsell* on Shopify) edits an order **after** it was first created,
the channel re-sends the order with one or more additional line items.

The connector re-evaluates the feed, but because the matching Odoo Sales Order
has already left the ``draft`` state, it only synchronises the order *state* and
logs::

    Only order state can be update as order not in draft state

The new line item is captured in the *Order Feed* but never reaches the Sales
Order, so the fulfilment team has to add it by hand.

What this module does
=====================

After the standard feed import runs, this module:

#. Locates the Sales Order linked to the feed.
#. If the order is **confirmed** (state ``sale``) and not locked, compares the
   feed's line items against the order's lines using a ``(product, quantity)``
   multiset so that legitimate duplicates are preserved.
#. Appends any genuinely-new line items to the confirmed order, preserving the
   channel-supplied (possibly discounted) unit price.
#. Posts a note in the order chatter listing what was added.

Draft/sent quotations are left untouched because the connector already handles
those natively. Locked orders are skipped (and logged) because Odoo forbids
editing them automatically.

It does **not** modify the third-party connector or any core Odoo module; it
extends ``order.feed`` through standard Odoo inheritance.

Usage
=====

* The fix runs automatically on every feed import.
* It can be triggered manually from the *Order Feeds* list/form via the
  **Action ▸ Sync Missing Lines to Sales Order** menu.
* An optional, disabled-by-default scheduled action
  (*Multi-Channel: Append Missing Lines to Confirmed Orders*) can be enabled as
  a safety net for feeds processed before this module was installed.

Configuration
=============

*Settings ▸ Multi-Channel Sync ▸ Append New Lines to Confirmed Orders*
(enabled by default) controls the behaviour globally.

Dependencies
============

* ``odoo_multi_channel_sale`` (Webkul) -- must be installed in the addons path.

Credits
=======

* Open Source Integrators
