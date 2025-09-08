from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductAttributeLine(models.Model):
    _inherit = "product.template.attribute.line"

    is_qty_required = fields.Boolean(string="Qty Required", copy=False)

    def write(self, values):
        """
        OVERRIDE:
        Handles enabling/disabling 'is_qty_required' on Product Template Attribute Line.
        - When enabled: Creates attribute value qty lines for each PTAV.
        - When disabled: Prevents disabling if variants exist; otherwise unlinks qty records.
        """
        result = super().write(values)
        is_qty_required = values.get("is_qty_required")

        if is_qty_required is None:
            return result  # No action needed if qty requirement not changed

        qty_vals = []

        for line in self:
            for ptav in line.product_template_value_ids:
                if is_qty_required and line.is_qty_required:
                    qty_list = ptav._get_attribute_value_qty_vals(
                        ptav.default_qty,
                        ptav.maximum_qty + 1,
                        ptav.product_attribute_value_id,
                        ptav
                    )
                    qty_vals.extend(qty_list or [])

                elif not is_qty_required and not line.is_qty_required:
                    if ptav.ptav_product_variant_ids:
                        raise ValidationError(_(
                            "Qty Required cannot be disabled because variants exist for '%s' - Attribute: %s."
                        ) % (line.product_tmpl_id.display_name, line.attribute_id.name))

                    ptav.attribute_value_qty_ids.unlink()

        if qty_vals:
            self.env["attribute.value.qty"].create(qty_vals)

        return result

    @api.onchange("is_qty_required", "multi", "custom")
    def onchange_is_qty_required(self):
        if self.is_qty_required and (self.multi or self.custom):
            self.is_qty_required = False


class ProductAttributePrice(models.Model):
    _inherit = "product.template.attribute.value"

    is_qty_required = fields.Boolean(
        related="attribute_line_id.is_qty_required",
        store=True,
        string="Qty Required",
        copy=False,
    )
    default_qty = fields.Integer("Minimum Quantity", default=1)
    maximum_qty = fields.Integer("Maximum Quantity", default=2)
    attribute_value_qty_ids = fields.One2many(
        "attribute.value.qty", "template_attri_value_id", string="Value Quantity"
    )

    @api.constrains("default_qty", "maximum_qty")
    def _check_default_qty_maximum_qty(self):
        for rec in self:
            if rec.default_qty > rec.maximum_qty:
                raise ValidationError(
                    _("Maximum Qty can't be smaller then Default Qty")
                )

    def _get_attribute_value_qty_vals(self, default_qty, maximum_qty, attr_value, template_attri_value_id):
        """
        Helper method to generate a list of quantity records based on the given range.
        Each quantity corresponds to a combination of product template and attribute value.
        """
        return [
            {
                "product_tmpl_id": self.product_tmpl_id.id,
                "product_attribute_id": self.attribute_id.id,
                "product_attribute_value_id": attr_value.id,
                "qty": qty,
                "template_attri_value_id": template_attri_value_id.id,
            }
            for qty in range(default_qty, maximum_qty)
        ]

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        qty_vals = []

        # Handle creation of quantity values if a new attribute value is added via the M2M bubble
        for res in results:
            attribute_line = res.attribute_line_id
            if not attribute_line.is_qty_required:
                continue  # Skip if qty is not required

            if attribute_line.is_qty_required:
                qty_list = res._get_attribute_value_qty_vals(
                    res.default_qty,
                    res.maximum_qty + 1,
                    res.product_attribute_value_id,
                    res
                )
                qty_vals.extend(qty_list or [])

        if qty_vals:
            self.env["attribute.value.qty"].create(qty_vals)

        return results



    def write(self, vals):
        """
        OVERRIDE:
        Handles Qty Increasing or Descareing in Product Template Attribute Value.
        Based on that it Will Update New Qty Id.
        """
        result = super().write(vals)

        # Only run if relevant fields are updated
        if 'default_qty' in vals or 'maximum_qty' in vals:
            attribute_value_qty = self.env["attribute.value.qty"]
            for record in self:
                if not record.is_qty_required:
                    continue  # Skip if qty is not required
                default_qty = vals.get('default_qty', record.default_qty)
                maximum_qty = vals.get('maximum_qty', record.maximum_qty)

                # Compute new range of qty values
                new_qty_range = set(range(default_qty, maximum_qty+1))
                existing_qty_lines = record.attribute_value_qty_ids

                # Extract existing qtys
                existing_qtys = set(existing_qty_lines.mapped('qty'))

                # Compute changes
                qtys_to_add = new_qty_range - existing_qtys
                qtys_to_remove = existing_qtys - new_qty_range
                print(qtys_to_add,qtys_to_remove,"////selffffffffff",self)
                if qtys_to_remove and self.ptav_product_variant_ids:
                    raise ValidationError(_(
                        "Qty cannot be removed because product variants exist for '%s' - Attribute: %s."
                    ) % (record.product_tmpl_id.display_name, record.attribute_id.name))

                if qtys_to_remove and not self.ptav_product_variant_ids:
                    qtys = record.attribute_value_qty_ids.filtered(lambda l:l.qty in list(qtys_to_remove))
                    qtys.unlink()
                # Add new records
                qty_vals = [
                    {
                        "product_tmpl_id": record.product_tmpl_id.id,
                        "product_attribute_id": record.attribute_id.id,
                        "product_attribute_value_id": record.product_attribute_value_id.id,
                        "qty": qty,
                        "template_attri_value_id": record.id,
                    }
                    for qty in qtys_to_add
                ]

                if qty_vals:
                    self.env["attribute.value.qty"].create(qty_vals)

        return result
