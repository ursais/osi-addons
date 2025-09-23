============================
Onlogic Partner Credit Limit
============================

This module extends **Sales**, **Stock**, and **Manufacturing** flows to add
**credit limit management** and ensure that customer orders are held or released
based on financial limits.

It integrates with Odoo’s **base_exception** framework to block or release
orders, pickings, and manufacturing orders depending on the credit status.

------------------
Main Features
------------------

* **Sales Orders**
  - Adds fields:
    - ``credit_hold`` – Boolean, indicates if the SO is blocked due to credit.
    - ``uninvoiced_balance`` – Amount not yet invoiced.
    - ``override_credit_limit_hold`` – Manual override flag to bypass credit check.
  - Blocks SOs when partner’s open orders + invoices exceed credit limit.
  - Supports **credit rollup** from child to parent partners.

* **Stock Pickings**
  - Propagates ``credit_hold`` from the related Sale Order.
  - If not on credit hold, automatically ignores exceptions (OCA base_exception).

* **Manufacturing Orders**
  - Propagates ``credit_hold`` from the related Sale Order.
  - If not on credit hold, automatically ignores exceptions.

* **Partners**
  - Supports ``partner_rollup_id`` to accumulate balances across entities.
  - Tracks:
    - Remaining Credit
    - Open SO Balance
    - Customer Deposit Balance

* **Blanket Orders**
  - Integrated with blanket order releases.
  - Sale Orders generated from Blanket Orders respect partner credit limits.

------------------
Technical Details
------------------

* Direct SQL updates are used for performance when setting
  ``ignore_exception`` on stock pickings and manufacturing orders.
* Integrates with OCA’s ``base_exception`` module for exception handling.
* Tests cover:
  - Partner rollup validation (no cycles allowed).
  - Sale → Picking flow under credit limits.
  - Manual override of credit holds.
  - Sale → Manufacturing flow (BOMs).
  - Blanket order release under credit rules.
  - Customer deposit balance from payments.

------------------
Configuration
------------------

1. Set a **Credit Limit** on a customer (via *Contacts*).
2. Optionally configure a **Partner Rollup** to roll balances up to a parent.
3. Create Sale Orders, Pickings, or MOs — the module will:
   - Put documents on **Credit Hold** if the limit is exceeded.
   - Allow override via ``Override Credit Limit Hold``.

------------------
Usage Example
------------------

* **Scenario**:  
  Customer has a credit limit of 400.  
  A new SO of 350 is confirmed.  
  - SO balance is 350 → remaining credit is 50.  
  - Picking and MO are allowed (no credit hold).  

* **Override**:  
  If an SO is flagged with ``Override Credit Limit Hold``,  
  it will bypass the credit hold regardless of the balance.

------------------
Dependencies
------------------

* Odoo Core: ``sale``, ``stock``, ``mrp``, ``account``
* OCA: ``base_exception`` (for exception handling)
