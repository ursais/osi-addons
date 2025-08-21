# Import Odoo libs
from odoo import api, fields, models


class MrpEco(models.Model):
    """
    Extend ECO to allow staging of attributes/values for configurable products.
    """

    _inherit = "mrp.eco"

    # COLUMNS ####

    show_staged_configuration = fields.Boolean(
        compute="_compute_show_staged_configuration",
    )
    rebuild_scaffold_bom = fields.Boolean(
        string="Rebuild Scaffold BoM",
        default=True,
    )
    staged_attribute_line_ids = fields.One2many(
        "mrp.eco.attribute.line", "eco_id", string="Staged Attributes"
    )

    # END #########
    # METHODS #####

    @api.depends(
        "type_id",
        "type_id.enable_staged_configuration",
    )
    def _compute_show_staged_configuration(self):
        for eco in self:
            eco.show_staged_configuration = bool(
                eco.type_id and eco.type_id.enable_staged_configuration
            )

    # -------------------------------------------------------------------------
    # Lifecycle overrides
    # -------------------------------------------------------------------------
    def action_new_revision(self):
        """On ECO revision, snapshot product's attributes into staging."""
        res = super().action_new_revision()
        for eco in self:
            if not eco.show_staged_configuration:
                continue
            if eco.staged_attribute_line_ids:
                continue
            eco._populate_staged_configuration_from_product()
        return res

    def action_apply(self):
        """Apply staged configuration back to product, with chatter logs."""
        res = super().action_apply()
        for eco in self:
            if not eco.show_staged_configuration or not eco.product_tmpl_id:
                continue

            # Update the product with the changes that were staged.
            eco._apply_staged_configuration_to_product()

            # Handle the BoM's by creating the new BoM from scaffold and link to ECO
            if eco.rebuild_scaffold_bom and eco.product_tmpl_id:
                # Run scaffold method (it will create its own new BoM)
                eco.product_tmpl_id.action_create_rebuild_scaffolding_bom()

                # Now fetch the latest scaffold BoM (highest version, still active)
                scaffold_bom = self.env["mrp.bom"].search(
                    [
                        ("product_tmpl_id", "=", eco.product_tmpl_id.id),
                        ("scaffolding_bom", "=", True),
                        ("active", "=", True),
                    ],
                    order="version desc",
                    limit=1,
                )

                if scaffold_bom:
                    # Archive the BoM that super() created if it's different
                    if eco.new_bom_id and eco.new_bom_id != scaffold_bom:
                        eco.new_bom_id.write({"active": False})
                        # Keep version continuity
                        scaffold_bom.version = eco.new_bom_id.version

                    # Delete the temp ECO BoM
                    eco.new_bom_id.unlink()

                    # Replace ECO’s new BoM with scaffold one
                    eco.new_bom_id = scaffold_bom

                # Now that new scaffold BoM created, update variant BoM's
                eco.product_tmpl_id._reset_all_variants_bom_with_scaffold_bom()

        return res

    # -------------------------------------------------------------------------
    # Snapshot helpers
    # -------------------------------------------------------------------------
    def _populate_staged_configuration_from_product(self):
        """
        Clone product.template's attribute lines into ECO staging.
        min_qty/max_qty = min/max across all PTAVs of that line.
        """
        self.ensure_one()
        product = self.product_tmpl_id
        if not product:
            return

        staged_lines = []
        for ptal in product.attribute_line_ids:
            value_ids = ptal.value_ids.ids
            min_qtys, max_qtys = [], []
            for ptav in ptal.product_template_value_ids:
                min_qtys.append(ptav.default_qty)
                max_qtys.append(ptav.maximum_qty)
            staged_lines.append(
                (
                    0,
                    0,
                    {
                        "attribute_id": ptal.attribute_id.id,
                        "value_ids": [(6, 0, value_ids)],
                        "min_qty": min(min_qtys) if min_qtys else 0,
                        "max_qty": max(max_qtys) if max_qtys else 0,
                        "default_val": getattr(ptal, "default_val", False)
                        and ptal.default_val.id
                        or False,
                        "required": getattr(ptal, "required", False),
                        "multi": getattr(
                            ptal, "multi", ptal.attribute_id.create_variant != "no"
                        ),
                        "used_in_sale_description": getattr(
                            ptal, "used_in_sale_description", False
                        ),
                        "is_qty_required": getattr(ptal, "is_qty_required", False),
                    },
                )
            )
        self.write({"staged_attribute_line_ids": staged_lines})

    # -------------------------------------------------------------------------
    # Apply staged -> product with diff
    # -------------------------------------------------------------------------
    def _ptal_state(self, ptal):
        return {
            "attribute_id": ptal.attribute_id.id,
            "attribute_name": ptal.attribute_id.display_name,
            "value_ids": set(ptal.value_ids.ids),
            "required": getattr(ptal, "required", False),
            "multi": getattr(ptal, "multi", None),
            "used_in_sale_description": getattr(
                ptal, "used_in_sale_description", False
            ),
            "is_qty_required": getattr(ptal, "is_qty_required", False),
            "default_val": getattr(ptal, "default_val", False)
            and ptal.default_val.id
            or False,
        }

    def _sline_state(self, sline):
        return {
            "attribute_id": sline.attribute_id.id,
            "attribute_name": sline.attribute_id.display_name,
            "value_ids": set(sline.value_ids.ids),
            "min_qty": sline.min_qty,
            "max_qty": sline.max_qty,
            "required": sline.required,
            "multi": sline.multi,
            "used_in_sale_description": sline.used_in_sale_description,
            "is_qty_required": sline.is_qty_required,
            "default_val": sline.default_val.id if sline.default_val else False,
        }

    def _compute_configuration_diff(self, product, staged_lines):
        ptal_by_attr = {l.attribute_id.id: l for l in product.attribute_line_ids}
        staged_by_attr = {l.attribute_id.id: l for l in staged_lines}
        adds, removes, updates = [], [], []

        for attr_id, ptal in ptal_by_attr.items():
            if attr_id not in staged_by_attr:
                removes.append({"ptal": ptal, "old": self._ptal_state(ptal)})

        for attr_id, sline in staged_by_attr.items():
            s_state = self._sline_state(sline)
            ptal = ptal_by_attr.get(attr_id)
            if not ptal:
                adds.append({"sline": sline, "new": s_state})
                continue
            p_state = self._ptal_state(ptal)
            changes = {}
            for fname in [
                "required",
                "multi",
                "used_in_sale_description",
                "is_qty_required",
                "default_val",
            ]:
                if p_state.get(fname) != s_state.get(fname):
                    changes[fname] = (p_state.get(fname), s_state.get(fname))
            vals_added = sorted(s_state["value_ids"] - p_state["value_ids"])
            vals_removed = sorted(p_state["value_ids"] - s_state["value_ids"])
            qty_changed = False
            if s_state["is_qty_required"]:
                for ptav in ptal.product_template_value_ids:
                    if (
                        ptav.default_qty != s_state["min_qty"]
                        or ptav.maximum_qty != s_state["max_qty"]
                    ):
                        qty_changed = True
                        break

            if changes or vals_added or vals_removed or qty_changed:
                updates.append(
                    {
                        "ptal": ptal,
                        "sline": sline,
                        "changes": changes,
                        "vals_added": vals_added,
                        "vals_removed": vals_removed,
                        "qty_changed": qty_changed,  # pass through for rendering
                    }
                )
        return {"adds": adds, "removes": removes, "updates": updates}

    def _render_change_summary_html(self, diff):
        def badge(txt):
            return f"<span style='padding:1px 6px;border:1px solid #ccc;margin-left:6px'>{txt}</span>"

        def format_val(fname, val):
            """Pretty print field values."""
            if fname == "default_val":
                return (
                    val
                    and self.env["product.attribute.value"].browse(val).display_name
                    or "—"
                )
            if isinstance(val, bool):
                return "Yes" if val else "No"
            return val or "—"

        parts = []
        if diff["adds"]:
            parts.append("<strong>Attributes Added</strong><ul>")
            for it in diff["adds"]:
                vals = ", ".join(it["sline"].value_ids.mapped("display_name"))
                parts.append(
                    f"<li>{it['sline'].attribute_id.display_name}{badge('added')} — {vals}</li>"
                )
            parts.append("</ul>")

        if diff["updates"]:
            parts.append("<strong>Attributes Updated</strong><ul>")
            for it in diff["updates"]:
                bullets = []
                if it["vals_added"]:
                    bullets.append(
                        "Values added: %s"
                        % ", ".join(
                            self.env["product.attribute.value"]
                            .browse(it["vals_added"])
                            .mapped("display_name")
                        )
                    )
                if it["vals_removed"]:
                    bullets.append(
                        "Values removed: %s"
                        % ", ".join(
                            self.env["product.attribute.value"]
                            .browse(it["vals_removed"])
                            .mapped("display_name")
                        )
                    )
                # Field changes
                for fname, (old, new) in it["changes"].items():
                    label = (
                        it["ptal"]._fields[fname].string
                        if fname in it["ptal"]._fields
                        else fname
                    )
                    if fname == "default_val":
                        label = f"{label} ({self.env.company.display_name})"
                    bullets.append(
                        f"{label}: {format_val(fname, old)} → {format_val(fname, new)}"
                    )
                # Qty changes (only if actually changed)
                if it.get("qty_changed"):
                    bullets.append(
                        f"Qty Required → PTAVs updated with Min={it['sline'].min_qty}, Max={it['sline'].max_qty}"
                    )

                parts.append(
                    f"<li>{it['sline'].attribute_id.display_name}{badge('changed')}<ul>"
                    + "".join(f"<li>{b}</li>" for b in bullets)
                    + "</ul></li>"
                )
            parts.append("</ul>")

        if diff["removes"]:
            parts.append("<strong>Attributes Removed</strong><ul>")
            for it in diff["removes"]:
                parts.append(
                    f"<li>{it['ptal'].attribute_id.display_name}{badge('removed')}</li>"
                )
            parts.append("</ul>")

        return "<div>" + "".join(parts or ["No changes detected."]) + "</div>"

    def _apply_staged_configuration_to_product(self):
        self.ensure_one()
        product = self.product_tmpl_id
        if not product:
            return
        diff = self._compute_configuration_diff(product, self.staged_attribute_line_ids)

        for it in diff["removes"]:
            ptal = it["ptal"]
            # Clear default_val first to satisfy constraint
            if "default_val" in ptal._fields and ptal.default_val:
                ptal.write({"default_val": False})
            ptal.unlink()

        for it in diff["adds"]:
            s = self._sline_state(it["sline"])
            create_vals = {
                "product_tmpl_id": product.id,
                "attribute_id": s["attribute_id"],
                "value_ids": [(6, 0, list(s["value_ids"]))],
            }
            self.env["product.template.attribute.line"].create(create_vals)

        for it in diff["updates"]:
            ptal, sline = it["ptal"], it["sline"]
            if it["vals_added"] or it["vals_removed"]:
                # Ensure default_val is valid
                if ptal.default_val and ptal.default_val.id not in sline.value_ids.ids:
                    ptal.write({"default_val": False})
                ptal.write({"value_ids": [(6, 0, list(sline.value_ids.ids))]})
            if it["changes"]:
                updates = {
                    fname: new
                    for fname, (_old, new) in it["changes"].items()
                    if fname in ptal._fields
                }
                if updates:
                    ptal.write(updates)
            if sline.is_qty_required:
                for ptav in ptal.product_template_value_ids:
                    vals = {}
                    if ptav.default_qty != sline.min_qty:
                        vals["default_qty"] = sline.min_qty
                    if ptav.maximum_qty != sline.max_qty:
                        vals["maximum_qty"] = sline.max_qty
                    if vals:
                        ptav.write(vals)

        if diff["adds"] or diff["updates"] or diff["removes"]:
            html = self._render_change_summary_html(diff)
            self.message_post(
                body=f"<p><strong>Product configuration updated</strong></p>{html}",
                body_is_html=True,
            )
            product.message_post(
                body=f"<p><strong>Updated via ECO {self.display_name}</strong></p>{html}",
                body_is_html=True,
            )

    # END #########
