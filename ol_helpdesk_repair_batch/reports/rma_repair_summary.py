# Import Python libs
from collections import defaultdict
from math import ceil

# Import Odoo libs
from odoo import api, models


class ReportRmaRepairSummary(models.AbstractModel):
    _name = "report.ol_helpdesk_repair_batch.report_rma_repair_summary"
    _description = "RMA Progress Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Hook into render to set company specific format for the report"""

        # Get the module/report name from the class name
        report = self.env["ir.actions.report"]._get_report_from_name(
            self._name.replace("report.", "")
        )

        tickets = self.env[report.model].browse(docids)

        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "docs": tickets,
            "product_lines": self.get_product_lines(tickets),
        }

    def get_product_lines(self, tickets):
        data = defaultdict(list)

        for ticket in tickets:
            # Go through directly linked repair orders
            repairs = ticket.repair_ids.filtered(lambda ro: ro.state == "done")

            non_serial_line_list = defaultdict(lambda: {"qty": 0, "notes": ""})

            for repair in repairs:
                product = repair.product_id
                lot = repair.lot_id if hasattr(repair, "lot_id") else False

                if lot:
                    # Track as serial-specific line
                    data[ticket.id].append(
                        {
                            "product_id": product,
                            "qty": 1,
                            "serial_number": lot.display_name,
                            "notes": (
                                repair.external_notes.strip()
                                if repair.external_notes
                                else ""
                            ),
                        }
                    )
                else:
                    non_serial_line_list[product]["qty"] += 1
                    if repair.external_notes:
                        non_serial_line_list[product]["notes"] += "</br>{}".format(
                            repair.external_notes.strip()
                        )

            # Append non-serialized products
            for product_id, line_data in non_serial_line_list.items():
                data[ticket.id].append(
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
