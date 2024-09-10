# Import necessary Odoo libraries
from odoo import Command, api, fields, models


class SaleOrderTemplateLine(models.Model):
    """
    Extends the Sale Order Template Line to add new fields and methods
    for handling product configuration.
    """

    _inherit = "sale.order.template.line"

    # COLUMNS #####

    # Define a one-to-many relationship with product configuration session custom values
    custom_value_ids = fields.One2many(
        comodel_name="product.config.session.custom.value",
        inverse_name="cfg_session_id",
        related="config_session_id.custom_value_ids",
        string="Configurator Custom Values",
    )

    # Related field to check if the product is configurable
    config_ok = fields.Boolean(
        related="product_id.config_ok", string="Configurable", readonly=True
    )

    # Define a many-to-one relationship with the product configuration session
    config_session_id = fields.Many2one(
        comodel_name="product.config.session", string="Config Session"
    )

    # Define a many-to-one relationship with the Bill of Materials (BoM)
    bom_id = fields.Many2one(
         comodel_name="mrp.bom",
        string="BoM",
        readonly=True,
    )

    # END #########

    # METHODS ##########

    def reconfigure_product(self):
        """
        Creates and launches a product configurator wizard with a linked
        template and variant in order to reconfigure an existing product.
        This method serves as a shortcut to pre-fill configuration data
        for a variant.
        """

        # Define the model for the configurator wizard
        wizard_model = "product.configurator.sale.order.temp"

        # Prepare additional values for the configurator wizard
        extra_vals = {
            "order_id": self.sale_order_template_id.id,
            "order_line_id": self.id,
            "product_id": self.product_id.id,
        }

        # Set the context with default order and order line IDs
        self = self.with_context(
            default_order_id=self.sale_order_template_id.id,
            default_order_line_id=self.id,
        )

        # Create and return the configurator wizard
        return self.product_id.product_tmpl_id.create_config_wizard(
            model_name=wizard_model, extra_vals=extra_vals
        )

    @api.depends("product_id")
    def _compute_name(self):
        """
        Compute the name field for the sale order template line.
        The name is generated based on the custom values or the
        product description if no custom values are present.
        """

        for line in self:

            name = ""  # Initialize the name variable

            # Fetch the custom values for the line
            custom_values = line.custom_value_ids

            # If custom values are present, include them in the name
            if custom_values:
                name += "\n" + "\n".join(
                    [f"{cv.display_name}: {cv.value}" for cv in custom_values]
                )

            # If no custom values, use the product description
            else:
                if not line.product_id:
                    continue  # Skip if no product is linked
                name = self.product_id.get_product_multiline_description_sale()

            # Assign the computed name to the line
            line.name = name

    def _prepare_order_line_values(self):
        """
        Prepare the values for creating or updating a sale order line
        from the sale order template line. This includes custom values,
        configuration status, and the Bill of Materials (BoM).
        """

        # Call the superclass method to get the base values
        values = super()._prepare_order_line_values()

        # Update the values with additional fields specific to the configuration
        values.update(
            {
                "config_ok": self.config_ok,
                "config_session_id": self.config_session_id.id,
                "custom_value_ids": [Command.set(self.custom_value_ids.ids)],
                "bom_id": self.bom_id.id,
            }
        )

        # Return the prepared values
        return values

    # END ##########
