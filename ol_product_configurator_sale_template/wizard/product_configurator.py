# Import Odoo libs
from odoo import api, fields, models


class ProductConfiguratorSaleOrderTemplate(models.TransientModel):
    _name = "product.configurator.sale.order.temp"
    _inherit = "product.configurator"
    _description = "Product Configurator Sale Order Template"

    # COLUMNS #####

    # Reference to the related sale order template
    order_id = fields.Many2one(
        comodel_name="sale.order.template", required=True, readonly=True
    )
    # Reference to the related sale order template line
    order_line_id = fields.Many2one(
        comodel_name="sale.order.template.line", readonly=True
    )

    # Domain attributes for the product configurator
    domain_attr_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="domain_attrs_values_template_order_rel",
        column1="wiz_id",
        column2="attribute_id",
        string="Domain",
    )
    domain_attr_2_ids = fields.Many2many(
        comodel_name="product.attribute.value",
        relation="domain_attrs_2_values_template_order_rel",
        column1="wiz_id",
        column2="attribute_id",
        string="Domain",
    )

    # END #########

    # METHODS ##########

    def _get_order_line_vals(self, product_id):
        """Hook to allow custom line values to be added to newly
        created or edited lines."""

        # Fetch the product using the provided product_id
        product = self.env["product.product"].browse(product_id)

        # Prepare initial values for the order line
        line_vals = {
            "product_id": product_id,
            "sale_order_template_id": self.order_id.id,
            "product_uom_id": product.uom_id.id,
        }

        # List of fields that require onchange behavior
        onchange_fields = ["product_uom_id"]
        line = self.env["sale.order.template.line"].new(line_vals)

        # Trigger onchange and update line values accordingly
        for field in onchange_fields:
            line_vals.update(
                {field: line._fields[field].convert_to_write(line[field], line)}
            )

        # Update line values with session and product name
        line_vals.update(
            {
                "config_session_id": self.config_session_id.id,
                "name": product._get_mako_tmpl_name(),
            }
        )
        return line_vals

    def action_config_done(self):
        """Parse values and execute final code before closing the wizard"""

        # Call the superclass method and get the result
        res = super().action_config_done()

        # If the result model matches the current model, return the result
        if res.get("res_model") == self._name:
            return res

        model_name = "sale.order.template.line"  # Model for order template lines

        # Get the values for the order line using the custom method
        line_vals = self._get_order_line_vals(res["res_id"])

        # Call onchange explicitly as write and create do not trigger onchange automatically
        order_line_obj = self.env[model_name]
        cfg_session = self.config_session_id

        # Fetch the onchange specifications for the model
        fields_spec = cfg_session.get_onchange_specifications(model=model_name)

        # Filter fields that are relevant and not taxes_id
        fields_spec = {
            key: val
            for key, val in fields_spec.items()
            if key in list(line_vals.keys()) and key != "taxes_id"
        }

        # Apply onchange and get the updated values
        updates = order_line_obj.onchange(line_vals, ["product_id"], fields_spec)
        values = updates.get("value", {})

        # Process the values for writing
        values = cfg_session.get_vals_to_write(values=values, model=model_name)
        values.update(line_vals)

        # Write values to existing order line or create a new one
        if self.order_line_id:
            self.order_line_id.write(values)
        else:
            self.order_id.write({"sale_order_template_line_ids": [(0, 0, values)]})
        return

    @api.model_create_multi
    def create(self, vals_list):
        """Override the create method to handle custom value logic"""

        # Iterate over the values to be created
        for vals in vals_list:

            # Check if the default order line ID is present in the context
            if self.env.context.get("default_order_line_id", False):

                # Fetch the sale order line using the context value
                sale_line = self.env["sale.order.template.line"].browse(
                    self.env.context["default_order_line_id"]
                )

                # If custom values are present, add them to the vals
                if sale_line.custom_value_ids:
                    vals["custom_value_ids"] = self._get_custom_values(
                        sale_line.config_session_id
                    )

        # Call the superclass create method with updated values
        return super().create(vals_list)

    def _get_custom_values(self, session):
        """Retrieve custom values for a given session"""

        # Prepare custom values list with removal operation
        custom_values = [(5,)] + [
            (
                0,
                0,
                {
                    "attribute_id": value_custom.attribute_id.id,
                    "value": value_custom.value,
                    "attachment_ids": [
                        (4, attach.id) for attach in value_custom.attachment_ids
                    ],
                },
            )
            for value_custom in session.custom_value_ids
        ]
        return custom_values

    # END ##########
