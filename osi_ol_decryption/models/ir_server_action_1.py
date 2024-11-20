from odoo import api, models, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)
import psycopg2
import psycopg2.extras
import odoorpc


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def update_compute_complete_address(self):
        partner_ids = self.env['res.partner'].search([("contact_address_complete", "!=", ""), ('active', '=', 'f')], order="id")
        for partner in partner_ids:
            print ("\n partner", partner.id)
            partner._compute_complete_address()

    def update_supplier_invoice_number(self):
        # Fetch supplier invoice numbers and references for in_invoice types
        self._cr.execute("""
            SELECT supplier_invoice_number, ref, id 
            FROM temp_account_move 
            WHERE move_type = 'in_invoice' AND supplier_invoice_number != ''
        """)
        move_ids = self._cr.dictfetchall()
        
        duplicate_supplier_numbers = set()
        
        for move in move_ids:
            supplier_invoice_number = move.get('supplier_invoice_number')
            ref = move.get('ref')
            move_id = move.get('id')
            
            # Check for duplicate supplier invoice numbers
            is_duplicate = supplier_invoice_number in duplicate_supplier_numbers
            duplicate_supplier_numbers.add(supplier_invoice_number)

            # Determine the new ref value based on conditions
            if is_duplicate:
                if ref:
                    new_ref = f"{ref}-{supplier_invoice_number}-{move_id}"
                else:
                    new_ref = f"{supplier_invoice_number}-{move_id}"
            else:
                new_ref = f"{ref}-{supplier_invoice_number}" if ref else supplier_invoice_number
            

            self._cr.execute("UPDATE account_move SET ref = %s WHERE id = %s", (new_ref, move_id))


    def update_product_tax_code(self):
        conn_13 = psycopg2.connect(
            database="odoo13_20241106",
            user="odoo",
            password="odoo",
            host="localhost",
            port="5432",
        )

        cur_13 = conn_13.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur_13.execute("select res_id,value_reference from ir_property where name = 'tax_code_id' and company_id = 1")
        product_tax_code_ids = cur_13.fetchall()
        for rec in product_tax_code_ids:
            res_id = rec.get('res_id').split(',')[1]
            value = rec.get('value_reference').split(',')[1]
            self._cr.execute("update product_template set tax_code_id = %s where id = %s", (value,res_id ))



    def update_tracking_number(self):
        self._cr.execute(
            """UPDATE stock_picking AS sp SET carrier_tracking_ref = tn.number FROM (SELECT picking_id, STRING_AGG(number, ', ') AS number FROM tracking_number GROUP BY picking_id) AS tn WHERE sp.id = tn.picking_id;"""
        )

    def odoo_rpc_call_product_weight(self):
        odoo_13 = odoorpc.ODOO("localhost", port=8069, timeout=12000)
        odoo_13.login("odoo13_20241106", "admin", "pw")
        obj_product = odoo_13.env["product.product"]
        final_count  = 172723
        limit = 10000
        offset = 0
        while True:
            product_ids = obj_product.search_read(
                [('id', 'not in', [112677, 147811,92960,96905,135649, 143682]),'|',("active", "=", True),("active", "=", False)],
                fields=["id", "weight", "product_tmpl_id"],
                order="id",
                offset=offset,
                limit=limit
            )
            print("\n product_ids", product_ids)
            for product in product_ids:
                self._cr.execute(
                    "update product_template set weight_dummy = %s where id = %s"
                    % (product.get("weight"), product.get("product_tmpl_id")[0])
                )
            if offset > final_count:
                break
            offset += 10000

    @api.model
    def odoo_rpc_call(self):

        odoo_13 = odoorpc.ODOO("localhost", port=8069, timeout=12000)
        odoo_13.login("odoo13_20241106", "admin", "pw")
        obj_product = odoo_13.env["product.template"]
        obj_att_value = odoo_13.env["product.attribute.value"]
        obj_v17_att_value = odoo_13.env["product.attribute.value"]

        obj_product_17 = self.env["product.template"]

        """FIX work_location in Employee"""
        print ("\n FIX work_location in Employee")
        employee_obj = self.env["hr.employee"]
        work_location_obj = self.env["hr.work.location"]
        obj_employee = odoo_13.env["hr.employee"]
        employee_ids = obj_employee.search_read(
            [("work_location", "!=", False)], fields=["id", "work_location"], order="id"
        )
        for emp in employee_ids:
            work_id = work_location_obj.search(
                [("name", "=", emp.get("work_location"))], limit=1
            )
            if work_id:
                print("\n work_idwork_id", work_id)
                self._cr.execute(
                    "update hr_employee set work_location_id = %s where id = %s"
                    % (work_id.id, emp.get("id"))
                )

        """FIX Payment Team Data missing"""
        print ("\n FIX Payment Team Data missing")
        obj_sale_order = odoo_13.env["sale.order"]
        sale_order_ids = obj_sale_order.search_read(
            [("id", "!=", False)], fields=["id", "payment_term_id"], order="id"
        )

        for sales in sale_order_ids:
            if sales.get("payment_term_id"):
                print("\n payment", sales.get("payment_term_id"))
                self._cr.execute(
                    "update sale_order set payment_term_id = %s where id = %s"
                    % (
                        sales.get("payment_term_id")[0],
                        sales.get("id"),
                    )
                )

        atts_val = obj_att_value.search_read([], fields=['id', 'name'], order="id")
        """Remove record rule from v13 of company before run."""
        print("Update attribute")
        for atts in atts_val:
            print ("\n atts",atts)
            self._cr.execute(
                "update product_attribute_value set name = json_build_object('en_US', '%s') where id = %s"
                % (atts.get('name'), atts.get('id'))
            )
        self._cr.execute(
            "update product_template_attribute_value set is_qty_required ='t' where maximum_qty > 1"
        )

        products = obj_product.search_read([("id", "!=", False)], fields=['id', 'backorder_config'], order="id")
        print ("\n Update Backorder")
        for product in products:
            print ("\n product", product)
            if product.get('backorder_config') != "no-backorder":
                product_17 = obj_product_17.browse(product.get('id'))
                product_17.write({"allow_backorder": True})

        return True
        

    def update_attribute_value_qty_id(self):
        ppavq_ids = self.env["product.product.attribute.value.qty"].search(
            [], order="id"
        )
        avq_obj = self.env["attribute.value.qty"]
        ptav_obj = self.env["product.template.attribute.value"]
        template_attribute_value_id = False
        for rec in ppavq_ids.filtered(lambda r: r.qty):
            if rec.attr_value_id:
                template_attribute_value_id = ptav_obj.search(
                    [
                        ("product_attribute_value_id", "=", rec.attr_value_id.id),
                        ("product_tmpl_id", "=", rec.product_id.product_tmpl_id.id),
                    ]
                )
                print("\n template_attribute_value_id", template_attribute_value_id)
            attribute_value_qty_id = avq_obj.search(
                [
                    ("product_attribute_id", "=", rec.attr_value_id.attribute_id.id),
                    ("product_attribute_value_id", "=", rec.attr_value_id.id),
                    ("product_tmpl_id", "=", rec.product_id.product_tmpl_id.id),
                    ("qty", "=", rec.qty),
                    (
                        "template_attri_value_id",
                        "=",
                        template_attribute_value_id and template_attribute_value_id.id,
                    ),
                ]
            )
            if attribute_value_qty_id:
                rec.attribute_value_qty_id = attribute_value_qty_id

            else:
                rec.attribute_value_qty_id = avq_obj.create(
                    {
                        "product_attribute_id": rec.attr_value_id.attribute_id.id,
                        "product_attribute_value_id": rec.attr_value_id.id,
                        "product_tmpl_id": rec.product_id.product_tmpl_id.id,
                        "qty": rec.qty,
                        "template_attri_value_id": template_attribute_value_id
                        and template_attribute_value_id.id,
                    }
                )

    @api.model
    def import_product_data(self):
        conn_13 = psycopg2.connect(
            database="odoo13_20241106",
            user="odoo",
            password="odoo",
            host="localhost",
            port="5432",
        )

        cur_13 = conn_13.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur_13.execute(
            "select id, has_configurable_attributes from product_template where has_configurable_attributes = 't' ;"
        )
        product_ids = cur_13.fetchall()
        for product in product_ids:
            _logger.info("\n \n data %s" %(product))
            self._cr.execute("update product_template set config_ok = 't' where id = %s" % (product.get('id'),))

        # cur_13.execute("select code,id,root_id from account_account;")
        # account_ids = cur_13.fetchall()
        # for account in account_ids:
        #     print ("\n =========account",account.get('id'), account.get('code'))
        #     self._cr.execute("update account_account set code = %s where id = %s" % (account.get('code'),account.get('id')))

        # self.env.cr.commit()

        # """FIX Original Customer Request Date?"""
        cur_13.execute(
            "select id, display_commitment_date from sale_order where display_commitment_date is not null"
        )
        sale_orders = cur_13.fetchall()
        for order in sale_orders:
            self._cr.execute(
                "update sale_order set original_request_date = '%s' where id = %s"
                % (
                    order.get("display_commitment_date"),
                    order.get("id"),
                )
            )

        """Move to migration script."""
        # cur_13.execute("""create table temp_ir_property as select * from ir_property where name= 'list_price' and fields_id = 834;""")

        """ Not in user name field non-store in v13
        # cur_13.execute("select * from product_attribute_value")
        # product_att_vals = cur_13.fetchall()
        # att_val_obj = self.env['product.attribute.value']
        # for atts in product_att_vals:
        #     rec = att_val_obj.browse(atts.get('id'))
        #     if not rec.name:
        #         _logger.info("\n \n rec.name %s and old atteibute name %s" %(rec.name, atts.get('name')))
        #     #rec.write({'name': atts.get('name')})
        update product_attribute_value set name = json_build_object('en_US', 'None') where name is null;
        '''No use'''
        # update product_template_attribute_line ptal set is_qty_required ='t' where id in (select ptav.attribute_line_id from product_template_attribute_value ptav where ptav.attribute_line_id = ptal.id and ptav.maximum_qty > 0);
        """
