# -*- coding: utf-8 -*-

from odoo import api, models


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"

    @api.model
    def _get_bom_data(
        self,
        bom,
        warehouse,
        product=False,
        line_qty=False,
        bom_line=False,
        level=0,
        parent_bom=False,
        parent_product=False,
        index=0,
        product_info=False,
        ignore_stock=False,
    ):
        bom_report_line = super()._get_bom_data(
            bom,
            warehouse,
            product=product,
            line_qty=line_qty,
            bom_line=bom_line,
            level=level,
            parent_bom=parent_bom,
            parent_product=parent_product,
            index=index,
            product_info=product_info,
            ignore_stock=ignore_stock,
        )
        is_minimized = self.env.context.get("minimized", False)
        if not product:
            product = bom.product_id or bom.product_tmpl_id.product_variant_id
        if line_qty is False:
            line_qty = bom.product_qty

        if not product_info:
            product_info = {}

        company = bom.company_id or self.env.company
        current_quantity = line_qty
        if bom_line:
            current_quantity = (
                bom_line.product_uom_id._compute_quantity(line_qty, bom.product_uom_id)
                or 0
            )

        prod_price = 0
        if not is_minimized:
            if product:
                prod_price = (
                    product.uom_id._compute_price(
                        product.with_company(company).lst_price, bom.product_uom_id
                    )
                    * current_quantity
                )
            else:
                # Use the product template instead of the variant
                prod_price = (
                    bom.product_tmpl_id.uom_id._compute_price(
                        bom.product_tmpl_id.with_company(company).lst_price,
                        bom.product_uom_id,
                    )
                    * current_quantity
                )

        bom_report_line["prod_price"] = prod_price
        return bom_report_line

    @api.model
    def _get_component_data(
        self,
        parent_bom,
        parent_product,
        warehouse,
        bom_line,
        line_quantity,
        level,
        index,
        product_info,
        ignore_stock=False,
    ):
        component_line = super()._get_component_data(
            parent_bom,
            parent_product,
            warehouse,
            bom_line,
            line_quantity,
            level,
            index,
            product_info,
            ignore_stock=ignore_stock,
        )
        company = parent_bom.company_id or self.env.company
        price = (
            bom_line.product_id.uom_id._compute_price(
                bom_line.product_id.with_company(company).lst_price,
                bom_line.product_uom_id,
            )
            * line_quantity
        )
        rounded_price = company.currency_id.round(price)
        component_line["prod_price"] = rounded_price
        return component_line

    @api.model
    def _get_bom_array_lines(
        self, data, level, unfolded_ids, unfolded, parent_unfolded=True
    ):
        bom_lines = data["components"]
        lines = []
        for bom_line in bom_lines:
            line_unfolded = ("bom_" + str(bom_line["index"])) in unfolded_ids
            line_visible = level == 1 or unfolded or parent_unfolded
            lines.append(
                {
                    "bom_id": bom_line["bom_id"],
                    "name": bom_line["name"],
                    "type": bom_line["type"],
                    "quantity": bom_line["quantity"],
                    "quantity_available": bom_line["quantity_available"],
                    "quantity_on_hand": bom_line["quantity_on_hand"],
                    "producible_qty": bom_line.get("producible_qty", False),
                    "uom": bom_line["uom_name"],
                    "prod_cost": bom_line["prod_cost"],
                    "prod_price": (
                        bom_line["prod_price"] if bom_line.get("prod_price") else 0
                    ),
                    "bom_cost": bom_line["bom_cost"],
                    "route_name": bom_line["route_name"],
                    "route_detail": bom_line["route_detail"],
                    "lead_time": bom_line["lead_time"],
                    "manufacture_delay": bom_line["manufacture_delay"],
                    "level": bom_line["level"],
                    "code": bom_line["code"],
                    "availability_state": bom_line["availability_state"],
                    "availability_display": bom_line["availability_display"],
                    "visible": line_visible,
                }
            )
            if bom_line.get("components"):
                lines += self._get_bom_array_lines(
                    bom_line,
                    level + 1,
                    unfolded_ids,
                    unfolded,
                    line_visible and line_unfolded,
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
                    "visible": parent_unfolded,
                }
            )
            operations_unfolded = unfolded or (
                parent_unfolded and ("operations_" + str(data["index"])) in unfolded_ids
            )
            for operation in data["operations"]:
                lines.append(
                    {
                        "name": operation["name"],
                        "type": "operation",
                        "quantity": operation["quantity"],
                        "uom": _("minutes"),
                        "bom_cost": operation["bom_cost"],
                        "level": level + 1,
                        "visible": operations_unfolded,
                    }
                )
        if data["byproducts"]:
            lines.append(
                {
                    "name": _("Byproducts"),
                    "type": "byproduct",
                    "uom": False,
                    "quantity": data["byproducts_total"],
                    "bom_cost": data["byproducts_cost"],
                    "level": level,
                    "visible": parent_unfolded,
                }
            )
            byproducts_unfolded = unfolded or (
                parent_unfolded and ("byproducts_" + str(data["index"])) in unfolded_ids
            )
            for byproduct in data["byproducts"]:
                lines.append(
                    {
                        "name": byproduct["name"],
                        "type": "byproduct",
                        "quantity": byproduct["quantity"],
                        "uom": byproduct["uom_name"],
                        "prod_cost": byproduct["prod_cost"],
                        "bom_cost": byproduct["bom_cost"],
                        "level": level + 1,
                        "visible": byproducts_unfolded,
                    }
                )
        return lines
