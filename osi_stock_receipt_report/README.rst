OSI Stock Receipt Report
========================

Customizes the **Picking Operations** report for incoming receipts
(``Ordre de réception``) to display purchase-related columns.

Changes applied to incoming receipt reports only:

* Document title prefixed with **Ordre de réception**.
* **Our Reference** – Internal product reference (``default_code``).
* **Supplier Designation** – Vendor product name from ``product.supplierinfo``.
* **Supplier Reference** – Vendor product code from ``product.supplierinfo``.
* **Ordered Qty** – Demand quantity from the stock move.
* **Received Qty** – Done/received quantity from the move line.
* **Our Lot** – Internal lot/serial number (standard Odoo tracking).
* **Supplier Lot** – New field on ``stock.move.line`` for the vendor's lot number.

Outgoing and internal transfer reports remain unchanged.

Configuration
-------------

No special configuration is required. Install the module and the report
will automatically apply to all incoming receipts.

The **Supplier Lot** field can be filled in on stock move lines during
receipt processing.

Dependencies
------------

* ``stock``
* ``purchase_stock``
