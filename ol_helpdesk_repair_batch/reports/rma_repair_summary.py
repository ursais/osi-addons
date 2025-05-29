# Import Python libs
from collections import defaultdict
from math import ceil

# Import Odoo libs
from odoo import api, models


class ReportRmaRepairSummary(models.AbstractModel):
    _name = "report.ol_pdf_reports.report_rma_repair_summary"
    _description = "RMA Progress Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env["ir.actions.report"]._get_report_from_name(
            self._name.replace("report.", "")
        )

        rmas = self.env[report.model].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "docs": rmas,
            "product_lines": self.get_product_lines(rmas),
        }

    def get_product_lines(self, rmas):
        data = defaultdict(list)
        for rma in rmas:

            # Find RMA Lines that are of certain type, and have Repair Orders
            rma_lines = rma.used_rma_line_ids.filtered(
                lambda l: l.line_product_type in ["component", "system", "phantom"]
                and l.repair_order_ids
            )

            non_serial_line_list = defaultdict(lambda: {"qty": 0, "notes": ""})
            sale_order_line_ph_kit_calc = defaultdict(lambda: defaultdict(int))
            for rma_line in rma_lines:

                if not rma_line.repair_order_ids.filtered(
                    lambda ro: ro.state in ["done"]
                ):
                    # We only want to list RMA Lines that have atr least one Repair Orders
                    continue

                if rma_line.lot_id:
                    # If we have a serial number
                    # each RMA Line should be represented as
                    # a separate line in the report
                    data[rma.id].append(
                        {
                            "product_id": rma_line.product_id,
                            "qty": 1,
                            "serial_number": rma_line.lot_id.display_name,
                            "notes": self.get_notes(rma_line),
                        }
                    )
                else:
                    if rma_line.line_product_type == "phantom":
                        # If this RMA Line if for a Phantom Kit's component,
                        # we want to show the Kit and not the component it self
                        product = rma_line.sale_order_line.product_id

                        # How many of this component have we repaired for this exact Phantom kit.
                        sale_order_line_ph_kit_calc[rma_line.sale_order_line][
                            rma_line.product_id
                        ] += 1
                        current_ph_kit_component_qty = sale_order_line_ph_kit_calc[
                            rma_line.sale_order_line
                        ][rma_line.product_id]

                        # How many of this component we have in the phantom kit
                        component_qty_in_ph_kit = rma_line.sale_order_line.product_id.phantom_bom_id.bom_line_ids.filtered(
                            lambda l, rma_line=rma_line: l.product_id
                            == rma_line.product_id
                        ).product_qty

                        # How many Phantom Kit's where effected by the component repairs.
                        # Example: If we have qty:5 Phantom Kits on the Sale Order Line,
                        # and the Phantom Kit has qty: 3 of a component in it,
                        # and we have repaired 2 of those components we have ceil(2/3) = 1 - we affected 1 Phantom Kits
                        # if we have repaired 7 of those components we have ceil(7/3) = 3 - we affected 3 Phantom Kits
                        number_of_ph_kits = ceil(
                            float(current_ph_kit_component_qty)
                            / float(component_qty_in_ph_kit)
                        )

                        if number_of_ph_kits > non_serial_line_list[product]["qty"]:
                            # If this component shows us a bigger affected Phantom Kit qty
                            # then the other components, we need to use this one
                            non_serial_line_list[product]["qty"] = number_of_ph_kits
                    else:
                        product = rma_line.product_id
                        non_serial_line_list[product]["qty"] += 1

                    # Collect the notes for the same product
                    non_serial_line_list[product]["notes"] += "</br>{}".format(
                        self.get_notes(rma_line)
                    )

            # Add each non serial product to the info
            for product_id, line_data in non_serial_line_list.items():
                data[rma.id].append(
                    {
                        "product_id": product_id,
                        "serial_number": False,
                        "notes": line_data["notes"],
                        "qty": int(line_data["qty"]),
                    }
                )

        return data

    def get_notes(self, rma_line):
        notes = ""
        # These are RMA Lines with products that have a serial number

        # Loop through all repair orders and merge the notes
        for repair_order in rma_line.repair_order_ids:
            if repair_order.state not in ["done"] or not repair_order.external_notes:
                # We only care about finished repair orders
                continue

            notes += "{note}".format(note=repair_order.external_notes.strip())

        return notes
