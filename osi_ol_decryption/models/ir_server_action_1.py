from odoo import api, models, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)
import psycopg2
import psycopg2.extras
import odoorpc
import re

class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def unistall_module(self):
        module_uninstall_list = ['documents_hr_expense','hr_expense_extract','partner_autocomplete', 'osi_csn_decryption']
        for module in module_uninstall_list:
            self.env['ir.module.module'].search([('name', 'in', module),('state', '=', 'installed')]).button_immediate_uninstall()

    def update_sync_plan_column(self):
        self.env['account.analytic.plan'].sudo().search([])._sync_plan_column()

    def update_check_amount_in_words(self):
        self = self.sudo()
        records = self.env['account.payment'].search([('check_amount_in_words', 'ilike', '\\xc3')])
        for rec in records:
            rec._compute_check_amount_in_words()
    
    def update_internal_notes(self):
        self = self.sudo()
        pattern = r'\\xc30[0-9a-f]+'
        records = self.env['repair.order'].search([('internal_notes', 'ilike', '\\xc3')])
        for rec in records:
            text = rec.internal_notes
            popped_parts = re.findall(pattern, text)
            for part in popped_parts:
                self._cr.execute("select pgp_sym_decrypt(%s,'SQRtYfq2g6');", (part,))
                str = self._cr.fetchone()
                text = text.replace(part, str[0])
                print ("\n\n texttext",text)
            self._cr.execute("update repair_order set internal_notes = %s where id = %s", (text,rec.id))

    def update_acount_move_name(self):
        self = self.sudo()
        records = self.env['account.move.line'].search([('name', 'ilike', '\\xc3')])
        pattern = r'\\xc30[0-9a-f]+'
        for rec in records:
            text = rec.name.replace('\\xc30d0407030232295c1dd558e2f878d2320131219ab000f8a1939e7f06b455412e4f864b8ed926ddf7e8db39feec14b63fb87e5b8f623dfb7d1349dfee3eb0fb1515f8', '$')
            popped_parts = re.findall(pattern, text)
            for part in popped_parts:
                self._cr.execute("select pgp_sym_decrypt(%s,'SQRtYfq2g6');", (part,))
                str = self._cr.fetchone()
                text = text.replace(part, str[0])
            self._cr.execute("update account_move_line set name = %s where id = %s", (text,rec.id))


    def get_non_decrpted_data(self):
        query = """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND data_type IN ('character varying', 'text', 'char')
            AND table_name NOT LIKE 'ir%'
            AND table_name NOT LIKE 'mail%'
            AND table_name NOT LIKE 'report%'
        """
        pattern = '\xc30'
        cursor = self._cr
        cursor.execute(query)
        columns = cursor.fetchall()
        # print ("\n columns", columns)
        results = []
        table_columns_dict = {}
        for table_name, column_name in columns:
            if table_name in ('jira_refresh_wizard','ir_model','migration_job','_mig_134_invl_aml_cond_ref','queue_job', 'mail_message_common', 'import_tc_pdf_wizard', 'crm_lead2dead_partner', 'hubspot_existing', 'hubspot_migration_conf', 'mail_compose_message', 'hubspot_migration', 'hubspot_urls'):
                continue
            if column_name in ('wsserver', 'wsServer', 'dhl_SiteID', 'references','companyid', 'companyId'):
                continue
            # try:
            search_query = f"""
            SELECT count(*) FROM {table_name} WHERE {column_name} ilike '%\\xc30%'
            """
            cursor.execute(search_query)
            data = cursor.fetchall()
            
            if data[0][0]:
                # print ("\n search_query", data)
                _logger.info("\n \n ============= Tabel %s and Colume %s \n \n  ==========", table_name,column_name)
                results.append((table_name, column_name))
                if table_name in table_columns_dict and column_name not in table_columns_dict[table_name]:
                    table_columns_dict[table_name].append(column_name)
                else:
                    table_columns_dict[table_name] = [column_name]
        # print ("\n results=========\n", results)
        _logger.info("\n\n table_columns_dicttable_columns_dict\n %s", table_columns_dict)
        return table_columns_dict

    def update_compute_complete_address(self):
        partner_ids = self.env['res.partner'].search([("contact_address_complete", "!=", ""), '|', ('active', '=', 'f'), ('active', '=', 't')], order="id")
        for partner in partner_ids:
            _logger.info("partner %s", partner.id)
            partner._compute_complete_address()
        
        self._cr.execute('select id,default_supplier_contact from res_partner where default_supplier_contact is not null;')
        datas = self._cr.fetchall()
        for data in datas: 
            self._cr.execute("insert into partner_supplier_contact_rel (partner_id,contact_id) VALUES (%s,%s)", (data[0],data[1]))

    def update_po_contact_ids(self):
        self._cr.execute('select id,contact_id from purchase_order where contact_id is not null;')
        datas = self._cr.fetchall()
        po_obj = self['purchase.order']
        for data in datas:
            self._cr.execute("insert into purchase_order_res_partner_rel (purchase_order_id,res_partner_id) VALUES (%s,%s)", (data[0],data[1]))

        # self = self.sudo()
        # self._cr.execute('select id,contact_id from purchase_order where contact_id is not null;')
        # datas = self._cr.fetchall()
        # po_obj = self['purchase.order']
        # for data in datas:
        #     po = po_obj.browse(data[0])
        #     po.write({'contact_ids': [(6,0, [data[1]])] })


    def update_supplier_invoice_number(self):
        # Fetch supplier invoice numbers and references for in_invoice types
        self._cr.execute("""
            SELECT supplier_invoice_number, ref, id 
            FROM temp_account_move 
            WHERE type = 'in_invoice' AND supplier_invoice_number != ''
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
            database="odoo13_prod_20250128",
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



    # def update_tracking_number(self):
    #     """Move to After Migration Script"""
    #     self._cr.execute(
    #         """UPDATE stock_picking AS sp SET carrier_tracking_ref = tn.number FROM (SELECT picking_id, STRING_AGG(number, ', ') AS number FROM tracking_number GROUP BY picking_id) AS tn WHERE sp.id = tn.picking_id;"""
    #     )

    def odoo_rpc_call_product_weight(self):
        odoo_13 = odoorpc.ODOO("localhost", port=8069, timeout=12000)
        odoo_13.login("odoo13_prod_20250128", "admin", "pw")
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
            # print("\n product_ids", product_ids)
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
        odoo_13.login("odoo13_prod_20250128", "admin", "pw")
        self = self.sudo()
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
    
    def fix_invalid_check_numbers(ctx):
        """
        Fix invalid check numbers from migrated v13 data.
        In v13, some payments had check numbers with non-numeric characters,
        which causes the print check functionality to fail in v17.
        This method finds those payments, sets check_number to 0, and adds
        a chatter message to the payment noting the change.
        """
        # Get payments with a check_number
        payments = ctx.env["account.payment"].sudo().search([("check_number", "!=", False)])

        # Filter payments where check_number is not purely numeric
        invalid_payments = payments.filtered(lambda p: not str(p.check_number).isdigit())

        for payment in invalid_payments:
            old_check_number = payment.check_number  # Store old check number

            # Use raw SQL to directly set check_number to 0
            # SQL is needed as Odoo complains that the existing data is not a Big Int
            ctx.env.cr.execute(
                """
                UPDATE account_payment
                SET check_number = %s
                WHERE id = %s
                """,
                (0, payment.id),
            )

            # Log a chatter message
            message = (
                f"Check number changed from '{old_check_number}' to '0' during "
                "database migration as the original number contained "
                "non-numeric characters."
            )
            payment.message_post(body=message)
    
    def update_product_category(self):
        self = self.sudo()
        self._cr.execute('select id,pim_category from product_template where pim_category is not null;')
        product_ids = self._cr.dictfetchall()
        category_ids = self.env['product.category'].search([('create_date' ,'>=', '2025-01-01')])
        for rec in product_ids:
            if rec.get('pim_category') in ('Product Management, Expansion','Expansion, Product Management'):
                categ_id = category_ids.filtered(lambda l:l.name == 'Expansion')
                self._cr.execute("update product_template set categ_id = %s where id = %s", (categ_id.id, rec.get('id')))
            else:
                categ_id = category_ids.filtered(lambda l:l.name == rec.get('pim_category'))
                self._cr.execute("update product_template set categ_id = %s where id = %s", (categ_id.id, rec.get('id')))
        self._cr.execute('select id,pim_category from product_template where pim_category is null;')
        product_ids = self._cr.dictfetchall()
        all_categ_id = category_ids.filtered(lambda l:l.name == 'All products')
        for rec in product_ids:
            self._cr.execute("update product_template set categ_id = %s where id = %s", (all_categ_id.id, rec.get('id')))
        self._cr.execute("delete from product_category where create_date <= '2025-01-01' and id not in (210,211,1,1232)")
        # self.env['product.category'].search([('create_date' ,'<=', '2025-01-01'), ('id', 'not in', (210,211,1,1232))]).unlink()
        
    def update_shipping_methods(self):
        self = self.sudo()
        self._cr.execute("select * from temp_ir_property_v13_vp where name ='inbound_shipping_method'")
        datas = self._cr.dictfetchall()
        temp_obj = self.env['product.template']
        carrier_ids = self.env['delivery.carrier.multiplier'].search([])
        for data in datas:
            company_id = int(data.get('company_id'))
            res_id = data.get('res_id').split(',')[1]
            value = data.get('value_text')
            carrier_id = carrier_ids.filtered(lambda l: l.carrier == value and l.company_id.id == company_id)
            product_id = temp_obj.browse(int(res_id))
            if not carrier_id and value in ('None', 'Free Shipping'):
                carrier_id = carrier_ids.filtered(lambda l: l.carrier == value)
            if carrier_id:
                product_id.with_company(company_id).write({"carrier_multiplier_id": carrier_id.id})

    def update_total_cost(self):
        company_ids = [1,2]
        product_ids = self.env['product.product'].serach([('tooling_cost', "!=", False)])
        for company in company_ids:
            self = self.with_company(company)
            for rec in product_ids:
                open_review = env["product.price.review"].search(
                    [
                        ("company_id", "=", self.env.company.id),
                        ("product_id", "=", rec.id),
                        # ("state", "=", "validated"),
                    ],
                    limit=1,
                )
                if not open_review:
                    open_review = open_review.create({'product_id': rec.id})
                    open_review.onchange_product_id()
                    
                if open_review:
                    rec.write({"approved_total_cost": open_review.approved_total_cost})

    # No need 
    # def update_attribute_value_qty_id(self):
    #     ppavq_ids = self.env["product.product.attribute.value.qty"].search(
    #         [], order="id"
    #     )
    #     avq_obj = self.env["attribute.value.qty"]
    #     ptav_obj = self.env["product.template.attribute.value"]
    #     template_attribute_value_id = False
    #     for rec in ppavq_ids.filtered(lambda r: r.qty):
    #         if rec.attr_value_id:
    #             template_attribute_value_id = ptav_obj.search(
    #                 [
    #                     ("product_attribute_value_id", "=", rec.attr_value_id.id),
    #                     ("product_tmpl_id", "=", rec.product_id.product_tmpl_id.id),
    #                 ]
    #             )
    #             print("\n template_attribute_value_id", template_attribute_value_id)
    #         attribute_value_qty_id = avq_obj.search(
    #             [
    #                 ("product_attribute_id", "=", rec.attr_value_id.attribute_id.id),
    #                 ("product_attribute_value_id", "=", rec.attr_value_id.id),
    #                 ("product_tmpl_id", "=", rec.product_id.product_tmpl_id.id),
    #                 ("qty", "=", rec.qty),
    #                 (
    #                     "template_attri_value_id",
    #                     "=",
    #                     template_attribute_value_id and template_attribute_value_id.id,
    #                 ),
    #             ]
    #         )
    #         if attribute_value_qty_id:
    #             rec.attribute_value_qty_id = attribute_value_qty_id

    #         else:
    #             rec.attribute_value_qty_id = avq_obj.create(
    #                 {
    #                     "product_attribute_id": rec.attr_value_id.attribute_id.id,
    #                     "product_attribute_value_id": rec.attr_value_id.id,
    #                     "product_tmpl_id": rec.product_id.product_tmpl_id.id,
    #                     "qty": rec.qty,
    #                     "template_attri_value_id": template_attribute_value_id
    #                     and template_attribute_value_id.id,
    #                 }
    #             )

    # @api.model
    # def import_product_data(self):
    #     conn_13 = psycopg2.connect(
    #         database="odoo13_20241106",
    #         user="odoo",
    #         password="odoo",
    #         host="localhost",
    #         port="5432",
    #     )

        # cur_13 = conn_13.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        "Move config_ok to After decryption script"
        # cur_13.execute(
        #     "select id, has_configurable_attributes from product_template where has_configurable_attributes = 't' ;"
        # )
        # product_ids = cur_13.fetchall()
        # for product in product_ids:
        #     _logger.info("\n \n data %s" %(product))
        #     self._cr.execute("update product_template set config_ok = 't' where id = %s" % (product.get('id'),))

        # cur_13.execute("select code,id,root_id from account_account;")
        # account_ids = cur_13.fetchall()
        # for account in account_ids:
        #     print ("\n =========account",account.get('id'), account.get('code'))
        #     self._cr.execute("update account_account set code = %s where id = %s" % (account.get('code'),account.get('id')))

        # self.env.cr.commit()

        # """FIX Original Customer Request Date? Move to After Decrption Script"""
        # cur_13.execute(
        #     "select id, display_commitment_date from sale_order where display_commitment_date is not null"
        # )
        # sale_orders = cur_13.fetchall()
        # for order in sale_orders:
        #     self._cr.execute(
        #         "update sale_order set original_request_date = '%s' where id = %s"
        #         % (
        #             order.get("display_commitment_date"),
        #             order.get("id"),
        #         )
        #     )

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
