# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, _


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    def _get_bom_lines(self, bom, bom_quantity, product, line_id, level):
        """Description: Calls super on parent function.
        Adds a new key:value(designator) pair to
        each dictionary in the list(components)
        """
        components, total = super()._get_bom_lines(
            bom, bom_quantity, product, line_id, level
        )
        lines = self.env["mrp.bom.line"]
        # loop through every dictionary in the list
        for dictionary in components:
            # search for the mrp.bom.line object for that dictionary
            line_id = lines.search([("id", "=", dictionary["line_id"])])
            # and set the key:value in it's dictionary
            dictionary["designator"] = line_id.designator
        return components, total

    def _get_pdf_line(
        self, bom_id, product_id=False, qty=1, child_bom_ids=[], unfolded=False
    ):
        """Description: Override parent function to edit sub-function content
        Added designator to the dictionary for access in xml.
        """
        data = self._get_bom(bom_id=bom_id, product_id=product_id.id, line_qty=qty)

        def get_sub_lines(bom, product_id, line_qty, line_id, level):
            data = self._get_bom(
                bom_id=bom.id,
                product_id=product_id.id,
                line_qty=line_qty,
                line_id=line_id,
                level=level,
            )
            bom_lines = data["components"]
            lines = []
            for bom_line in bom_lines:
                # appended designator
                lines.append(
                    {
                        "name": bom_line["prod_name"],
                        "type": "bom",
                        "quantity": bom_line["prod_qty"],
                        "uom": bom_line["prod_uom"],
                        "prod_cost": bom_line["prod_cost"],
                        "bom_cost": bom_line["total"],
                        "level": bom_line["level"],
                        "code": bom_line["code"],
                        "designator": bom_line["designator"],
                    }
                )
                if bom_line["child_bom"] and (
                    unfolded or bom_line["child_bom"] in child_bom_ids
                ):
                    line = self.env["mrp.bom.line"].browse(bom_line["line_id"])
                    lines += get_sub_lines(
                        line.child_bom_id,
                        line.product_id,
                        bom_line["prod_qty"],
                        line,
                        level + 1,
                    )
            if data["operations"]:
                lines.append(
                    {
                        "name": _("Operations"),
                        "type": "operation",
                        "quantity": data["operations_time"],
                        "uom": _("minutes"),
                        "bom_cost": data["operations_cost"],
                        "level": level,
                    }
                )
                for operation in data["operations"]:
                    if unfolded or "operation-" + str(bom.id) in child_bom_ids:
                        lines.append(
                            {
                                "name": operation["name"],
                                "type": "operation",
                                "quantity": operation["duration_expected"],
                                "uom": _("minutes"),
                                "bom_cost": operation["total"],
                                "level": level + 1,
                            }
                        )
            return lines

        bom = self.env["mrp.bom"].browse(bom_id)
        product = product_id or bom.product_id or bom.product_tmpl_id.product_variant_id
        pdf_lines = get_sub_lines(bom, product, qty, False, 1)
        data["components"] = []
        data["lines"] = pdf_lines
        return data
