import time
from datetime import datetime

import pytz

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class InventoryValuationCategory(models.AbstractModel):
    _name = "report.osi_inventory_by_date.inventory_valuation_ondate_report"
    _description = "Report Inventory Valuation : By Date"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get("form"):
            raise UserError(
                _("Form content is missing, this report cannot be printed.")
            )

        return {
            "doc_ids": self._ids,
            "docs": self,
            "data": data,
            "time": time,
            "get_warehouses_block": self._get_warehouses_block,
            "get_company": self._get_company,
            "get_valuation_data": self._get_valuation_data,
        }

    def _get_warehouses_block(self, warehouse_ids, company_id):
        warehouse_obj = self.env["stock.warehouse"].sudo()
        warehouses = "ALL"
        if warehouse_ids:
            warehouse_rec = warehouse_obj.search(
                [("id", "in", warehouse_ids), ("company_id", "=", company_id)]
            )
            if warehouse_rec:
                warehouses = ",".join([x.name for x in warehouse_rec])
            else:
                warehouses = "-"
        return warehouses

    def _get_company(self, company_ids):
        res_company_pool = self.env["res.company"]
        if not company_ids:
            company_ids = [x.id for x in res_company_pool.search([])]

        # filter to only have warehouses.
        selected_companies = []
        for company_id in company_ids:
            if (
                self.env["stock.warehouse"]
                .sudo()
                .search([("company_id", "=", company_id)])
            ):
                selected_companies.append(company_id)

        return res_company_pool.browse(selected_companies).read(["name", "currency_id"])

    def get_warehouse_name(self, warehouse_ids):
        """
        Return warehouse names
            - WH A, WH B...
        """
        warehouse_obj = self.env["stock.warehouse"].sudo()
        if not warehouse_ids:
            warehouse_ids = [x.id for x in warehouse_obj.search([])]
        war_detail = warehouse_obj.read(warehouse_ids, ["name"])
        return ", ".join([lt["name"] or "" for lt in war_detail])

    def find_warehouses(self, company_id):
        """
        Find all warehouses
        """
        return [
            x.id
            for x in self.env["stock.warehouse"]
            .sudo()
            .search([("company_id", "=", company_id)])
        ]

    def _find_locations(self, warehouses):
        """
        Find all warehouses stock locations and its childs.
        """
        warehouse_obj = self.env["stock.warehouse"].sudo()
        location_obj = self.env["stock.location"].sudo()
        stock_ids = []
        for warehouse in warehouses:
            stock_ids.append(warehouse_obj.sudo().browse(warehouse).view_location_id.id)
        # stock_ids = [x['view_location_id'] and x['view_location_id'][0]
        # for x in warehouse_obj.sudo().read(self.cr, 1, warehouses, ['view_location_id'])]
        return [
            location.id
            for location in location_obj.search(
                [("location_id", "child_of", stock_ids), ("usage", "=", "internal")]
            )
        ]

    def convert_withtimezone(self, userdate):
        """
        Convert to Time-Zone with compare to UTC
        """
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATETIME_FORMAT)
        tz_name = self.env.context.get("tz") or self.env.user.tz
        if tz_name:
            utc = pytz.timezone("UTC")
            context_tz = pytz.timezone(tz_name)
            # not need if you give default datetime into entry ;)
            user_datetime = user_date  # + relativedelta(hours=24.0)
            local_timestamp = context_tz.localize(user_datetime, is_dst=False)
            user_datetime = local_timestamp.astimezone(utc)
            return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    def _get_valuation_data(self, data, company_id):
        """
        View to get inventory value as of a date from the stock moves
        """
        # find all warehouses and get data for that product
        warehouse_ids = data["form"] and data["form"].get("warehouse_ids", []) or []
        if not warehouse_ids:
            warehouse_ids = self.find_warehouses(company_id)

        # find all locations from all warehouse for that company
        location_id = data["form"] and data["form"].get("location_id") or False
        if location_id:
            locations = [location_id]
        else:
            locations = self._find_locations(warehouse_ids)

        valuation_date = self.convert_withtimezone(
            data["form"]["valuation_date"] + " 23:59:59"
        )
        start_date = data["form"]["start_date"]
        self._cr.execute(
            """
                SELECT id,location,category,product,barcode,sku,
                CASE
                WHEN code1 is not null THEN code1
                ELSE code2
                END as account,
                coalesce(sum(qty), 0.0) as qty,
                coalesce(sum(value), 0.0) as value,
                CASE
                WHEN coalesce(sum(qty),0.0) = 0.0 THEN 0.0
                ELSE round(coalesce(sum(value), 0.0)/coalesce(sum(qty), 0.0), 2)::decimal
                END as cost
                FROM
                    ((
                    /* internal going out */
                    SELECT
                        pp.id as id, l.complete_name as location,
                        pc.name as category, pt.name as product,
                        acc1.code as code1, acc2.code as code2,
                        pp.default_code as sku, pp.barcode as barcode, m.date,
                        coalesce(sum(-abs(m.qty_done*uom2.factor/uom.factor))::
                        decimal, 0.0) AS qty,
                        coalesce(sum(-abs(m.qty_done*uom2.factor/uom.factor) *
                        cost.value_float)::decimal, 0.0) AS value
                    FROM product_product pp
                    LEFT JOIN stock_move_line m ON (m.product_id=pp.id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_category pc on (pt.categ_id=pc.id)
                    LEFT JOIN stock_location l ON (m.location_id=l.id)
                    LEFT JOIN uom_uom uom ON (m.product_uom_id=uom.id)
                    LEFT JOIN uom_uom uom2 ON (pt.uom_id=uom2.id)
                    LEFT JOIN ir_property irp1 on (irp1.res_id =
                        concat('product.category,',pc.id) and
                        irp1.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc1 on (acc1.id =
                        substr(irp1.value_reference, strpos(
                        irp1.value_reference, ',') + 1,
                        length(irp1.value_reference) - strpos(
                        irp1.value_reference,','))::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null and
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference,strpos(
                        irp2.value_reference, ',') + 1,
                        length(irp2.value_reference) - strpos(
                        irp2.value_reference,','))::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND
                        (m.location_id in %s) AND (m.location_dest_id in %s) AND
                        m.state='done' AND pp.active=True AND
                        pt.type = 'product' AND l.usage = 'internal'
                    GROUP BY pp.id, l.complete_name, pc.name, pt.name,
                        acc1.code, acc2.code, pp.default_code, m.date,
                        uom.factor, uom2.factor
                    )
                    UNION ALL
                    (
                    /* going out */
                    SELECT
                        pp.id as id, l.complete_name as location,
                        pc.name as category, pt.name as product,
                        acc1.code as code1, acc2.code as code2,
                        pp.default_code as sku,pp.barcode as barcode,m.date,
                        coalesce(sum(-abs(m.qty_done*uom2.factor/uom.factor))::
                        decimal, 0.0) AS qty,
                        coalesce(sum(-abs(m.qty_done*uom2.factor/uom.factor) *
                        cost.value_float)::decimal, 0.0) AS value
                    FROM product_product pp
                    LEFT JOIN stock_move_line m ON (m.product_id=pp.id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_category pc on (pt.categ_id=pc.id)
                    LEFT JOIN stock_location l ON (m.location_id=l.id)
                    LEFT JOIN uom_uom uom ON (m.product_uom_id=uom.id)
                    LEFT JOIN uom_uom uom2 ON (pt.uom_id=uom2.id)
                    LEFT JOIN ir_property irp1 on (irp1.res_id =
                        concat('product.category,', pc.id) AND
                        irp1.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc1 ON (acc1.id = substr(
                        irp1.value_reference, strpos(irp1.value_reference, ',
                        ') + 1, length(irp1.value_reference) - strpos(
                        irp1.value_reference, ','))::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null AND
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference, strpos(
                        irp2.value_reference, ',') + 1, length(
                        irp2.value_reference) - strpos(irp2.value_reference,',
                        '))::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND (m.location_id in %s) AND
                        (m.location_dest_id not in %s) AND m.state='done' AND
                        pp.active=True AND pt.type = 'product' AND
                         l.usage = 'internal'
                    GROUP BY pp.id, l.complete_name, pc.name, pt.name,
                        acc1.code, acc2.code, pp.default_code, m.date,
                        uom.factor, uom2.factor
                    )
                    UNION ALL
                    (
                    /* coming in */
                    SELECT
                        pp.id, l.complete_name as location, pc.name as pc_name,
                        pt.name as product, acc1.code as code1,
                        acc2.code as code2, pp.default_code,
                        pp.barcode as barcode,m.date,
                        coalesce(sum(abs(m.qty_done*uom2.factor/uom.factor))::
                        decimal, 0.0) AS qty,
                        coalesce(sum(abs(m.qty_done*uom2.factor/uom.factor) *
                        cost.value_float)::decimal, 0.0) AS value
                    FROM product_product pp
                    LEFT JOIN stock_move_line m ON (m.product_id=pp.id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_category pc on (pt.categ_id=pc.id)
                    LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                    LEFT JOIN uom_uom uom ON (m.product_uom_id=uom.id)
                    LEFT JOIN uom_uom uom2 ON (pt.uom_id=uom2.id)
                    LEFT JOIN ir_property irp1 on (irp1.res_id =
                        concat('product.category,',pc.id) AND
                        irp1.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc1 on (acc1.id =
                        substr(irp1.value_reference,strpos(
                        irp1.value_reference, ',') + 1, length(
                        irp1.value_reference) - strpos(irp1.value_reference, ',
                        '))::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null AND
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference, strpos(
                        irp2.value_reference, ',') + 1, length(
                        irp2.value_reference) - strpos(irp2.value_reference,',
                        '))::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND
                        (m.location_dest_id in %s) AND
                        (m.location_id not in %s) AND m.state='done' AND
                        pp.active=True AND pt.type = 'product' AND
                        l.usage = 'internal'
                    GROUP BY pp.id, l.complete_name, pc.name, pt.name,
                    acc1.code, acc2.code, pp.default_code, m.date, uom.factor,
                    uom2.factor
                    )
                    UNION ALL
                    (
                    /* internal coming in */
                    SELECT
                        pp.id, l.complete_name as location, pc.name as pc_name,
                        pt.name as product, acc1.code as code1,
                        acc2.code as code2, pp.default_code,
                        pp.barcode as barcode, m.date,
                        coalesce(sum(abs(m.qty_done*uom2.factor/uom.factor))::
                        decimal, 0.0) AS qty,
                        coalesce(sum(abs(m.qty_done*uom2.factor/uom.factor) *
                        cost.value_float)::decimal, 0.0) AS value
                    FROM product_product pp
                    LEFT JOIN stock_move_line m ON (m.product_id=pp.id)
                    LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                    LEFT JOIN product_category pc on (pt.categ_id=pc.id)
                    LEFT JOIN stock_location l ON (m.location_dest_id=l.id)
                    LEFT JOIN uom_uom uom ON (m.product_uom_id=uom.id)
                    LEFT JOIN uom_uom uom2 ON (pt.uom_id=uom2.id)
                    LEFT JOIN ir_property irp1 on (irp1.res_id =
                        concat('product.category,',pc.id) AND
                        irp1.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc1 on (acc1.id =
                        substr(irp1.value_reference, strpos(
                        irp1.value_reference, ',') + 1, length(
                        irp1.value_reference) - strpos(irp1.value_reference,',
                        '))::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null AND
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference, strpos(
                        irp2.value_reference, ',') + 1, length(
                        irp2.value_reference) - strpos(irp2.value_reference,',
                        '))::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND
                        (m.location_dest_id in %s) AND (m.location_id in %s) AND
                        m.state='done' AND pp.active=True AND
                        pt.type = 'product' AND l.usage = 'internal'
                    GROUP BY pp.id, l.complete_name, pc.name,pt.name,
                       acc1.code, acc2.code, pp.default_code, m.date,
                       uom.factor, uom2.factor
                    ))
                AS foo
                WHERE qty !=  0.0
                GROUP BY id, location, category, product, barcode, sku, account
            """,
            (
                start_date,
                valuation_date,
                tuple(locations),
                tuple(locations),
                start_date,
                valuation_date,
                tuple(locations),
                tuple(locations),
                start_date,
                valuation_date,
                tuple(locations),
                tuple(locations),
                start_date,
                valuation_date,
                tuple(locations),
                tuple(locations),
            ),
        )
        res = self._cr.dictfetchall()
        return res
