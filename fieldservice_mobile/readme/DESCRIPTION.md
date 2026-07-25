This module provides backend support for the Field Service mobile application. It
manages mobile-specific stage visibility, stage duration tracking, portal configuration,
dynamic feature mapping by security group, and payment link generation for field service
orders linked to sales orders.

It also exposes HTTP endpoints used by the offline-capable mobile client:

- `POST /fsm/sync` — apply order updates, clock punches (`fsm.stage.history`) and
  signature in a single atomic transaction
- `POST /fsm/photo` — multipart upload that creates `ir.attachment` without base64 RPC
- `POST /fsm/pull` — delta pull of orders assigned to the current technician
  (`person_id` / `person_ids`), filtered by `write_date`
