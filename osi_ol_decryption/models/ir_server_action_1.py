from odoo import api, models, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)
import psycopg2
import psycopg2.extras
import odoorpc
import re
import openpyxl

class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def update_saleorder_substate(self):
        substate_ids = self.env['base.substate'].search([('model', '=', 'sale.order')])    
        complete = substate_ids.filtered(lambda l : l.name == 'Complete')
        self._cr.execute("update sale_order set substate_id = %s where detailed_state in ('done_partial', 'done',)", (complete.id,))
        review = substate_ids.filtered(lambda l : l.name == 'Legacy Order Review')
        self._cr.execute("update sale_order set substate_id = %s where detailed_state in ('review')", (review.id,))
        waiting = substate_ids.filtered(lambda l : l.name == 'Waiting')
        self._cr.execute("update sale_order set substate_id = %s where detailed_state in ('sale')", (waiting.id,))
        production = substate_ids.filtered(lambda l : l.name == 'In Production')
        self._cr.execute("update sale_order set substate_id = %s where detailed_state in (''in_production','invoiced','invoiced_partial','ship_hold','ship_ready'')", (production.id,))
        
        
    def configure_account_sepa_direct_debit(self):
        self.env["ir.module.module"].search(
                [("name", "=", 'configure_account_sepa_direct_debit'), ("state", "!=", "installed")]
            ).button_immediate_install()

    def create_onlogic_locations_and_route(self):
        self = self.sudo()
        # --- Step 1: Create Base View Locations ---
        locations_to_create_us = [
            # US
            ("Primary", "Stock", "view"),
            ("Overstock", "WH", "view"),
        ]
        locations_to_create_eu = [
            # EU
            ("Primary", "Stock", "view"),
            ("Overstock", "EU", "view"),
        ]

        for name, parent_name, usage in locations_to_create_us:
            parent = self.env["stock.location"].search(
                [("name", "=", parent_name), ("company_id", "=", 1)], limit=1
            )
            if not parent:
                continue  

            if not self.env["stock.location"].search(
                [("name", "=", name), ("company_id", "=", 1)], limit=1
            ):
                loaction = self.env["stock.location"].create(
                    {
                        "name": name,
                        "location_id": parent.id,
                        "usage": usage,
                        "company_id": 1,
                    }
                )

                data = self.env["ir.model.data"].sudo().create(
                    {
                        "name": f"stock_location_{name.lower()}",
                        "model": "stock.location",
                        "module": "__setup__",
                        "res_id": loaction.id,
                        "noupdate": True,
                    }
                )
                
        for name, parent_name, usage in locations_to_create_eu:
            parent = self.env["stock.location"].search(
                [("name", "=", parent_name), ("company_id", "=", 2)], limit=1
            )
            if not parent:
                continue 

            if not self.env["stock.location"].search(
                [("name", "=", name), ("company_id", "=", 2)], limit=1
            ):
                loaction = self.env["stock.location"].create(
                    {
                        "name": name, 
                        "location_id": parent.id,
                        "usage": usage,
                        "company_id": 2,
                    }
                )

                self.env["ir.model.data"].sudo().create(
                    {
                        "name": f"stock_location_eu_{name.lower()}",
                        "model": "stock.location",
                        "module": "__setup__",  
                        "res_id": loaction.id,
                        "noupdate": True,
                    }
                )

        # --- Step 3: Create Route in OnLogic US ---

        route_us = self.env["stock.route"].create(
            {
                "name": "Overstock Replenishment",
                "product_selectable": False,
                "company_id": 1,
            }
        )

        op_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "internal"),
                ("company_id", "=", 1),
                ("name", "=", "Internal Transfers"),
            ],
            limit=1,
        )

        # Find Locations
        source_loc = self.env["stock.location"].search(
            [("name", "=", "Overstock"), ("company_id", "=", 1)], limit=1
        )
        dest_loc = self.env["stock.location"].search(
            [("name", "=", "Primary"), ("company_id", "=", 1)], limit=1
        )

        self.env["stock.rule"].create(
            {
                "name": "Pull from Overstock",
                "route_id": route_us.id,
                "action": "pull",  # Pull From
                "picking_type_id": op_type.id,
                "location_src_id": source_loc.id,
                "location_dest_id": dest_loc.id,
                "procure_method": "make_to_stock",  # Supply Method = Take From Stock
                "company_id": 1,
            }
        )

        op_type = self.env["stock.picking.type"].search(
            [
                ("code", "=", "internal"),
                ("company_id", "=", 2),
                ("name", "=", "Internal Transfers"),
            ],
            limit=1,
        )

        # Find Locations
        source_loc = self.env["stock.location"].search(
            [("name", "=", "Overstock"), ("company_id", "=", 2)], limit=1
        )
        dest_loc = self.env["stock.location"].search(
            [("name", "=", "Primary"), ("company_id", "=", 2)], limit=1
        )

        route_eu = self.env["stock.route"].create(
            {
                "name": "Overstock Replenishment",
                "product_selectable": False,
                "company_id": 2,
            }
        )

        self.env["stock.rule"].create(
            {
                "name": "Pull from Overstock",
                "route_id": route_eu.id,
                "action": "pull",  # Pull From
                "picking_type_id": op_type.id,
                "location_src_id": source_loc.id,
                "location_dest_id": dest_loc.id,
                "procure_method": "make_to_stock",  # Supply Method = Take From Stock
                "company_id": 2,
            }
        )
        
        file_path = "/home/odoo/odoo17/odoo/addons/osi_ol_decryption/osi_ol_decryption/data/US_and_EU_Stock_Locations.xlsx"
        wb = openpyxl.load_workbook(filename=file_path, data_only=True)
        count = 1
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            if count == 1:
                company = 1
                overstock = self.env.ref('__setup__.stock_location_overstock')
                primary = self.env.ref('__setup__.stock_location_primary')
            else:
                company = 2
                overstock = self.env.ref('__setup__.stock_location_eu_overstock')
                primary = self.env.ref('__setup__.stock_location_eu_primary')

            for row in sheet.iter_rows(min_row=3):
                name = row[0].value
                parent = row[1].value
                print ("\n parent", parent, name)
                if parent in ('WH/Stock/Primary', 'EU/Stock/Primary'):
                    loaction = primary.id
                if parent in ('EU/Overstock','WH/Overstock'):
                    loaction = overstock.id
                if loaction and name:
                    id = self.env['stock.location'].search([('name', 'ilike', name), ('company_id','=', company)]).id
                    
                    if id:
                        self._cr.execute("update stock_location set location_id = %s where id = %s ", (loaction, id))
                        self._cr.commit()
            
            count +=1

    
    def payment_method_update(self):
        "Update the Payment Method's"
        self = self.sudo()
        payment_ids = []
        cr = self._cr
        payment_methods = {
            1: "Paypal",
            8: "Stripe",
            2: "Bank Transfer",
            3: "Zero Payment",
            4: "Manual",
            5: "Check",
            6: "Paypal",
            7: "Custom",
            10: "Net Terms",
            9: "Credit Card",
            11: "iDEAL",
            12: "Bancontact",
            13: "GiroPay",
            14: "Sofort",
            15: "Maestro",
            16: "Credit Card Prepayment"
        }
        bank_transfer = self.env.ref("payment.payment_method_bank_transfer")
        payment_ids.append(bank_transfer.id)
        paypal = self.env.ref("payment.payment_method_paypal")
        payment_ids.append(paypal.id)
        sofort = self.env.ref("payment.payment_method_sofort")
        payment_ids.append(sofort.id)
        self._cr.execute("update payment_method set active = 't' where id in %s", (tuple(payment_ids),))
        self._cr.commit()
        new_payment_data = self.env['payment.method'].search([])
        
        self._cr.execute("select id,payment_method_id from sale_order where payment_method_id is not null")
        sale_order_data = self._cr.fetchall()
        for sale in sale_order_data:
            payment = False
            name = ''
            cr.execute("select id,sub_method_id,method_id from sale_order_payment_method where id = %s", (sale[1],))
            data = cr.dictfetchone()
            
            if data.get('sub_method_id') != None:
                name = payment_methods.get(data.get('sub_method_id'))
            else:
                name = payment_methods.get(data.get('method_id'))
            
            # if name == 'Custom':
            #     payment = new_payment_data.filtered(lambda l: l.name == 'Custom')
            if name == 'Net Terms':
                payment = new_payment_data.filtered(lambda l: l.name == 'Payment Terms')
            elif name in ('Credit Card Prepayment', 'Credit Card'):
                payment = new_payment_data.filtered(lambda l: l.name == 'Card')
            else:
                payment = new_payment_data.filtered(lambda l: l.name == name)
            
            if payment:
                cr.execute("update sale_order set sale_payment_method_id = %s where id = %s", (payment.id, sale[0] ))

    def mig_scrap_reasons(self):
        self = self.sudo()
        self._cr.execute("select name from failure_reason group by name;")
        failure_reason_ids = self._cr.fetchall()
        compnay_ids = self.env['res.company'].search([('id', 'in', (1,2))])
        for company in compnay_ids:
            for resaon in failure_reason_ids:
                if company.id == 2:
                    location = 117  # EU/SRMA Staging
                else:
                    location = 116  # WH/SRMA Staging
                
                scrap_reason = self.env['scrap.reason.code'].create({
                    'name': resaon[0],
                    'company_id': company.id,
                    'location_id': location
                })
        for company in compnay_ids:
            reason_ids = self.env['scrap.reason.code'].search([('company_id', '=', company.id)])
            for reason in reason_ids:
                self._cr.execute("""UPDATE stock_scrap AS ss SET reason_code_id = %s 
                                    FROM failure_reason AS fr 
                                    WHERE fr.id = ss.failure_reason 
                                    AND fr.name = %s 
                                    AND ss.company_id = %s;""", (reason.id,reason.name, company.id))

    def update_product_category_account(self):
        self = self.sudo()
        category_ids = self.env["product.category"].search([])
        acc_product = self.env.ref("lgx_account.41100-02")
        acc_materials = self.env.ref("lgx_account.51105-02")
        us_compnay = self.env.ref("base.main_company")
        for catg in category_ids:
            catg.with_company(us_compnay).write(
                {
                    "property_stock_account_input_categ_id": acc_product.id,
                    "property_stock_account_output_categ_id": acc_materials.id,
                }
            )

        acc_product = self.env.ref("lgx_account.41100-03")
        acc_materials = self.env.ref("lgx_account.51105-03")
        eu_compnay = self.env.ref("ol_base.onlogic_eu")
        for catg in category_ids:
            catg.with_company(eu_compnay).write(
                {
                    "property_stock_account_input_categ_id": acc_product.id,
                    "property_stock_account_output_categ_id": acc_materials.id,
                }
            )
        
        # update the journal Data
        self._cr.execute("update account_journal set active = 'f' where id = 162;") #Purchase Journal USD
        self._cr.execute("update account_journal set active = 'f' where id = 158;") #Purchase Refund Journal USD
        self._cr.execute("update account_journal set active = 'f' where id = 270;") #Vendor Bills
        self._cr.execute("update account_journal set name = json_build_object('en_US', 'Purchase Refund Journal') where id = 215;") # Purchase Refund Journal USD
        self._cr.execute("update account_journal set name = json_build_object('en_US', 'Purchase Journal') where id = 214;") # Purchase Journal EUR


    def delete_account(self):
        self = self.sudo()
        file_path = "/home/odoo/odoo17/odoo/addons/osi_ol_decryption/osi_ol_decryption/data/account_delete.xlsx"
        wb = openpyxl.load_workbook(filename=file_path, data_only=True)
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            count = 1  
            self._cr.execute("alter table account_account disable trigger all;")
            self._cr.commit()
            for row in sheet.iter_rows(min_row=2):
                code = row[0].value
                name = row[1].value
                company = row[4].value
                if name in ('Cash', 'Bank'):
                    continue
                account = self.env['account.account'].search([
                    ('code', '=', code),
                    ('name', '=', name),
                    ('company_id.name', '=', company)
                ], limit=1)
                if account:
                    self._cr.execute('delete from account_account where id = %s', (account.id,))
                    

            self._cr.execute("alter table account_account enable trigger all;")
            self._cr.commit()


    def update_accounts_from_excel(self):
        import openpyxl
        def format_decimal(value):
            # Ensure it's a float or decimal
            try:
                value = float(value)
            except ValueError:
                return value  # or raise an error

            # Split integer and decimal part
            integer_part = int(value)
            decimal_part = round(value - integer_part, 2)

            if decimal_part > 0:
                # Remove leading "0." from decimal and replace "." with "-"
                decimal_str = str(value).split(".")[1]
                return f"{integer_part}-{decimal_str}"
            else:
                return str(integer_part) 
        # Load workbook
        self = self.sudo()

        file_path = "/home/odoo/odoo17/odoo/addons/osi_ol_decryption/osi_ol_decryption/data/Odoo_17_GL_Remap.xlsx"

        wb = openpyxl.load_workbook(filename=file_path, data_only=True)
        companies = self.env['res.company'].search([])
        company_names = {c.name for c in companies}

        total_updates = 0

        for sheet_name in wb.sheetnames:
            sheet_company = sheet_name
            if sheet_company not in company_names:
                # print ("\n ==============sheet_name=====", sheet_name)
                if sheet_company == 'Greenfield Real Estate':
                    sheet_company = 'Greenfield Real Estate LLC'
                elif sheet_company == 'Interlogic':
                    sheet_company = 'Interlogic, Inc.'
                else:
                    continue  # Skip if sheet name is not a company
            company = self.env['res.company'].search([('name', '=', sheet_company)], limit=1)
            print ("\n company==========",company)
            sheet = wb[sheet_name]
            updated_count = 0

            # Read rows starting from row 3 (header is in row 2)
            for row in sheet.iter_rows(min_row=3):
                old_code = str(row[7].value)       # Column H (index 7)
                old_name = row[8].value       # Column I (index 8)
                old_type = row[9].value       # Column J (index 9)
                new_code = str(row[14].value)      # Column O (index 14)
                new_name = row[15].value      # Column P (index 15)
                new_type = row[16].value      # Column Q (index 16)
                reconcil = row[19].value       # Column T (index 19)
                tag_string = row[20].value    # Column U (index 20)
                not_deprecated = row[24].value  #Column x (Index 24)

                # if old_code.endswith(".0"):
                #     old_code = old_code.rstrip("0").rstrip(".") 
                
                # if new_code.endswith(".0"):
                #     new_code = new_code.rstrip("0").rstrip(".")
                old_code = format_decimal(old_code)
                # new_code = format_decimal(new_code) 
                if not old_code:
                    continue
                print ("\n old_code:-", old_code, "old_name:-", old_name, "old_type:-", old_type, "new_code:-", new_code, "new_name:-", new_name, "new_type:-", new_type)
                # Search account within company
                account = self.env['account.account'].search([
                    ('code', '=', old_code),
                    ('name', '=', old_name),
                    ('company_id', '=', company.id)
                ], limit=1)

                if not account and new_code == 'None':
                    continue
                # Prepare tag IDs
                tag_ids = []
                if tag_string:
                    tag_names = [t.strip() for t in tag_string.split(',')]
                    for tag_name in tag_names:
                        tag = self.env['account.account.tag'].search([('name', '=', tag_name)], limit=1)
                        if not tag:
                            self.env['account.account.tag'].create({'name': tag_name, 'applicability': 'accounts'})
                        if tag:
                            tag_ids.append(tag.id)

                # Check for changes
                diffs = {}
                selection = dict(account._fields['account_type'].selection)
                if account:
                    if new_code and account.code != str(new_code):
                        diffs['code'] = new_code
                    if new_name and account.name != new_name:
                        diffs['name'] = new_name
                    if new_type and old_type and old_type != new_type:
                        if new_type == 'Non-current liabilities':
                            new_type = 'Non-current Liabilities'
                        if new_type == '#N/A':
                            continue

                        keys_found = [key for key, value in selection.items() if value == new_type]
                        diffs['account_type'] = keys_found[0]
                    if tag_ids and set(account.tag_ids.ids) != set(tag_ids):
                        diffs['tag_ids'] = [(6, 0, tag_ids)]
                    if not_deprecated:
                        diffs['deprecated'] = False

                    # if diffs:
                    #     print ("\n --------------write----------", diffs)
                    #     if diffs.get('code') == '11019A.02':
                    #         continue
                    #     account.with_company(company).write(diffs)
                    #     updated_count += 1
                    if diffs:
                        print("\n --------------write----------", diffs)
                        vals = []
                        params = []
                        vals.append("reconcile = %s")
                        params.append(reconcil)
                        if 'code' in diffs:
                            vals.append("code = %s")
                            params.append(diffs['code'])
                        if 'name' in diffs:
                            vals.append("name = json_build_object(%s, %s)")
                            params.append('en_US')
                            params.append(diffs['name'])
                        if 'account_type' in diffs:
                            vals.append("account_type = %s")
                            params.append(diffs['account_type'])
                        if 'deprecated' in diffs:
                            params.append("f")
                            vals.append(('deprecated = %s'))
                        if vals:
                            params.append(account.id)
                            
                            query = f"""
                                UPDATE account_account
                                SET {', '.join(vals)}
                                WHERE id = %s
                            """
                            print ("\n query", query, "\n params", params)
                            self.env.cr.execute(query, tuple(params))

                        if 'tag_ids' in diffs:
                            # Update tags in many2many manually
                            self.env.cr.execute(
                                "DELETE FROM account_account_account_tag WHERE account_account_id = %s",
                                (account.id,))
                            for tag_id in tag_ids:
                                self.env.cr.execute(
                                    "INSERT INTO account_account_account_tag (account_account_id, account_account_tag_id) VALUES (%s, %s)",
                                    (account.id, tag_id)
                                )

                        updated_count += 1

                else:
                    account = self.env['account.account'].with_company(company).search([
                    ('code', '=', new_code),
                    ('name', '=', new_name)], limit=1)
                    if not account:
                        print ("\n new_typenew_type==========", new_type)
                        if new_type == 'Non-current liabilities':
                            new_type = 'Non-current Liabilities'
                        keys_found = [key for key, value in selection.items() if value == new_type]
                        
                        diffs = {'name': new_name, 'code': new_code, 'account_type': keys_found[0], 'company_id': company.id, 'tag_ids': [(6, 0, tag_ids)]}
                        print ("\n --------------create----------", diffs)
                        if (diffs.get('code') == '21440.09' and diffs.get('company_id') == 9) or (diffs.get('code') == '99999.1' and diffs.get('company_id') == 3) or (diffs.get('code') == '28' and diffs.get('company_id') == 1):
                            continue
                        self.env['account.account'].with_company(company).create(diffs)
        
        self.env['account.account'].with_user(1).search([])._compute_account_root()
        

    def run_hot_ar(self):
        _logger.info("===============run_hot_ar====================")
        hot_ar_cron = self.env.ref("ol_account_hot_ar.compute_hot_ar_cron")
        hot_ar_cron.method_direct_trigger()

    def unistall_module(self):
        _logger.info("===============rununistall_module_hot_ar====================")
        module_uninstall_list = [
            "documents_hr_expense",
            "hr_expense_extract",
            "partner_autocomplete",
            "osi_ol_decryption",
            "account_avatax",
            "account_avatax_geolocalize",
            "account_avatax_sale",
            "account_avatax_stock"
        ]
        for module in module_uninstall_list:
            self.env["ir.module.module"].search(
                [("name", "=", module), ("state", "=", "installed")]
            ).button_immediate_uninstall()

    def update_sync_plan_column(self):
        _logger.info("===============update_sync_plan_column====================")
        self.env["account.analytic.plan"].sudo().search([])._sync_plan_column()

    def update_check_amount_in_words(self):
        _logger.info("===============update_check_amount_in_words====================")
        self = self.sudo()
        records = self.env["account.payment"].search(
            [("check_amount_in_words", "ilike", "\\xc3")]
        )
        for rec in records:
            rec._compute_check_amount_in_words()

    def update_internal_notes(self):
        _logger.info("===============update_internal_notes====================")
        self = self.sudo()
        pattern = r"\\xc30[0-9a-f]+"
        records = self.env["repair.order"].search(
            [("internal_notes", "ilike", "\\xc3")]
        )
        for rec in records:
            text = rec.internal_notes
            popped_parts = re.findall(pattern, text)
            for part in popped_parts:
                self._cr.execute("select pgp_sym_decrypt(%s,'SQRtYfq2g6');", (part,))
                str = self._cr.fetchone()
                text = text.replace(part, str[0])
                # print ("\n\n texttext",text)
            self._cr.execute(
                "update repair_order set internal_notes = %s where id = %s",
                (text, rec.id),
            )

    def update_acount_move_name(self):
        _logger.info("===============update_acount_move_name====================")
        self = self.sudo()
        records = self.env["account.move.line"].search([("name", "ilike", "\\xc3")])
        pattern = r"\\xc30[0-9a-f]+"
        for rec in records:
            text = rec.name.replace(
                "\\xc30d0407030232295c1dd558e2f878d2320131219ab000f8a1939e7f06b455412e4f864b8ed926ddf7e8db39feec14b63fb87e5b8f623dfb7d1349dfee3eb0fb1515f8",
                "$",
            )
            popped_parts = re.findall(pattern, text)
            for part in popped_parts:
                self._cr.execute("select pgp_sym_decrypt(%s,'SQRtYfq2g6');", (part,))
                str = self._cr.fetchone()
                text = text.replace(part, str[0])
            self._cr.execute(
                "update account_move_line set name = %s where id = %s", (text, rec.id)
            )

        records = self.env["account.move"].search(
            [("invoice_partner_display_name", "ilike", "\\xc30")]
        )
        count = 0        
        for rec in records:
            self._cr.execute("update account_move set invoice_partner_display_name = %s where id = %s", (rec.partner_id.display_name, rec.id))
            count += 1
            if count == 10000:
                count = 0
                self._cr.commit()
            # rec.write({"invoice_partner_display_name": rec.partner_id.display_name})

    def get_non_decrpted_data(self):
        query = """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND data_type IN ('character varying', 'text', 'char')
            AND table_name NOT LIKE 'ir%'
            AND table_name NOT LIKE 'mail%'
            AND table_name NOT LIKE 'report%'
        """
        pattern = "\xc30"
        cursor = self._cr
        cursor.execute(query)
        columns = cursor.fetchall()
        # print ("\n columns", columns)
        results = []
        table_columns_dict = {}
        for table_name, column_name in columns:
            if table_name in (
                "jira_refresh_wizard",
                "ir_model",
                "migration_job",
                "_mig_134_invl_aml_cond_ref",
                "queue_job",
                "mail_message_common",
                "import_tc_pdf_wizard",
                "crm_lead2dead_partner",
                "hubspot_existing",
                "hubspot_migration_conf",
                "mail_compose_message",
                "hubspot_migration",
                "hubspot_urls",
                "stock_report",
                'mrp_bom_line',
                'stock_lot',
                'stock_move_line',
                'stock_move',
                'account_move_line',
                

            ):
                continue
            if column_name in (
                "wsserver",
                "wsServer",
                "dhl_SiteID",
                "references",
                "companyid",
                "companyId",
            ):
                continue
            # try:
            search_query = f"""
            SELECT count(*) FROM {table_name} WHERE {column_name} ilike '%\\xc30%'
            """
            cursor.execute(search_query)
            data = cursor.fetchall()

            if data[0][0]:
                # print ("\n search_query", data)
                _logger.info(
                    "\n \n ============= Tabel %s and Colume %s \n \n  ==========",
                    table_name,
                    column_name,
                )
                results.append((table_name, column_name))
                if (
                    table_name in table_columns_dict
                    and column_name not in table_columns_dict[table_name]
                ):
                    table_columns_dict[table_name].append(column_name)
                else:
                    table_columns_dict[table_name] = [column_name]
        # print ("\n results=========\n", results)
        _logger.info(
            "\n\n table_columns_dicttable_columns_dict\n %s", table_columns_dict
        )
        return table_columns_dict
    
    def update_compute_complete_address(self, batch_size=50000):
        _logger.info("===============update_compute_complete_address====================")
        offset = 0
        lang_key = 'en_US'
        while True:
            self.env.cr.execute(f"""
                WITH to_update AS (
                    SELECT rp.id AS partner_id,
                        TRIM(BOTH ',' FROM
                            COALESCE(rp.street || ',', '') ||
                            COALESCE(rp.zip || ' ','') ||
                            COALESCE(rp.city || ',', '') ||
                            COALESCE(st.name || ',', '') ||
                            COALESCE(ct.name->>'{lang_key}', '')
                        ) AS new_address
                    FROM res_partner rp
                    LEFT JOIN res_country_state st ON rp.state_id = st.id
                    LEFT JOIN res_country ct ON rp.country_id = ct.id
                    ORDER BY rp.id
                    OFFSET {offset}
                    LIMIT {batch_size}
                )
                UPDATE res_partner rp
                SET contact_address_complete = to_update.new_address
                FROM to_update
                WHERE rp.id = to_update.partner_id
            """)
            self.env.cr.commit()
            _logger.info("Committed batch at offset %s", offset)

            # Stop when fewer than batch_size rows were processed
            if self.env.cr.rowcount < batch_size:
                break
            offset += batch_size

        _logger.info("=============== Finished Bulk Update ====================")

        self._cr.execute(
            "select id,default_supplier_contact from res_partner where default_supplier_contact is not null;"
        )
        datas = self._cr.fetchall()
        for data in datas:
            self._cr.execute(
                "insert into partner_supplier_contact_rel (partner_id,contact_id) VALUES (%s,%s)",
                (data[0], data[1]),
            )
    
    def update_po_contact_ids(self):
        _logger.info("===============update_po_contact_ids====================")
        self._cr.execute(
            "select id,contact_id from purchase_order where contact_id is not null;"
        )
        datas = self._cr.fetchall()

        for data in datas:
            self._cr.execute(
                "insert into purchase_order_res_partner_rel (purchase_order_id,res_partner_id) VALUES (%s,%s)",
                (data[0], data[1]),
            )

    def update_supplier_invoice_number(self):
        _logger.info("===============update_supplier_invoice_number====================")
        # Fetch supplier invoice numbers and references for in_invoice types
        self._cr.execute(
            """
            SELECT supplier_invoice_number, ref, id 
            FROM temp_account_move 
            WHERE type = 'in_invoice' AND supplier_invoice_number != ''
        """
        )
        move_ids = self._cr.dictfetchall()

        duplicate_supplier_numbers = set()

        for move in move_ids:
            supplier_invoice_number = move.get("supplier_invoice_number")
            ref = move.get("ref")
            move_id = move.get("id")

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
                new_ref = (
                    f"{ref}-{supplier_invoice_number}"
                    if ref
                    else supplier_invoice_number
                )

            self._cr.execute(
                "UPDATE account_move SET ref = %s WHERE id = %s", (new_ref, move_id)
            )
    
    def update_product_tax_code(self):
        _logger.info("========== Starting tax_code_id update ==========")
        self._cr.execute("""
            WITH tax_map AS (
                SELECT
                    split_part(res_id, ',', 2)::int AS template_id,
                    split_part(value_reference, ',', 2)::int AS tax_code_id
                FROM temp_ir_property_v13_vp
                WHERE name = 'tax_code_id' AND company_id = 1
            )
            UPDATE product_template pt
            SET tax_code_id = tm.tax_code_id
            FROM tax_map tm
            WHERE pt.id = tm.template_id
        """)
        self._cr.commit()
        _logger.info("========== tax_code_id update completed ==========")
    
    
    def odoo_rpc_call_product_weight(self):
        """Created the pre_computed sql file and will update the record from After Decryption File"""
        _logger.info("===============odoo_rpc_call_product_weight====================")
        odoo_13 = odoorpc.ODOO("localhost", port=8069, timeout=12000)
        odoo_13.login("odoo13_prod", "admin", "pw")
        obj_product = odoo_13.env["product.product"]
        final_count = 172723
        limit = 10000
        offset = 0
        while True:
            product_ids = obj_product.search_read(
                [
                    ("id", "not in", [112677, 147811, 92960, 96905, 135649, 143682]),
                    "|",
                    ("active", "=", True),
                    ("active", "=", False),
                ],
                fields=["id", "weight", "product_tmpl_id"],
                order="id",
                offset=offset,
                limit=limit,
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
        _logger.info("===============odoo_rpc_call====================")
        odoo_13 = odoorpc.ODOO("localhost", port=8069, timeout=12000)
        odoo_13.login("odoo13_prod", "admin", "pw")
        self = self.sudo()
        obj_product = odoo_13.env["product.template"]
        obj_att_value = odoo_13.env["product.attribute.value"]
        obj_v17_att_value = odoo_13.env["product.attribute.value"]

        obj_product_17 = self.env["product.template"]

        """FIX work_location in Employee Move to sh file"""

        # employee_obj = self.env["hr.employee"]
        # work_location_obj = self.env["hr.work.location"]
        # obj_employee = odoo_13.env["hr.employee"]
        # employee_ids = obj_employee.search_read(
        #     [("work_location", "!=", False)], fields=["id", "work_location"], order="id"
        # )
        # for emp in employee_ids:
        #     work_id = work_location_obj.search(
        #         [("name", "=", emp.get("work_location"))], limit=1
        #     )
        #     if work_id:
        #         self._cr.execute(
        #             "update hr_employee set work_location_id = %s where id = %s"
        #             % (work_id.id, emp.get("id"))
        #         )

        """FIX Payment Team Data missing"""

        obj_sale_order = odoo_13.env["sale.order"]
        sale_order_ids = obj_sale_order.search_read(
            [("id", "!=", False)], fields=["id", "payment_term_id"], order="id"
        )

        for sales in sale_order_ids:
            if sales.get("payment_term_id"):
                self._cr.execute(
                    "update sale_order set payment_term_id = %s where id = %s"
                    % (
                        sales.get("payment_term_id")[0],
                        sales.get("id"),
                    )
                )

        atts_val = obj_att_value.search_read([], fields=["id", "name"], order="id")
        """Remove record rule from v13 of company before run."""
        # print("Update attribute")
        for atts in atts_val:
            self._cr.execute(
                "update product_attribute_value set name = json_build_object('en_US', '%s') where id = %s"
                % (atts.get("name"), atts.get("id"))
            )
        self._cr.execute(
            "update product_template_attribute_value set is_qty_required ='t' where maximum_qty > 1"
        )

        products = obj_product.search_read(
            [("id", "!=", False)], fields=["id", "backorder_config"], order="id"
        )

        for product in products:
            if product.get("backorder_config") != "no-backorder":
                product_17 = obj_product_17.browse(product.get("id"))
                product_17.write({"allow_backorder": True})

        return True

    
    def fix_invalid_check_numbers(self):
        _logger.info("===============fix_invalid_check_numbers====================")
        """
        Fix invalid check numbers from migrated v13 data.
        In v13, some payments had check numbers with non-numeric characters,
        which causes the print check functionality to fail in v17.
        This method finds those payments, sets check_number to 0, and adds
        a chatter message to the payment noting the change.
        """
        # Get payments with a check_number
        payments = (
            self.env["account.payment"].sudo().search([("check_number", "!=", False)])
        )

        # Filter payments where check_number is not purely numeric
        invalid_payments = payments.filtered(
            lambda p: not str(p.check_number).isdigit()
        )

        for payment in invalid_payments:
            old_check_number = payment.check_number  # Store old check number

            # Use raw SQL to directly set check_number to 0
            # SQL is needed as Odoo complains that the existing data is not a Big Int
            self.env.cr.execute(
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
        _logger.info("===============update_product_category====================")
        self = self.sudo()
        self._cr.execute(
            "select id,pim_category from product_template where pim_category is not null;"
        )
        product_ids = self._cr.dictfetchall()
        category_ids = self.env["product.category"].search(
            ["|", ("create_date", ">=", "2025-01-01"), ("id", "=", 1)]
        )
        attribute_ids = self.env["attribute.set"].search([])
        for rec in product_ids:
            if rec.get("pim_category") in (
                "Product Management, Expansion",
                "Expansion, Product Management",
            ):
                categ_id = category_ids.filtered(lambda l: l.name == "Expansion")

                attribute_id = attribute_ids.filtered(lambda a: a.name == "Expansion")
                self._cr.execute(
                    "update product_template set categ_id = %s,attribute_set_id = %s where id = %s",
                    (categ_id.id, attribute_id.id, rec.get("id")),
                )
            elif rec.get('pim_category') == 'Computers, Panel PCs':
                categ_id = category_ids.filtered(lambda l: l.name == "Computers")
                attribute_id = attribute_ids.filtered(lambda a: a.name == "Computers")
                self._cr.execute(
                    "update product_template set categ_id = %s,attribute_set_id = %s where id = %s",
                    (categ_id.id, attribute_id.id, rec.get("id")),
                )
            elif rec.get('pim_category') == 'Cases, Computers':
                categ_id = category_ids.filtered(lambda l: l.name == "Cases")
                attribute_id = attribute_ids.filtered(lambda a: a.name == "Cases")
                self._cr.execute(
                    "update product_template set categ_id = %s,attribute_set_id = %s where id = %s",
                    (categ_id.id, attribute_id.id, rec.get("id")),
                )
            else:
                categ_id = category_ids.filtered(
                    lambda l: l.name == rec.get("pim_category")
                )

                attribute_id = attribute_ids.filtered(
                    lambda a: a.name == rec.get("pim_category")
                )
                self._cr.execute(
                    "update product_template set categ_id = %s, attribute_set_id = %s where id = %s",
                    (categ_id.id, attribute_id.id, rec.get("id")),
                )

        self._cr.execute(
            "select id,pim_category from product_template where pim_category is null;"
        )
        product_ids = self._cr.dictfetchall()
        all_categ_id = category_ids.filtered(lambda l: l.name == "All products")
        for rec in product_ids:
            self._cr.execute(
                "update product_template set categ_id = %s where id = %s",
                (all_categ_id.id, rec.get("id")),
            )

        self._cr.execute(
            "delete from product_category where create_date <= '2025-01-01' and id not in (210,211,1,1232)"
        )

        # self.env['product.category'].search([('create_date' ,'<=', '2025-01-01'), ('id', 'not in', (210,211,1,1232))]).unlink()

    def update_shipping_methods(self):
        _logger.info("===============update_shipping_methods====================")
        self = self.sudo()
        self._cr.execute(
            "select * from temp_ir_property_inbound_shipping_method where name ='inbound_shipping_method'"
        )
        datas = self._cr.dictfetchall()
        temp_obj = self.env["product.template"]
        carrier_ids = self.env["delivery.carrier.multiplier"].search([])
        for data in datas:
            company_id = int(data.get("company_id"))
            res_id = data.get("res_id").split(",")[1]
            value = data.get("value_text")
            carrier_id = carrier_ids.filtered(
                lambda l: l.carrier == value and l.company_id.id == company_id
            )
            product_id = temp_obj.browse(int(res_id))
            if not carrier_id and value in ("None", "Free Shipping"):
                carrier_id = carrier_ids.filtered(lambda l: l.carrier == value)
            if carrier_id:
                product_id.with_company(company_id).write(
                    {"carrier_multiplier_id": carrier_id.id}
                )

    def update_total_cost(self):
        _logger.info("===============update_total_cost====================")
        self = self.sudo()
        company_ids = [1, 2]
        product_ids = self.env["product.product"].search(
            [("tooling_cost", "!=", False)]
        )
        for company in company_ids:
            self = self.with_company(company)
            for rec in product_ids:
                open_review = self.env["product.price.review"].search(
                    [
                        ("company_id", "=", self.env.company.id),
                        ("product_id", "=", rec.id),
                        # ("state", "=", "validated"),
                    ],
                    limit=1,
                )
                if not open_review:
                    open_review = open_review.create({"product_id": rec.id})
                    open_review.onchange_product_id()

                if open_review:
                    rec.write({"approved_total_cost": open_review.approved_total_cost})
        product_ids = self.env["product.product"].search(
            [("length", ">", 0),('width', '>', 0), ('height', '>', 0) ]
        )
        for product in product_ids:
            product._onchange_volume()

    def create_stock_putway_rule(self):
        _logger.info("===============create_stock_putway_rule====================")
        # OSI Task: https://osi.mavenlink.com/workspaces/44078089/#tracker/923588804
        # Putaway Rule Migration Creation Server Action
        
        from odoo.tools import convert_csv_import, file_open
        pathname = "osi_ol_decryption/data/stock.location.csv"
        with file_open(pathname, 'rb', env=self.env) as fp:
            convert_csv_import(self.env, 'osi_ol_decryption', pathname, fp.read(), {}, 'update', False)

        cr = self.env.cr
        v13dataquery = """  
            SELECT res_id, id, name, value_text
            FROM temp_ir_property_row_rack_case 
            WHERE company_id = 1 
            AND (name = 'loc_row' OR name = 'loc_rack' OR name = 'loc_case') 
            GROUP BY res_id, id, name, value_text;
        """
        _logger.info("\n\n\n\nPutaway Rule Migration Server Action Start")
        cr.execute(v13dataquery)
        v13Datas = cr.fetchall()
        migrationData = [{}]
        result = {}
        for data in v13Datas:
            # product_id = int(data[0].split(',')[1])
            product_id = data[0]
            location = data[2]
            if product_id not in result:
                result[product_id] = []
            # Append the location value to the list of locations for the current product_id
            result[product_id].append(location)
        final_output = []

        for res_id, locations in result.items():
            # Sort locations so 'loc_row' comes first, followed by 'loc_rack' and 'loc_case'
            sorted_locations = sorted(
                locations, key=lambda x: ["loc_row", "loc_rack", "loc_case"].index(x)
            )

            # Join the locations with underscores
            final_output.append({res_id: "-".join(sorted_locations)})
            select_query = """SELECT name,value_text from temp_ir_property_row_rack_case WHERE company_id = 1 and res_id = %s and (name = 'loc_row' OR name = 'loc_rack' OR name = 'loc_case');"""
            cr.execute(select_query, (res_id,))
            datas = cr.fetchall()
            location_str = ""
            for data in datas:
                if data[0] == "loc_row":
                    location_str = data[1]
                if data[0] == "loc_rack":
                    location_str = location_str + "_" + data[1]
                if data[0] == "loc_case":
                    location_str = location_str + "_" + data[1]

            odoo_location = self.env["stock.location"].search(
                [("complete_name", "ilike", location_str)]
            )
            if len(odoo_location) == 1:
                product_tmpl_id = int(res_id.split(",")[1])
                product_id = self.env["product.product"].search(
                    [("product_tmpl_id", "=", product_tmpl_id)]
                )
                in_location = self.env.ref("stock.stock_location_stock")
                putaway_rule = self.env["stock.putaway.rule"].create(
                    {
                        "location_in_id": in_location.id,
                        "product_id": product_id.id,
                        "category_id": product_id.categ_id.id,
                        "location_out_id": odoo_location.id,
                        "company_id": self.env.ref("base.main_company").id,
                    }
                )
                # _logger.info("\n\n\n\nPutaway Rule Migration Server Action=>===%s==%s===%s==%s",product_id,location_str,odoo_location,odoo_location.name)
                cr.commit()
        cr.execute("drop table temp_ir_property_row_rack_case;")
        _logger.info("\n\n\n\nPutaway Rule Migration Server Action Done")
    
    
    def set_product_candidates(self):
        """
        Until the product categories and candidates get hashed out, we are going to enable
        all the candidate fields on the products and set the 'ok' fields product based on state.
        """
        table_name = "product_template"
        fields_to_update = [
            "candidate_bom",
            "candidate_component_manufacture",
            "candidate_manufacture",
            "candidate_purchase",
            "candidate_sale",
            "candidate_sale_confirm",
            "candidate_ship",
        ]

        # Build the SET clause
        set_clause = ", ".join(f"{field} = TRUE" for field in fields_to_update)

        # Execute raw SQL
        self.env.cr.execute(
            f"""
            UPDATE {table_name}
            SET {set_clause}
        """
        )

        self.env.cr.execute("""
            UPDATE
                product_template pt
            SET 
                candidate_bom = pc.candidate_bom,
                candidate_component_manufacture = pc.candidate_component_manufacture,
                candidate_manufacture = pc.candidate_manufacture,
                candidate_purchase = pc.candidate_purchase,
                candidate_sale = pc.candidate_sale,
                candidate_sale_confirm = pc.candidate_sale_confirm,
                candidate_ship = pc.candidate_ship
            FROM
                product_category pc
            WHERE
                pt.categ_id = pc.id;
            """)

        # Set 'ok' fields based on candidate and state
        self.env.cr.execute(
            """
        UPDATE product_template pt
        SET
            sale_ok = ps.approved_sale AND pt.candidate_sale,
            sale_ok_confirm = ps.approved_sale_confirm AND pt.candidate_sale_confirm,
            mrp_ok = ps.approved_mrp AND pt.candidate_manufacture,
            mrp_component_ok = ps.approved_component_mrp AND pt.candidate_component_manufacture,
            bom_ok = ps.approved_bom AND pt.candidate_bom,
            purchase_ok = ps.approved_purchase AND pt.candidate_purchase,
            ship_ok = ps.approved_ship AND pt.candidate_ship
        FROM product_state ps
        WHERE pt.product_state_id = ps.id
        """
        )
        product_ids = self.env['product.template'].sudo().search([('phantom_bom_id', '!=', False), ("purchase_ok", "=", True)])
        product_ids.write({'purchase_ok': False, 'candidate_purchase': False})
        product_ids = self.env['product.template'].sudo().search([("categ_id.name", "in", ["Systems", "Computers", "Panel PCs"]), ("purchase_ok", "=", True)])
        product_ids.write({'purchase_ok': False, "candidate_purchase": False})
            

    def uninstall_old_module(self):
        _logger.info("===============uninstall_old_module====================")
        env = self.env
        module_uninstall_list = [
            "ls_account_bank_statement",
            "ls_account_cost_center",
            "ls_auto_reconciliation",
            "ls_positive_pay",
            "ls_assembly_stage_lookup",
            "ls_auth_oauth",
            "ls_business_intelligence",
            "ls_delivery_shipping_views",
            "ls_blind_dropship",
            "ls_check_printing",
            "ls_crm_hud",
            "ls_crm_notes",
            "ls_customer_bulk_change",
            "ls_custom_stock_status",
            "ls_data_migration",
            "ls_secret_field",
            "ls_delivery_tnt",
            "ls_delivery_configurator",
            "ls_tax_and_shipping_api",
            "ls_delivery_custom",
            "ls_delivery_dhl",
            "ls_delivery_fedex",
            "ls_delivery_phantom_kit",
            "ls_split_shipments",
            "ls_delivery_ups",
            "ls_graphql_product",
            "ls_dev_tools",
            "ls_expedite_opportunity_report",
            "ls_elastic_apm",
            "ls_fraud_detection",
            "ls_gcp_attachment",
            "ls_graphql_account",
            "ls_graphql_corrective_action",
            "ls_graphql_customer",
            "ls_mrp_api",
            "ls_graphql_mrp",
            "ls_graphql_project",
            "ls_graphql_purchase",
            "ls_graphql_rma",
            "ls_graphql_stock",
            "ls_graphql_user",
            "ls_helpdesk_jira",
            "ls_helpdesk_itsupport",
            "ls_jira_search",
            "ls_jira_integration",
            "ls_ma_report",
            "ls_monitoring",
            "ls_mrp_plan_multiple",
            "ls_mrp_reverse",
            "ls_elastic_apm",
            "ls_mrp_traveler",
            "ls_mrp_views",
            "ls_multicompany",
            "ls_partner_chart",
            "ls_picking_transfer_multiple",
            "ls_production_automation_repair_link",
            "ls_project",
            "ls_rma_email",
            "ls_query_builder",
            "ls_quote_configuration",
            "ls_sale_metrics",
            "ls_sale_stock_status",
            "ls_scrap_replacement",
            "ls_stock_account",
            "ls_stock_constrained_sku",
            "ls_stock_serial_wizard",
            "ls_supplier_return",
            "ls_tier_pricing",
            "ls_trackjs",
            "ls_webhooks_graphql",
            "ls_webhooks_test",
            "ls_webhooks",
            "ls_web_report_viewer",
            "ls_wip_count",
            "ls_wip_report",
            "ls_workflow_map",
            "ls_sale_order_edits",
            "ls_api",
            "ls_payment_sources",
            "ls_uuid",
            "ls_customer",
            "ls_payment_netterms",
            "ls_payment_stripe",
            "ls_vendor_lead_time_report",
            "ls_account_avatax",
            "ls_lead_time",
            "ls_portal",
            "ls_mail",
            "ls_invoice_reminders",
            "ls_account_reports",
            "ls_vat_report",
            "ls_pdf_reports",
            "ls_translations",
            "ls_inventory_turnover_report",
            "ls_terms_and_conditions",
            "ls_tracking_number",
            "ls_serial_number_report",
            "ls_scrap",
            "ls_sale_booking",
            "ls_sale_verticals",
            "ls_sale_operations",
            "ls_sale_archive_partners",
            "ls_rma_repair_link",
            "ls_ddmrp",
            "ls_sale_hold",
            "ls_product_expected_date",
            "ls_inbound_shipping",
            "ls_account_payment",
            "ls_mrp_label",
            "ls_repair",
            "ls_base_vat",
            "ls_persistent_notes",
            "ls_hts",
            "ls_mrp_transfer_serial",
            "ls_auto_stock_allocation",
            "ls_order_status",
            "ls_product_tooling_cost",
            "ls_inventory_report",
            "ls_rma",
            "ls_queue_job",
            "ls_delivery_account",
            "ls_delivery_wizard",
            "ls_internal_purchase_request",
            "ls_payment_method",
            "ls_coupon_code",
            "ls_delivery",
            "ls_phantom_kit_enhancements",
            "ls_stock_inventory",
            "ls_templates",
            "ls_product_system_stock",
            "ls_product_procurement",
            "ls_public_attachments",
            "ls_public_content",
            "ls_product_manufacturer",
            "ls_product_location",
            "ls_gcp_base",
            "ls_corrective_action",
            "ls_production_automation",
            "ls_sale_compensation",
            "ls_sale_workflow",
            "ls_rush_order",
            "ls_public_content",
            "ls_crm",
            "ls_crm_event_log",
            "ls_product_classification",
            "ls_auto_invoice",
            "ls_account",
            "ls_check_framework",
            "ls_phantom_kits",
            "ls_purchase",
            "ls_ui",
            "ls_sale_holidays",
            "ls_partner",
            "ls_inventory",
            "ls_graphql_sale",
            "ls_graphql",
            "ls_sale_email",
            "ls_sale",
            "ls_base",
            "ls_product",
            "ls_stock",
            "ls_stock_available_date",
            "ls_link_objects",
            "ls_mrp",
            "ls_assembly_stage_lookup",
            "email_template_qweb",
            "hr_recruitment_sms",
            "ls_product_compatibility",
            "ls_product_configurator",
            "ls_product_operations_category",
            "ls_product_tariff",
            "ls_shipping_data",
            "ls_stock_loadcsv",
            "osi_encryption",
            "partner_email_check",
            "session_redis",
            "web_dialog_size",
            "web_environment_ribbon",
            "web_ir_actions_act_view_reload",
            "web_tree_many2one_clickable",
            "web_widget_bokeh_chart",
            "ls_delivery_ups_rest",
            "avatax_fiscal_position_us"
        ]

        data_list = env["ir.model.data"].search(
            [("module", "in", module_uninstall_list)]
        )
        for data in data_list:
            if data.model in (
                "ir.ui.view",
                "ir.ui.menu",
                "ir.rule",
                "ir.cron",
                "ir.model.fields",
                "ir.model.access",
                "ir.model.fields.selection",
                "res.groups",
                "ir.actions.act_window",
                "ir.actions.act_window.view",
                "ir.actions.report",
                "ir.model",
            ):
                table = data.model.replace(".", "_")
                _logger.info(data.read([]))
                if table in ("ir_ui_view", "ir_ui_menu"):
                    self._cr.execute("alter table %s DISABLE TRIGGER ALL" % (table,))
                    # otable = data.name.split('model_')[1]
                    # if otable and len(otable.split('_report')) == 1:

                    self._cr.execute(
                        "delete from %s where id = %s"
                        % (
                            table,
                            data.res_id,
                        )
                    )
                    self._cr.execute("alter table %s enable TRIGGER ALL" % (table,))

                if table in ("ir_cron"):
                    action_ids = env["ir.actions.server"].search(
                        [("model_id", "=", data.res_id)]
                    )
                    if action_ids:
                        for action in action_ids:
                            self._cr.execute(
                                "delete from %s where ir_actions_server_id = %s"
                                % (
                                    "ir_cron",
                                    action.id,
                                )
                            )
                        action_ids.unlink()
                
                if table in (
                    "ir_actions_act_window",
                    "ir_actions_act_window_view",
                    "ir_actions_report",
                ):
                    env[data.model].browse(data.res_id).unlink()
                
                elif table in ('res_groups'):
                    self._cr.execute("alter table %s DISABLE TRIGGER ALL" % (table,))
                    self._cr.execute("update ir_model_access set  group_id = null where group_id = %s" % (data.res_id,))
                    self._cr.execute("delete from %s where id = %s" % (table, data.res_id))
                    self._cr.execute("alter table %s enable TRIGGER ALL" % (table,))
                    
                else:
                    if table != "ir_model":
                        
                        self._cr.execute(
                            "delete from %s where id = %s"
                            % (
                                table,
                                data.res_id,
                            )
                        )

                self._cr.execute(
                    "delete from %s where id = %s"
                    % (
                        "ir_model_data",
                        data.id,
                    )
                )

        data_list = (
            env["ir.model.data"]
            .search(
                [("module", "in", module_uninstall_list), ("model", "not ilike", "ir")]
            )
            .unlink()
        )
        module_uninstall_list += ["account_avatax","account_avatax_sale"]
        for module in module_uninstall_list:
            self._cr.execute(
                "update ir_module_module set state='to remove' where name='%s'"
                % (module)
            )

        # env['ir.module.module'].search([('name', 'in', module_uninstall_list),('state', '=', 'installed')]).button_immediate_uninstall()

    def install_new_module(self):
        modules = [
            "job_cost_estimate_customer",
            "mrp_batch",
            "ol_crm",
            "ol_crm_estimate",
            "ol_crm_mrp_plm",
            "ol_crm_purchase_request",
            "ol_crm_sale_blanket_order",
            "ol_exception",
            "ol_job_cost_estimate_customer",
            "ol_mrp_plm_cancel",
            "ol_mrp_plm_purchase",
            "ol_mrp_plm_substate",
            "ol_mrp_sale_price_rollup",
            "ol_partner_stage",
            "ol_product_configurator",
            "ol_product_pricing_review",
            "ol_product_profile",
            "ol_product_state",
            "ol_purchase",
            "ol_purchase_3way_match",
            "ol_purchase_request_estimate",
            "ol_rush_order",
            "ol_account",
            "ol_sale",
            "ol_sale_blanket_order",
            "ol_sale_stock_tags",
            "ol_scrap_reason_code",
            "ol_stock",
            "ol_tier_validation",
            "osi_ap_addresses",
            "osi_blanket_order_mps",
            "product_configurator",
            "product_configurator_sale",
            "product_configurator_mrp_quantity",
            "product_configurator_restriction_policy",
            "product_manufacturer",
            "purchase_order_line_menu",
            "web_m2x_options",
            "web_m2x_options_manager",
            "sale_product_approval_purchase",
            "sale_product_approval_mrp",
            "base_exception",
            "server_action_mass_edit",
            "purchase_deposit",
            "web_company_color",
            "product_attribute_set",
            "osi_check_alignment",
            "ol_mrp_traveler",
            "ol_product_classification",
            "ol_product_operations_category",
            "ol_stock_constrained_sku",
            "ol_mrp_plm",
            "hr_attendance",
            "osi_downpayment_taxes",
            "stock_inventory",
            "ol_sale_substate",
            "ol_account_reports",
            "ol_base",
            "ol_job_cost_estimator_tier_validation",
            "ol_mrp_plm_tier_validation",
            "ol_product_configurator_stock",
            "ol_product_configurator_sale_template",
            "ol_product_tariff",
            "ol_product_tooling",
            "ol_sale_mrp_tags",
            "ol_sale_template",
            "ol_sale_email",
            "ol_sale_optional_product",
            "ol_mrp_bom_rebuild",
            "ol_sale_cost_workup",
            "purchase_backorder",
            "sale_order_line_menu",
            "base",
            "web",
            "account_accountant",
            "account_consolidation",
            "approvals",
            "calendar",
            "contact",
            "crm",
            "delivery_fedex",
            "delivery_ups",
            "delivery_usps",
            "documents",
            "helpdesk",
            "hr",
            "hr_contract",
            "hr_expense",
            "hr_skills",
            "knowledge",
            "mail",
            "maintenance",
            "mrp",
            "mrp_plm",
            "planning",
            "project",
            "project_todo",
            "purchase",
            "quality_control",
            "repair",
            "room",
            "sale_management",
            "sale_subscription",
            "stock",
            "stock_barcode",
            "timesheet_grid",
            "account_avatax_oca",
            "account_move_tier_validation",
            "auditlog",
            "base_tier_validation",
            "base_tier_validation_formula",
            "base_user_role",
            "base_user_role_company",
            "mail_debrand",
            "partner_identification",
            "partner_stage",
            "partner_tier_validation",
            "product_configurator_mrp",
            "product_configurator_mrp_component",
            "sale_blanket_order_tier_validation",
            "sale_product_approval_stock",
            "stock_request",
            "stock_request_mrp",
            "stock_request_picking_type",
            "stock_request_stage",
            "stock_request_submit",
            "sale_automatic_workflow",
            "sale_backorder",
            "sale_blanket_order",
            "sale_exception",
            "sale_product_approval",
            "sale_tier_validation",
            "scrap_reason_code",
            "sh_product_customer_code",
            "oi_login_as",
            "ol_warranty",
            "ol_sale_tier_validation",
            "ol_sale_lead_time",
            "ol_sale_booking",
            "ol_sale_blanket_order_lead_time",
            "ol_product_reporting_category",
            "ol_mrp",
            "ol_helpdesk_repair_batch",
            "ol_pim",
            "ol_product",
            "ol_account_hot_ar",
            "ol_credit_limit",
            "ol_rma_supplier",
            "ol_fraud_detection",
	    "account_sepa",
            "ol_sale_order_inspection",
        ]

        for module in modules:
            self.env["ir.module.module"].search(
                [("name", "=", module), ("state", "!=", "installed")]
            ).button_immediate_install()


