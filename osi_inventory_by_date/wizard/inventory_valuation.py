import base64
from io import BytesIO

import xlwt

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from ..report.inventory_valuation import InventoryValuationCategory
from . import xls_format


class InventoryValuationDateReport(models.TransientModel, InventoryValuationCategory):
    _name = "inventory.valuation.ondate.report"
    _description = "Inventory Valuation Report by Date"

    company_id = fields.Many2one("res.company", string="Company")
    warehouse_ids = fields.Many2many("stock.warehouse", string="warehouse")
    location_id = fields.Many2one("stock.location", string="Location")
    valuation_date = fields.Date(required=True, default=fields.Date.context_today)
    start_date = fields.Datetime(required=True, default=fields.Datetime.now)
    filter_product_ids = fields.Many2many("product.product", string="Products")
    filter_product_categ_ids = fields.Many2many("product.category", string="Categories")

    @api.onchange("company_id")
    def onchange_company_id(self):
        """
        Make warehouse compatible with company
        """
        warehouse_ids = self.env["stock.warehouse"].sudo().search([])
        if self.company_id:
            warehouse_ids = (
                self.env["stock.warehouse"]
                .sudo()
                .search([("company_id", "=", self.company_id.id)])
            )
        return {
            "domain": {"warehouse_ids": [("id", "in", [x.id for x in warehouse_ids])]},
            "value": {"warehouse_ids": False},
        }

    @api.onchange("warehouse_ids", "company_id")
    def onchange_warehouse(self):
        """
        Make warehouse compatible with company
        """
        location_obj = self.env["stock.location"]
        location_ids = location_obj.search([("usage", "=", "internal")])
        total_warehouses = self.warehouse_ids
        if total_warehouses:
            addtional_ids = []
            for warehouse in total_warehouses:
                store_location_id = warehouse.view_location_id.id
                addtional_ids.extend(
                    [
                        y.id
                        for y in location_obj.search(
                            [
                                ("location_id", "child_of", store_location_id),
                                ("usage", "=", "internal"),
                            ]
                        )
                    ]
                )
            location_ids = addtional_ids
        elif self.company_id:
            total_warehouses = (
                self.env["stock.warehouse"]
                .sudo()
                .search([("company_id", "=", self.company_id.id)])
            )
            addtional_ids = []
            for warehouse in total_warehouses:
                store_location_id = warehouse.view_location_id.id
                addtional_ids.extend(
                    [
                        y.id
                        for y in location_obj.search(
                            [
                                ("location_id", "child_of", store_location_id),
                                ("usage", "=", "internal"),
                            ]
                        )
                    ]
                )
            location_ids = addtional_ids
        else:
            location_ids = [p.id for p in location_ids]
        return {
            "domain": {"location_id": [("id", "in", location_ids)]},
            "value": {"location_id": False},
        }

    def _to_company(self, company_ids):
        company_obj = self.env["res.company"]
        warehouse_obj = self.env["stock.warehouse"].sudo()
        if not company_ids:
            company_ids = [x.id for x in company_obj.search([])]

        # filter to only have warehouses.
        selected_companies = []
        for company_id in company_ids:
            if warehouse_obj.search([("company_id", "=", company_id)]):
                selected_companies.append(company_id)

        return selected_companies

    def xls_get_warehouses(self, warehouses, company_id):
        warehouse_obj = self.env["stock.warehouse"].sudo()
        if not warehouses:
            return "ALL"

        warehouse_rec = warehouse_obj.search(
            [
                ("id", "in", warehouses),
                ("company_id", "=", company_id),
            ]
        )
        return warehouse_rec and ",".join([x.name for x in warehouse_rec]) or "-"

    @api.model
    def _product_detail(self, product_id):
        product = self.env["product.product"].sudo().browse(product_id)
        variable_attributes = product.attribute_line_ids.filtered(
            lambda l: len(l.value_ids) > 1
        ).mapped("attribute_id")
        variant = product.attribute_value_ids._variant_name(variable_attributes)
        product_name = variant and "%s (%s)" % (product.name, variant) or product.name
        return product_name, product.barcode, product.default_code

    def print_report(self):
        """
        Print report either by warehouse or product-category
        """
        assert (
            len(self) == 1
        ), "This option should only be used for a single id at a time."
        datas = {
            "form": {
                "company_id": self.company_id and [self.company_id.id] or [],
                "warehouse_ids": [y.id for y in self.warehouse_ids],
                "location_id": self.location_id and self.location_id.id or False,
                "valuation_date": self.valuation_date.strftime(DF),
                "start_date": self.start_date.strftime("%Y-%m-%d %H:%M"),
                "id": self.id,
                "filter_product_ids": [p.id for p in self.filter_product_ids],
                "filter_product_categ_ids": [
                    p.id for p in self.filter_product_categ_ids
                ],
            }
        }

        if [y.id for y in self.warehouse_ids] and (not self.company_id):
            self.warehouse_ids = []
            raise UserError(
                _(
                    "Please select company of those warehouses to get correct view.\n"
                    "You should remove all warehouses first from selection field."
                )
            )

        return (
            self.env.ref("osi_inventory_by_date.action_inventory_valuation_ondate")
            .with_context(landscape=True)
            .report_action(self, data=datas)
        )

    def print_xls_report(self):
        """
        Print ledger report
        """
        assert (
            len(self) == 1
        ), "This option should only be used for a single id at a time."
        workbook = xlwt.Workbook()

        M_header_tstyle = xls_format.font_style(
            position="center",
            bold=1,
            border=1,
            fontos="black",
            font_height=400,
            color="grey",
        )
        header_tstyle_c = xls_format.font_style(
            position="center",
            bold=1,
            border=1,
            fontos="black",
            font_height=180,
            color="grey",
        )
        other_tstyle_c = xls_format.font_style(
            position="center", fontos="black", font_height=180, color="grey"
        )
        other_tstyle_cr = xls_format.font_style(
            position="center",
            fontos="purple_ega",
            bold=1,
            font_height=180,
            color="grey",
        )
        # other_tstyle_r = xls_format.font_style(
        #     position="right", fontos="purple_ega", bold=1, font_height=180, color="grey"
        # )
        other_tstyle_grandc = xls_format.font_style(
            position="center",
            fontos="purple_ega",
            bold=1,
            border=1,
            font_height=180,
            color="grey",
        )
        other_tstyle_grandr = xls_format.font_style(
            position="right",
            fontos="purple_ega",
            bold=1,
            border=1,
            font_height=180,
            color="grey",
        )

        datas = {
            "form": {
                "company_id": self.company_id and [self.company_id.id] or [],
                "warehouse_ids": [y.id for y in self.warehouse_ids],
                "location_id": self.location_id and self.location_id.id or False,
                "valuation_date": self.valuation_date.strftime(DF),
                "start_date": self.start_date.strftime("%Y-%m-%d %H:%M"),
                "id": self.id,
                "filter_product_ids": [p.id for p in self.filter_product_ids],
                "filter_product_categ_ids": [
                    p.id for p in self.filter_product_categ_ids
                ],
            }
        }
        company_ids = self._to_company(self.company_id and [self.company_id.id] or [])

        company_obj = self.env["res.company"]
        summary = "Detail Report"
        for company in company_ids:
            c_rec = company_obj.sudo().browse(company)
            Header_Text = "%s" % (str(c_rec.name))
            sheet = workbook.add_sheet(Header_Text)
            sheet.set_panes_frozen(True)
            sheet.set_horz_split_pos(9)
            sheet.row(0).height = 256 * 3
            sheet.write_merge(0, 0, 0, 11, Header_Text, M_header_tstyle)

            total_lines = self._get_valuation_data(datas, company)
            warehouses = self.xls_get_warehouses(
                [y.id for y in self.warehouse_ids], company
            )
            sheet_start_header = 3
            sheet_start_value = 4
            sheet.write_merge(
                sheet_start_header, sheet_start_header, 0, 1, "Date", header_tstyle_c
            )
            sheet.write_merge(
                sheet_start_value,
                sheet_start_value,
                0,
                1,
                self.valuation_date.strftime(DF),
                other_tstyle_cr,
            )
            sheet.write_merge(
                sheet_start_header, sheet_start_header, 2, 3, "Company", header_tstyle_c
            )
            sheet.write_merge(
                sheet_start_value, sheet_start_value, 2, 3, c_rec.name, other_tstyle_c
            )
            sheet.write_merge(
                sheet_start_header,
                sheet_start_header,
                4,
                5,
                "Warehouse(s)",
                header_tstyle_c,
            )
            sheet.write_merge(
                sheet_start_value, sheet_start_value, 4, 5, warehouses, other_tstyle_c
            )
            sheet.write_merge(
                sheet_start_header,
                sheet_start_header,
                6,
                7,
                "Currency",
                header_tstyle_c,
            )
            sheet.write_merge(
                sheet_start_value,
                sheet_start_value,
                6,
                7,
                c_rec.currency_id.name,
                other_tstyle_c,
            )
            sheet.write_merge(
                sheet_start_header, sheet_start_header, 8, 9, "Display", header_tstyle_c
            )
            sheet.write_merge(
                sheet_start_value, sheet_start_value, 8, 9, summary, other_tstyle_c
            )

            header_row_start = 8
            sheet.write(header_row_start, 0, "Location", header_tstyle_c)
            sheet.col(0).width = 256 * 20
            sheet.write(header_row_start, 1, "Category", header_tstyle_c)
            sheet.col(1).width = 256 * 40
            sheet.write(header_row_start, 2, "Account", header_tstyle_c)
            sheet.col(2).width = 256 * 20
            sheet.write(header_row_start, 3, "Product", header_tstyle_c)
            sheet.col(3).width = 256 * 40
            sheet.write(header_row_start, 4, "Barcode", header_tstyle_c)
            sheet.col(4).width = 256 * 20
            sheet.write(header_row_start, 5, "Part Number", header_tstyle_c)
            sheet.col(5).width = 256 * 20
            sheet.write(header_row_start, 6, "Quantity", header_tstyle_c)
            sheet.col(6).width = 256 * 20
            sheet.write(header_row_start, 7, "Cost", header_tstyle_c)
            sheet.col(7).width = 256 * 20
            sheet.write(header_row_start, 8, "Value", header_tstyle_c)
            sheet.col(8).width = 256 * 20
            row = 9
            total_value = 0.0
            total_qty = 0.0
            for line in total_lines:
                qty = line.get("qty", 0.0)
                if qty > 0:
                    sheet.write(row, 0, line.get("location", ""), other_tstyle_c)
                    sheet.write(row, 1, line.get("category", ""), other_tstyle_c)
                    sheet.write(row, 2, line.get("account", ""), other_tstyle_c)
                    sheet.write(
                        row, 3, list(line.get("product").values())[0], other_tstyle_c
                    )
                    sheet.write(row, 4, line.get("barcode", ""), other_tstyle_c)
                    sheet.write(row, 5, line.get("sku", ""), other_tstyle_c)
                    sheet.write(row, 6, line.get("qty", ""), other_tstyle_c)
                    sheet.write(row, 7, line.get("cost", ""), other_tstyle_c)
                    sheet.write(row, 8, line.get("value", ""), other_tstyle_c)
                    total_qty += line.get("qty")
                    total_value += line.get("value", 0.0)
                    row += 1

            sheet.write(row, 0, "Grand Total", other_tstyle_grandc)
            sheet.write(row, 8, "%.2f" % total_value, other_tstyle_grandr)

        stream = BytesIO()
        workbook.save(stream)

        export_obj = self.env["inventory.valuation.success.box"]
        res_id = export_obj.create(
            {
                "file": base64.encodebytes(stream.getvalue()),
                "fname": "Inventory Valuation by Location and Date Report.xls",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/binary/download_document?model=inventory.valuation.success.box&field=file&record_id=%s&filename=Inventory Valuation by Location and Date Report.xls"
            % (res_id.id),
            "target": "new",
        }
