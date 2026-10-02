To configure mobile stages:

- Go to **Field Service > Configuration > Stages**.
- Enable **Display in Mobile** for stages that should appear in the mobile app.
- Enable **Display in Odoo** for stages that should appear on FSM orders in Odoo.
- Assign a server action on stages that require automated updates.

To configure automated actions tied to stage sequences, adjust the domain on each
automation under **Settings > Technical > Automation > Automated Actions**.

To configure mobile features:

- Go to **Field Service > Configuration > FSM Mobile Features**.
- Select installed modules for the dynamic mobile menu.
- Activate a feature mapping record and assign security groups per feature line.

To allow a portal technician to use the mobile app:

- Create (or open) the portal user and add the **Field Service Mobile / Portal Worker**
  group (implies Portal).
- Link that user partner to an `fsm.person` worker.
- Assign orders to that worker (`person_id` / `person_ids`); record rules limit portal
  workers to their own orders.
- Default feature lines already include the portal worker group; adjust per-feature
  groups if you need a narrower mobile menu.

**Upgrade note:** FSM mobile ACLs are no longer granted to every Portal user. After
upgrading this module, assign **Portal Worker** to each technician who should keep using
the app; otherwise they lose access to orders, attachments, and sync APIs.
