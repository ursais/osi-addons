import logging
import time
from datetime import datetime

import pytz

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class InventoryValuationCategory(models.AbstractModel):
    _name = "report.osi_inventory_by_date.inventory_valuation_ondate_report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Get report values for the inventory valuation report template
        
        :param docids: Document IDs (not used in this report)
        :param data: Dictionary containing report data including form parameters
        :return: Dictionary of values to pass to the report template
        :raises UserError: If form data is missing or invalid
        """
        try:
            if not data or not data.get("form"):
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
        except UserError:
            # Re-raise UserError as-is (user-facing messages)
            raise
        except Exception as e:
            _logger.error(
                "Error in _get_report_values: %s",
                str(e),
                exc_info=True
            )
            raise UserError(
                _(
                    "An error occurred while preparing the report. "
                    "Please contact your system administrator. Error: %s"
                ) % str(e)
            ) from e

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
        
        :param userdate: Date string in DEFAULT_SERVER_DATETIME_FORMAT
        :return: Converted date string in UTC timezone
        :raises UserError: If date format is invalid or timezone conversion fails
        """
        try:
            if not userdate:
                raise UserError(_("Date value is required for timezone conversion."))
            
            user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATETIME_FORMAT)
            tz_name = self.env.context.get("tz") or (self.env.user.tz if hasattr(self.env.user, 'tz') else None)
            
            if tz_name:
                try:
                    utc = pytz.timezone("UTC")
                    context_tz = pytz.timezone(tz_name)
                    # not need if you give default datetime into entry ;)
                    user_datetime = user_date  # + relativedelta(hours=24.0)
                    local_timestamp = context_tz.localize(user_datetime, is_dst=False)
                    user_datetime = local_timestamp.astimezone(utc)
                    return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                except Exception as tz_error:
                    _logger.warning(
                        "Timezone conversion failed for timezone '%s': %s. Using UTC.",
                        tz_name,
                        str(tz_error)
                    )
                    # Fallback to UTC if timezone conversion fails
                    return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            
            return user_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        except ValueError as ve:
            _logger.error(
                "Invalid date format '%s' for timezone conversion: %s",
                userdate,
                str(ve)
            )
            raise UserError(
                _("Invalid date format. Expected format: %s. Received: %s")
                % (DEFAULT_SERVER_DATETIME_FORMAT, userdate)
            ) from ve
        except Exception as e:
            _logger.error(
                "Unexpected error in convert_withtimezone: %s",
                str(e),
                exc_info=True
            )
            raise UserError(
                _("An error occurred while converting the date. Please check the date format.")
            ) from e

    def _get_valuation_data(self, data, company_id):
        """
        View to get inventory value as of a date from the stock moves
        
        :param data: Dictionary containing form data with warehouse_ids, location_id, 
                     valuation_date, start_date, filter_product_ids, filter_product_categ_ids
        :param company_id: Company ID for filtering
        :return: List of dictionaries containing valuation data
        :raises UserError: If input validation fails or query execution fails
        """
        try:
            # Input validation
            if not data or not data.get("form"):
                raise UserError(_("Form data is missing. Please try again."))
            
            form_data = data["form"]
            
            # Validate required fields
            if not form_data.get("valuation_date"):
                raise UserError(_("Valuation date is required."))
            
            if not form_data.get("start_date"):
                raise UserError(_("Start date is required."))
            
            # find all warehouses and get data for that product
            warehouse_ids = form_data.get("warehouse_ids", []) or []
            if not warehouse_ids:
                warehouse_ids = self.find_warehouses(company_id)
            
            if not warehouse_ids:
                _logger.warning(
                    "No warehouses found for company %s. Returning empty results.",
                    company_id
                )
                return []

            # find all locations from all warehouse for that company
            location_id = form_data.get("location_id") or False
            if location_id:
                locations = [location_id]
            else:
                locations = self._find_locations(warehouse_ids)
            
            # Validate locations
            if not locations:
                _logger.warning(
                    "No locations found for warehouses %s. Returning empty results.",
                    warehouse_ids
                )
                return []
            
            # Ensure locations is a list of integers
            if not isinstance(locations, list):
                locations = [locations]
            locations = [int(loc) for loc in locations if loc]
            
            if not locations:
                _logger.warning("Locations list is empty after validation.")
                return []

            valuation_date = self.convert_withtimezone(
                form_data["valuation_date"] + " 23:59:59"
            )

            start_date = form_data["start_date"]
            
            _logger.info(
                "Generating inventory valuation report: company=%s, warehouses=%s, "
                "locations=%s, start_date=%s, valuation_date=%s",
                company_id, warehouse_ids, len(locations), start_date, valuation_date
            )
            
            # Prepare query parameters with proper tuple formatting
            locations_tuple = tuple(locations)
            
            # Execute query with error handling
            try:
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
                        substr(irp1.value_reference, strpos(irp1.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null and
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference,strpos(irp2.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND
                        (m.location_id in %s) AND (m.location_dest_id in %s) AND
                        m.state='done' AND pp.active=True AND
                        pt.type = 'product' AND l.usage = 'internal' AND
                        (acc2.company_id = m.company_id or acc1.company_id = m.company_id)
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
                        irp1.value_reference, strpos(irp1.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null AND
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference, strpos(irp2.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND (m.location_id in %s) AND
                        (m.location_dest_id not in %s) AND m.state='done' AND
                        pp.active=True AND pt.type = 'product' AND
                         l.usage = 'internal' AND
                         (acc2.company_id = m.company_id or acc1.company_id = m.company_id)
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
                        substr(irp1.value_reference,strpos(irp1.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null AND
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference, strpos(irp2.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND
                        (m.location_dest_id in %s) AND
                        (m.location_id not in %s) AND m.state='done' AND
                        pp.active=True AND pt.type = 'product' AND
                        l.usage = 'internal' AND
                        (acc2.company_id = m.company_id or acc1.company_id = m.company_id)
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
                        substr(irp1.value_reference, strpos(irp1.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property irp2 on (irp2.res_id is null AND
                        irp2.name='property_stock_valuation_account_id')
                    LEFT JOIN account_account acc2 on (acc2.id =
                        substr(irp2.value_reference, strpos(irp2.value_reference, ',') + 1)::int)
                    LEFT JOIN ir_property cost on (cost.res_id =
                        concat('product.product,', pp.id) AND
                        cost.name='standard_price')
                    WHERE  m.date > %s AND m.date < %s AND
                        (m.location_dest_id in %s) AND (m.location_id in %s) AND
                        m.state='done' AND pp.active=True AND
                        pt.type = 'product' AND l.usage = 'internal' AND
                        (acc2.company_id = m.company_id or acc1.company_id = m.company_id)
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
                        locations_tuple,
                        locations_tuple,
                        start_date,
                        valuation_date,
                        locations_tuple,
                        locations_tuple,
                        start_date,
                        valuation_date,
                        locations_tuple,
                        locations_tuple,
                        start_date,
                        valuation_date,
                        locations_tuple,
                        locations_tuple,
                    ),
                )
                
                res = self._cr.dictfetchall()
                
                _logger.info(
                    "Inventory valuation query completed successfully. "
                    "Retrieved %d records.",
                    len(res) if res else 0
                )
                
                return res or []
                
            except Exception as query_error:
                _logger.error(
                    "SQL query execution failed for inventory valuation report: %s. "
                    "Company: %s, Warehouses: %s, Locations: %s, "
                    "Start Date: %s, Valuation Date: %s",
                    str(query_error),
                    company_id,
                    warehouse_ids,
                    locations,
                    start_date,
                    valuation_date,
                    exc_info=True
                )
                raise UserError(
                    _(
                        "An error occurred while generating the inventory valuation report. "
                        "Please check the logs for details. Error: %s"
                    ) % str(query_error)
                ) from query_error
                
        except UserError:
            # Re-raise UserError as-is (these are user-facing messages)
            raise
        except Exception as e:
            _logger.error(
                "Unexpected error in _get_valuation_data: %s",
                str(e),
                exc_info=True
            )
            raise UserError(
                _(
                    "An unexpected error occurred while generating the inventory valuation report. "
                    "Please contact your system administrator. Error: %s"
                ) % str(e)
            ) from e
