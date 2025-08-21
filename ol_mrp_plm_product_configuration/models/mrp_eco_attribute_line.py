# Import Odoo libs
from odoo import api, fields, models


class MrpEcoAttributeLine(models.Model):
    """
    Staging models (live only on ECO).
    They DO NOT affect product until Apply.
    """

    _name = "mrp.eco.attribute.line"
    _description = "ECO Staged Attribute Line"
    _order = "sequence, id"

    # COLUMNS #####

    eco_id = fields.Many2one(
        comodel_name="mrp.eco",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    attribute_id = fields.Many2one(
        comodel_name="product.attribute",
        required=True,
    )
    value_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="eco_attr_line_value_rel",
        column1="line_id",
        column2="value_id",
        string="Values",
        domain="[('attribute_id', '=', attribute_id)]",
        required=True,
    )
    min_qty = fields.Integer(
        string="Min Qty",
        default=0,
    )
    max_qty = fields.Integer(
        string="Max Qty",
        default=0,
    )
    required = fields.Boolean(string="Required")
    multi = fields.Boolean(string="Multi")
    used_in_sale_description = fields.Boolean(string="Show in Sale Description")
    is_qty_required = fields.Boolean(string="Qty Required")
    default_val = fields.Many2one(
        comodel_name="product.attribute.value",
        company_dependent=True,
    )

    # END #########
    # METHODS #####

    @api.onchange("value_ids")
    def _onchange_value_ids_clear_current_company_default(self):
        """Clear default_val for the current company if removed from value_ids."""
        for line in self:
            if line.default_val and line.default_val.id not in line.value_ids.ids:
                line.default_val = False

    def write(self, vals):
        """Clear removed defaults and auto-set remaining value if required=True."""
        res = super().write(vals)

        for line in self:
            allowed_val_ids = set(line.value_ids.ids)

            # Clear all removed defaults in ir.property
            props = (
                self.env["ir.property"]
                .sudo()
                .search(
                    [
                        ("name", "=", "default_val"),
                        ("res_id", "=", f"{line._name},{line.id}"),
                    ]
                )
            )
            for prop in props:
                if (
                    not prop.value_reference
                    or int(prop.value_reference.split(",")[1]) not in allowed_val_ids
                ):
                    prop.unlink()

            # Auto-set remaining value if required and only one value left
            if line.required and len(allowed_val_ids) == 1:
                remaining_val_id = next(iter(allowed_val_ids))

                # Update current company field for UI
                if not line.default_val or line.default_val.id != remaining_val_id:
                    line.default_val = remaining_val_id

                # Create ir.property for all companies that don't have one
                existing_props = (
                    self.env["ir.property"]
                    .sudo()
                    .search(
                        [
                            ("name", "=", "default_val"),
                            ("res_id", "=", f"{line._name},{line.id}"),
                        ]
                    )
                )
                existing_company_ids = {
                    p.company_id.id for p in existing_props if p.company_id
                }
                all_companies = self.env["res.company"].sudo().search([])

                # Get the fields_id for default_val
                field = (
                    self.env["ir.model.fields"]
                    .sudo()
                    .search(
                        [
                            ("model", "=", line._name),
                            ("name", "=", "default_val"),
                        ],
                        limit=1,
                    )
                )
                if not field:
                    continue  # safety, should never happen

                for company in all_companies:
                    if company.id not in existing_company_ids:
                        self.env["ir.property"].sudo().create(
                            {
                                "name": "default_val",
                                "fields_id": field.id,
                                "company_id": company.id,
                                "value_reference": f"product.attribute.value,{remaining_val_id}",
                                "res_id": f"{line._name},{line.id}",
                            }
                        )

        return res

    # END #########
