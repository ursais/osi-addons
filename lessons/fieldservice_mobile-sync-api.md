# fieldservice_mobile sync API (19.0)

- Mobile app historically uses N JSON-RPC `write` / `create_fsm_attachment` calls.
- Backend endpoints live in `fieldservice_mobile/controllers/fsm_mobile_api.py`:
  - `/fsm/sync` (jsonrpc) — order + clocks (`fsm.stage.history`) + signature, one TX
  - `/fsm/photo` (http multipart) — creates `ir.attachment` from raw bytes
  - `/fsm/pull` (jsonrpc) — `write_date` delta scoped to technician `fsm.person`
- Technician link: `fsm.person.partner_id == res.users.partner_id` (same as Flutter
  `getPersonId()`).
- Business logic is on `fsm.order` (`fsm_order_mobile_sync.py`) so TransactionCase
  can cover it without HttpCase.
- Odoo 19 route type is `jsonrpc` (not legacy `json`).
