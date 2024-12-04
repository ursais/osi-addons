# Import Odoo libs
from collections import defaultdict
from odoo import api, fields, models


class SaleEstimateLineJob(models.Model):
    """
    Add customer_lead field Sale Estimate Line
    """

    _inherit = "sale.estimate.line.job"

    # COLUMNS #####

    customer_lead = fields.Float(
        compute="_compute_customer_lead",
        store=True,
        readonly=False,
        precompute=True,
    )
    forecast_availability = fields.Float(
        "Forecast Availability",
        compute="_compute_forecast_information",
        digits="Product Unit of Measure",
        compute_sudo=True,
    )
    forecast_expected_date = fields.Datetime(
        "Forecasted Expected date",
        compute="_compute_forecast_information",
        compute_sudo=True,
    )

    # END #########

    # METHODS #####

    @api.depends("product_id")
    def _compute_customer_lead(self):
        for line in self:
            line.customer_lead = line.product_id.sale_delay or 0.0

    @api.depends(
        "product_id",
        "product_uom_qty",
    )
    def _compute_forecast_information(self):
        """Compute forecasted information of the related product by warehouse."""
        self.forecast_availability = False
        self.forecast_expected_date = False

        # Prefetch product info to avoid fetching all product fields
        self.product_id.fetch(["type", "uom_id"])

        not_product_moves = self.filtered(
            lambda move: move.product_id.type != "product"
        )
        for move in not_product_moves:
            move.forecast_availability = move.product_qty

        product_moves = self - not_product_moves

        outgoing_unreserved_moves_per_warehouse = defaultdict(set)
        now = fields.Datetime.now()

        def key_virtual_available(move, incoming=False):
            warehouse_id = (
                move.location_dest_id.warehouse_id.id
                if incoming
                else move.location_id.warehouse_id.id
            )
            return warehouse_id, max(move.date or now, now)

        # Prefetch efficiently virtual_available for _is_consuming draft move.
        prefetch_virtual_available = defaultdict(set)
        virtual_available_dict = {}
        for move in product_moves:
            if move._is_consuming() and move.state == "draft":
                prefetch_virtual_available[key_virtual_available(move)].add(
                    move.product_id.id
                )
            elif move.picking_type_id.code == "incoming":
                prefetch_virtual_available[
                    key_virtual_available(move, incoming=True)
                ].add(move.product_id.id)
        for key_context, product_ids in prefetch_virtual_available.items():
            read_res = (
                self.env["product.product"]
                .browse(product_ids)
                .with_context(warehouse=key_context[0], to_date=key_context[1])
                .read(["virtual_available"])
            )
            virtual_available_dict[key_context] = {
                res["id"]: res["virtual_available"] for res in read_res
            }

        for move in product_moves:
            if move._is_consuming():
                if move.state == "assigned":
                    move.forecast_availability = move.product_uom._compute_quantity(
                        move.quantity, move.product_id.uom_id, rounding_method="HALF-UP"
                    )
                elif move.state == "draft":
                    # for move _is_consuming and in draft -> the forecast_availability > 0 if in stock
                    move.forecast_availability = (
                        virtual_available_dict[key_virtual_available(move)][
                            move.product_id.id
                        ]
                        - move.product_qty
                    )
                elif move.state in ("waiting", "confirmed", "partially_available"):
                    outgoing_unreserved_moves_per_warehouse[
                        move.location_id.warehouse_id
                    ].add(move.id)
            elif move.picking_type_id.code == "incoming":
                forecast_availability = virtual_available_dict[
                    key_virtual_available(move, incoming=True)
                ][move.product_id.id]
                if move.state == "draft":
                    forecast_availability += move.product_qty
                move.forecast_availability = forecast_availability

        for warehouse, moves_ids in outgoing_unreserved_moves_per_warehouse.items():
            if not warehouse:  # No prediction possible if no warehouse.
                continue
            moves = self.browse(moves_ids)
            forecast_info = moves._get_forecast_availability_outgoing(warehouse)
            for move in moves:
                move.forecast_availability, move.forecast_expected_date = forecast_info[
                    move
                ]

    # END #########
