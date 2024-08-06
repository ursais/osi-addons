## Security

Go to Settings \> Users and assign the appropiate permissions to users.
Different security groups grant distinct levels of access to the RMA
features.

- Users in group "RMA Customer User" or "RMA Supplier User" can access
  to, create and process RMA's associated to customers or suppliers
  respectively.
- Users in group "RMA Manager" can access to, create, approve and
  process RMA's associated to both customers and suppliers.

## RMA Approval Policy

There are two RMA approval policies in product catogories:

- One step: Always auto-approve RMAs that only contain products within
  categories with this policy.
- Two steps: A RMA order containing a product within a category with
  this policy will request the RMA manager approval.

In order to change the approval policy of a product category follow the
next steps:

1.  Go to *Inventory \> Configuration \> Products \> Product
    Categories*.
2.  Select one and change the field *RMA Approval Policy* to your
    convenience.

## Other Settings

1.  Go to RMA \> Configuration \> Settings \> Return Merchandising
    Authorization and select the option "Display 3 fields on rma:
    partner, invoice address, delivery address" if needed.
2.  Go to RMA \> Configuration \> Warehouse management \> Warehouses and
    add a default RMA location and RMA picking type for customers and
    suppliers RMA picking type. In case the warehouse is configured to
    use routes, you need to create at least one route per rma type with
    at least two push rules (one for inbound another for outbound) it's
    very important to select the type of operation supplier if we are
    moving in the company and customer if we are moving out of the
    company.
