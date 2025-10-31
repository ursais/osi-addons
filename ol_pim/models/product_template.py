# Import Odoo libs
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """
    Adding fields to product templates.
    """

    _inherit = "product.template"

    # COLUMNS ##########

    public_destination = fields.Selection(
        [
            ("not_public", "Not Public"),
            ("b2b", "B2B"),
            ("b2c", "B2C"),
            ("b2b_b2c", "B2B + B2C"),
        ],
        string="Public Destination",
        default="not_public",
    )

    # END ##########

    @api.model
    def _normalize_code(self, name):
        """Convert label to lowercase safe code."""
        return (name or "").strip().lower().replace(" ", "_").replace("-", "_")

    @api.model
    def _write_non_base_translations(self, record, field_name, translations):
        """Write translations for non-base languages and return base value."""
        base_val = None
        if not isinstance(translations, list):
            return None

        for entry in translations:
            locale = entry.get("locale")
            val = entry.get("value")
            if not locale or val is None:
                continue
            if locale == "en_US":
                base_val = val
            else:
                record.with_context(lang=locale).write({field_name: val})
        return base_val

    def action_populate_from_pim_latest_message(self):
        """Populate product attributes and fields from pim_latest_message JSON."""
        self.ensure_one()
        Attribute = self.env["attribute.attribute"]
        Option = self.env["attribute.option"]

        data = self.pim_latest_message
        # If no pim data then do nothing
        if not data:
            return

        # Handle stored as string
        if isinstance(data, str):
            try:
                data = eval(data)
            except Exception:
                self.message_post(
                    body=_(
                        "<b>PIM Import:</b> Invalid JSON format in pim_latest_message — skipping update."
                    ),
                    body_is_html=True,
                )
                data = {}

        EXCLUDED_FIELDS = {
            "type",
            "tracking",
            "categ_id",
            "default_code",
            "barcode",
            "sale_ok",
            "purchase_ok",
            "uom_id",
            "uom_po_id",
            "active",
            "system_tier",
        }

        log = []
        vals_to_write = {}

        # ============================================================
        # Process attributes
        # ============================================================
        for attr in Attribute.search([]):
            if not attr.code or attr.code in EXCLUDED_FIELDS:
                continue

            field_name = attr.field_id.name
            if not field_name or field_name not in self._fields:
                log.append(f"⚠️ Attribute '{attr.code}' missing or invalid field_id")
                continue

            if attr.code not in data:
                continue

            value = data[attr.code]
            field_def = self._fields[field_name]
            ftype = field_def.type

            # ----------------------------------------
            # CHAR / TEXT
            # ----------------------------------------
            if ftype in ("char", "text"):
                if isinstance(value, list):
                    base_val = self._write_non_base_translations(
                        self, field_name, value
                    )
                    if base_val is not None:
                        vals_to_write[field_name] = base_val
                elif isinstance(value, dict) and "value" in value:
                    vals_to_write[field_name] = value["value"]
                else:
                    vals_to_write[field_name] = str(value or "")

            # ----------------------------------------
            # MANY2ONE / MANY2MANY
            # ----------------------------------------
            elif ftype in ("many2one", "many2many"):
                labels = []

                # Case A: list of locale dicts (translations)
                if (
                    isinstance(value, list)
                    and value
                    and isinstance(value[0], dict)
                    and "locale" in value[0]
                ):
                    chosen_locale = None
                    for pref in ("en_US", "en_EU", "nl_NL"):
                        for v in value:
                            if v.get("locale") == pref:
                                chosen_locale = v
                                break
                        if chosen_locale:
                            break
                    if not chosen_locale:
                        chosen_locale = value[0]

                    if isinstance(chosen_locale.get("label"), list):
                        labels = chosen_locale["label"]
                    elif isinstance(chosen_locale.get("label"), str):
                        labels = [chosen_locale["label"]]
                    elif isinstance(chosen_locale.get("value"), list):
                        labels = chosen_locale["value"]

                # Case B: list of dicts
                elif isinstance(value, list) and all(
                    isinstance(v, dict) for v in value
                ):
                    for v in value:
                        lbl = v.get("label") or v.get("value")
                        if lbl:
                            labels.append(lbl)

                # Case C: single dict or string
                elif isinstance(value, dict):
                    lbl = value.get("label") or value.get("value")
                    if lbl:
                        labels.append(lbl)
                elif isinstance(value, str):
                    labels = [value]

                labels = [l.strip() for l in labels if l]
                if not labels:
                    continue

                matched = []
                created = []

                for lbl in labels:
                    opt = attr.option_ids.filtered(
                        lambda o: (o.name or "").strip().lower() == lbl.lower()
                    )
                    if not opt:
                        new_opt = Option.create(
                            {
                                "name": lbl,
                                "code": self._normalize_code(lbl),
                                "attribute_id": attr.id,
                            }
                        )
                        created.append(lbl)
                        matched.append(new_opt.id)
                    else:
                        matched.append(opt.id)

                if created:
                    log.append(
                        f"🆕 Created new options for '{attr.code}': {', '.join(created)}"
                    )

                if not matched:
                    log.append(
                        f"⚠️ No matching options found for '{attr.code}' values: {labels}"
                    )
                    continue

                if ftype == "many2one":
                    vals_to_write[field_name] = matched[0]
                else:
                    vals_to_write[field_name] = [(6, 0, matched)]

        # ============================================================
        # Dynamic option translations
        # ============================================================
        for attr in Attribute.search([]):
            field_name = attr.field_id.name
            if not field_name or field_name not in self._fields:
                continue
            field_def = self._fields[field_name]
            if field_def.comodel_name != "attribute.option":
                continue

            json_data = data.get(attr.code)
            if not json_data:
                continue

            if isinstance(json_data, list):
                sorted_json = sorted(
                    json_data, key=lambda x: 1 if x.get("locale") == "en_US" else 0
                )
                for locale_entry in sorted_json:
                    locale = locale_entry.get("locale")
                    values = locale_entry.get("value", [])
                    labels = locale_entry.get("label", [])

                    if (
                        not locale
                        or not values
                        or not labels
                        or len(values) != len(labels)
                    ):
                        continue

                    for code, label in zip(values, labels):
                        if not code or not label:
                            continue
                        option = attr.option_ids.filtered(lambda o: o.code == code)
                        if not option:
                            continue
                        current_label = option.with_context(lang=locale).name
                        if current_label != label:
                            option.with_context(lang=locale).write({"name": label})

        # ============================================================
        # Process allow_backorder
        # ============================================================
        backorder_config = data.get("backorder_config")
        allow_backorder_val = None

        if backorder_config and isinstance(backorder_config, list):
            for company_entry in backorder_config:
                values_list = company_entry.get("value", [])
                for val_entry in values_list:
                    locale = val_entry.get("locale")
                    value_str = val_entry.get("value")
                    if not locale or value_str is None:
                        continue
                    if locale == "en_US":
                        allow_backorder_val = value_str
                        break
                if allow_backorder_val:
                    break

            if not allow_backorder_val:
                for company_entry in backorder_config:
                    values_list = company_entry.get("value", [])
                    for val_entry in values_list:
                        value_str = val_entry.get("value")
                        if value_str:
                            allow_backorder_val = value_str
                            break
                    if allow_backorder_val:
                        break

        if allow_backorder_val in ("notify", "no-notify"):
            allow_backorder_val_bool = True
        elif allow_backorder_val == "no-backorder":
            allow_backorder_val_bool = False
        else:
            allow_backorder_val_bool = True  # default

        if not self.allow_backorder:
            self.write({"allow_backorder": allow_backorder_val_bool})

        # ============================================================
        # Process public_destination
        # ============================================================
        public_dest_data = data.get("public_destination")
        if public_dest_data and isinstance(public_dest_data, dict):
            json_value = public_dest_data.get("value")
            selection = dict(self._fields["public_destination"].selection)
            if json_value and json_value in selection:
                if self.public_destination != json_value:
                    self.write({"public_destination": json_value})

        # ============================================================
        # Final write & log
        # ============================================================
        if vals_to_write:
            self.write(vals_to_write)
            log.insert(0, "✅ Attribute fields updated successfully.")
        else:
            log.insert(0, "ℹ️ No values were written to this product.")

        self.message_post(
            body="<b>PIM Import Log:</b><br/>%s" % "<br/>".join(log),
            body_is_html=True,
        )
