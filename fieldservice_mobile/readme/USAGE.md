1. Open the **Field Service** application.
2. Under **Configuration**, open **FSM Mobile Features**.
3. Select installed modules and feature lines for the mobile menu.
4. Assign security groups to control which features each user can access.
5. Activate the desired feature mapping record.

Portal users can access allowed features and attachments according to the configured
security rules and settings for stock move visibility and updates.

## Mobile sync API

Authenticated mobile sessions (portal or internal workers linked to an `fsm.person` via
`partner_id`) can call:

### Batch sync — `POST /fsm/sync` (`type=jsonrpc`)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "order_id": 12,
    "order": {"stage_id": 5, "resolution": "Done"},
    "clocks": [
      {
        "stage_id": 6,
        "start_datetime": "2026-07-24 15:00:00",
        "duration": 0.5,
        "total_duration": 1.0
      }
    ],
    "signature": {
      "signed_by": "Jane Doe",
      "signature": "<base64 png>"
    }
  }
}
```

Use `"mutations": [ {...}, {...} ]` to push several orders in the same request /
transaction.

### Photo upload — `POST /fsm/photo` (`multipart/form-data`)

Fields: `order_id`, optional `name`, and a file field named `ufile`, `file`, `photo` or
`attachment`.

### Delta pull — `POST /fsm/pull` (`type=jsonrpc`)

```json
{
  "params": {
    "since": "2026-07-24 00:00:00",
    "limit": 80,
    "offset": 0
  }
}
```

Returns only orders where the current user's `fsm.person` is `person_id` or in
`person_ids`, optionally filtered with `write_date > since`.
