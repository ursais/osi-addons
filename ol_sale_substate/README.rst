=====================
Onlogic Sale Substate
=====================

This module extends the functionality of the OCA `sale_substate` module by introducing additional substates for Sales Orders, along with automated logic to update substates based on order progress.

It enhances Sales Order tracking by providing more granular status visibility throughout the order lifecycle—from quotation to invoicing and payment.

Features
--------

New Substates
~~~~~~~~~~~~~

This module adds the following `base.substate` records to represent key moments in the sales process:

1. **Quotation Sent**
   Indicates the quotation has been sent to the customer.

2. **Order Review**
   The order has been sent but contains one or more active exceptions. It awaits review before confirmation.

3. **Waiting**
   The order has been confirmed and is awaiting production (planned MOs are still in draft).

4. **In Production**
   One or more manufacturing orders have started production.

5. **Partially Invoiced**
   The order is confirmed and some, but not all, order lines are invoiced.

6. **Invoiced**
   All order lines are invoiced.

7. **Complete**
   The order is fully invoiced **and** fully paid.

Automated Substate Updates
~~~~~~~~~~~~~~~~~~~~~~~~~~

Automated actions update the substate field (`substate_id`) on the Sales Order based on key changes:

- **Quotation Sent**
  Triggered when the Sales Order `state` is set to `'sent'`.

- **Order Review**
  Triggered when the order is in state `'sent'` and has an active exception.

- **Waiting**
  Triggered when the order is confirmed (`state = 'sale'`), but production has not started (MOs are still in draft).

- **In Production**
  Triggered when the order is confirmed and at least one MO is in progress.

- **Partially Invoiced**
  Triggered when at least one invoice exists, and not all lines are invoiced.

- **Invoiced**
  Triggered when all lines are fully invoiced.

- **Complete**
  Triggered when the order is fully invoiced and all related invoices are fully paid.

Each automated rule checks for exceptions and exemption codes to avoid interfering with orders intentionally exempt from such logic.

Usage
-----

Once installed, substates will appear on Sales Orders and transition automatically as the order progresses through quotation, confirmation, production, and invoicing stages. No manual configuration is necessary beyond standard use of sales and manufacturing flows.

Substates can be used in reporting, custom views, and dashboards to provide detailed visibility into the order pipeline.
