# Import Odoo libs
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConstrainedSkuSearchWizard(models.TransientModel):
    """
    Wizard to find sale order by name or serial number
    """

    _name = "constrained.sku.search.wizard"
    _description = "Constrained SKU Search Wizard"

    # COLUMNS #####

    type = fields.Selection(
        [("search", "Search"), ("list", "List")],
        string="Type",
        default="list",
        help="Defines how the related records are added",
    )
    sale_order_ids = fields.Many2many(
        string="Sale Orders",
        comodel_name="sale.order",
        relation="constrained_sku_wizard_sale_orders_rel",
        column1="wizard_id",
        column2="sale_order_id",
    )
    picking_ids = fields.Many2many(
        string="Transfers",
        comodel_name="stock.picking",
        relation="constrained_sku_wizard_stock_pickings_rel",
        column1="wizard_id",
        column2="stock_picking_id",
    )
    sale_order_list = fields.Text(
        string="Sale Order Names", help="Comma separated list of Sale Order names"
    )
    picking_list = fields.Text(
        string="Transfer Names", help="Comma separated list of Transfer names"
    )

    # END #########

    @api.onchange("sale_order_id", "picking_id")
    def onchange_related_record(self):
        """
        Limit the serials if a sale order is selected
        """

    def action_add(self):
        """
        Add the selected records
        """

        if self.type == "search":
            pickings = self.get_pickings_from_search()
        else:
            pickings = self.get_pickings_from_list()

        # These are the SKUs available in the records
        # filter out systems
        components = (
            pickings.mapped("move_ids.product_id")  # Replaced move_lines with move_ids
            .filtered(lambda p: not p.has_configurable_attributes)
            .ids
        )

        lines_data = []
        for i, picking in enumerate(pickings):
            lines_data.append(
                {
                    "sale_order_id": picking.sale_id.id,
                    "picking_id": picking.id,
                    "sequence": i,
                }
            )

        return {
            "type": "ir.actions.act_window",
            "res_model": "constrained.sku.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"lines_data": lines_data, "components": components},
        }

    def get_pickings_from_search(self):
        """
        Get all Stock Pickings from the chosen records
        """

        pickings = self.env["stock.picking"]

        if self.sale_order_ids:
            # Filter valid Sale Orders
            valid_sale_orders = self.filter_sale_orders(self.sale_order_ids)

            # Use picking_ids and filter out pickings that are already 'done' or 'cancel'
            open_pickings = valid_sale_orders.mapped("picking_ids").filtered(
                lambda p: p.state not in ["done", "cancel"]
            )
            pickings += open_pickings

        if self.picking_ids:
            # Filter valid Stock Pickings
            valid_stock_pickings = self.filter_stock_pickings(self.picking_ids)

            # Add the Stock Pickings
            pickings += valid_stock_pickings

        return pickings

    def get_pickings_from_list(self):
        """
        Get all Stock Pickings from the input lists
        """

        # Define a custom sorting function that accepts sale_order_names as an argument
        def custom_sort(order, list_of_names):
            return (
                list_of_names.index(order.name)
                if order.name in list_of_names
                else len(list_of_names)
            )

        pickings = self.env["stock.picking"]
        if self.sale_order_list:
            # Get the list of Sale Order names
            sale_order_names = self.process_list(self.sale_order_list)

            # Get the Sale Orders
            sale_orders = self.env["sale.order"].search(
                [("name", "in", sale_order_names)]
            )

            # Filter valid Sale Orders
            valid_sale_orders = self.filter_sale_orders(sale_orders)

            # Sort the results based on the input
            sorted_sale_orders = valid_sale_orders.sorted(
                key=lambda order: custom_sort(order, sale_order_names)
            )

            # Add the Stock Pickings from the sale orders
            pickings += sorted_sale_orders.mapped("open_picking_ids")

        if self.picking_list:
            # Get the list of Stock Picking names
            stock_picking_names = self.process_list(self.picking_list)

            # Get the Stock Pickings
            stock_pickings = self.env["stock.picking"].search(
                [("name", "in", stock_picking_names)]
            )

            # Filter valid Stock Pickings
            valid_stock_pickings = self.filter_stock_pickings(stock_pickings)

            # Filter valid Sale Orders
            sorted_sale_orders = valid_stock_pickings.sorted(
                key=lambda order: custom_sort(order, stock_picking_names)
            )

            # Add the Stock Pickings
            pickings += sorted_sale_orders

        return pickings

    def filter_sale_orders(self, sale_orders):
        """
        Filter out Sale Orders with invalid states
        """
        return sale_orders.filtered(
            lambda so: so.state
            not in [
                "draft",
                "sent",
                "cancel",
            ]
        )

    def filter_stock_pickings(self, stock_pickings):
        """
        Filter out Stock Pickings
        We are only interested in Internal and Outgoing pickings with the correct state
        """
        return stock_pickings.filtered(
            lambda sp: sp.picking_type_code in ["internal", "outgoing"]
            and sp.state not in ["done", "cancel"]
        )

    def process_list(self, input_string):

        try:
            # Split the input string by new line first
            elements = input_string.split("\n")
            # Now split each line by comma and chain them into a single list
            result = [
                item.strip() for line in elements for item in line.split(",") if item
            ]
        except Exception as error:
            raise ValidationError(
                "Could not process input. Please make sure you use a comma or new lines separated"
                f" list!\nError: {error}"
            ) from error
        return result

    # END #########
