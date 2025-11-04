from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

import os


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def decrypt_char_field(self, all_data=False):
        KEY = ""
        with open('/home/odoo/decryption.txt', 'r') as file:
            KEY = file.read()
            file.close()
        if not KEY:
            _logger.error("Key Missing")
            return
        KEY = KEY.strip() 
        runningLog = "DECRYPTING CHAR FIELDS V2\n\n"
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        self.env.cr.commit()
        # and tab.table_name = 'res_partner'

        self.env.cr.execute(
            """ 
                SELECT 
                    col.table_name,
                    col.column_name
                FROM information_schema.columns col
                JOIN
                    information_schema.tables tab ON tab.table_schema = col.table_schema
                    AND tab.table_name = col.table_name
                    AND tab.table_type = 'BASE TABLE'
                JOIN
                    ir_model_fields imf ON imf.model = REPLACE(col.table_name, '_', '.') 
                    AND imf.name = col.column_name
                WHERE 
                    col.data_type IN ('character varying', 'character', 'text', '"char"', 'name')
                AND imf.ttype != 'selection'
                AND col.table_schema NOT IN ('information_schema', 'pg_catalog')
                AND col.table_name NOT LIKE 'ir%'
                AND (col.character_maximum_length > 64 OR col.character_maximum_length IS NULL)
                AND tab.table_name NOT LIKE 'mail%'
                AND col.table_name NOT LIKE 'report%'
                --and col.column_name in ('vat')
                -- AND col.table_name in ()
                --AND col.table_name ~* '^[p-zP-Z]'
                AND col.table_name NOT IN ('res_config_settings', 'res_lang','account_invoice_extract_words', 'mrp_bom_line','stock_lot', 'stock_move_line', 'stock_move', 'account_move_line', 'webhook_broadcast_date')
                ORDER BY col.table_name, col.ordinal_position;"""
        )
        table_columns_list_set = self.env.cr.fetchall()

        table_columns_dict = {}
        for table, column in table_columns_list_set:
            if table in table_columns_dict and column not in table_columns_dict[table]:
                table_columns_dict[table].append(column)
            else:
                table_columns_dict[table] = [column]

        # Line use to find the non decrepated data and use to decrpitions
        if all_data:
            table_columns_dict = self.get_non_decrpted_data()

        runningLog += "\n MASTER TABLE GROUPED DICT: %s" % (str(table_columns_dict))
        excluded_tables_columns = {
            "project_task_burndown_chart_report": [
                "date_group_by",
            ],
            "res_partner": [
                "contact_address_complete",
            ],
            "account_move": ["sequence_prefix", "invoice_partner_display_name"],
            "stock_move": ["reporting_extended_name", "reporting_name", 'next_serial', 'origin_system'],
            "account_bank_statement": ['name']
        }
        columns_missing = []
        tables_missing = []
        tables_skipped = []

        def check_column(table, col):
            # all_columns_query = """SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}';""".format(table, col)
            column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');""".format(
                table, col
            )
            self.env.cr.execute(column_exists_query)
            col_exists = self.env.cr.fetchone()

            if col_exists[0]:
                # log("column %s exists in table %s:" % (col, table))
                return True
            else:
                # log("column %s does NOT exist in table %s" % (col, table))
                return False

        for table, columns in table_columns_dict.items():
            runningLog += "\n\n\nGoing Through Table: %s  for Columns: %s" % (
                table,
                str(columns),
            )

            table_exists_query = """SELECT EXISTS (SELECT FROM information_schema.tables WHERE  table_schema = 'public' AND table_name = '{}');""".format(
                table
            )
            column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');"""
            columns_exists = []
            self.env.cr.execute(table_exists_query)
            table_exists = self.env.cr.fetchone()
            if table_exists[0] is False:
                tables_missing.append(table)
                runningLog += "\n Skipping table %s as it doesn't exist in this db" % (
                    table,
                )
                tables_skipped.append(table)
                continue

            for each_col in columns:
                if (
                    table in excluded_tables_columns
                    and each_col in excluded_tables_columns[table]
                ):
                    # runningLog += (
                    #     "\n Skipping column %s from table %s as it is present in the excluded list %s"
                    #     % (each_col, table, excluded_tables_columns)
                    # )
                    continue
                col_query = column_exists_query.format(table, each_col)
                self.env.cr.execute(col_query)
                col_exists = self.env.cr.fetchone()
                if col_exists[0]:
                    columns_exists.append(each_col)
                else:
                    columns_missing.append((table, each_col))
                    # runningLog += (
                    #     "\n Skipping column %s from table %s as it is not present in this db"
                    #     % (each_col, table)
                    # )
            if not columns_exists:
                tables_skipped.append(table)
                # runningLog += (
                #     "\n Skipping table as no columns present: table %s  cloumns %s"
                #     % (table, columns)
                # )
                continue

            if not check_column(table, "id"):
                # runningLog += "\n Skipping table  %s  as it doesn't have id column" % (
                #     table
                # )
                # _logger.info(
                #     "\n Skipping table  %s  as it doesn't have id column" % (table)
                # )
                continue
            batch_size = 100000
            if table in ("project_task"):
                batch_size = 10000
            offset = 0
            if table == 'account_move_line':
                offset = 7400000
            self.env.cr.execute("select count(*) from %s" % (table))
            records = self.env.cr.fetchall()
            _logger.info(
                "\n\nGoing Through Table: %s  for Columns: %s with %s records"
                % (table, str(columns_exists), records[0][0])
            )
            offset_limit = records[0][0] + 1000
            _logger.info("\n offset_limitoffset_limit %s" % (offset_limit))
            while True:
                query = "SELECT id, {}  FROM {} ORDER BY id  LIMIT {} OFFSET {}".format(
                    ", ".join(['"%s"' % c for c in columns_exists]),
                    table,
                    batch_size,
                    offset,
                )
                self.env.cr.execute(query)
                table_data = self.env.cr.fetchall()
                # _logger.info(
                #     "\n\nGoing Through Table: %s  for Columns: %s with %s records"
                #     % (table, str(columns_exists), records[0][0])
                # )
                # if not table_data:
                #     break  # Exit the loop if there are no more records to process
                # print ("\n table_data", table_data)
                if table == "stock_move":
                    if offset > offset_limit:
                        break
                else:
                    if offset > offset_limit:
                        break

                for index, col_data in enumerate(table_data):
                    id = col_data[0]
                    set_data = []

                    for col, col_data in zip(columns_exists, col_data[1:]):
                        if not col_data:
                            # runningLog += "\n Skipped Record with id %s as no field has data to be updated: %s " %(id, col_data)
                            continue

                        # Remove wrapped p tags if present
                        col_data = col_data.lstrip("<p>").rstrip("</p>")

                        if col_data.startswith("\\xc30"):
                            # Check for common elements being inserted and skip if thats the case.
                            if (
                                "<br>" in col_data.lower()
                                or "<br/>" in col_data.lower()
                                or "..." in col_data.lower()
                                or "@" in col_data.lower()
                            ):
                                # runningLog += (
                                #     "\n Skipped Record with id %s in column %s as encrypted data seems corrupted: %s "
                                #     % (id, col, col_data)
                                # )
                                # _logger.info(
                                #     "\n Skipped Record with id %s in  %s.%s as encrypted data seems corrupted: %s "
                                #     % (id, table, col, col_data)
                                # )
                                continue
                            set_data.append((col, col_data))

                    if not set_data:
                        continue
                    set_data_str = ", ".join(
                        [
                            """"%s" = pgp_sym_decrypt('%s', '%s')"""
                            % (col, col_data, KEY)
                            for col, col_data in set_data
                        ]
                    )
                    query = """ UPDATE %s SET %s  where id = %s ;""" % (
                        table,
                        set_data_str,
                        id,
                    )
                    self.env.cr.execute(query)
                    if (index + 1) % 100000 == 0:  # We save every 100k records
                        self.env.cr.commit()
                        _logger.info(
                            "Saved %s records of %s from table %s"
                            % (offset, records[0][0], table)
                        )
                    runningLog = (
                        "\n\nUpdate %s records from table %s with columns %s"
                        % (
                            len(set_data),
                            table,
                            columns_exists,
                        )
                    )
                offset += batch_size

            _logger.info("Comitting changes for table: %s" % table)
            self.env.cr.commit()

        runningLog += "\n\ntables_missing:\n %s" % tables_missing
        runningLog += "\n\ntables_skipped:\n %s" % tables_skipped
        runningLog += "\n\ncolumns_missing:\n %s" % columns_missing
        _logger.info(runningLog)

    def decrypt_number_field(self):
        runningLog = "DECRYPTING NUMERIC FIELDS V2\n\n"

        self.env.cr.execute(
            """SELECT
                    col.table_name,
                    col.column_name
                FROM
                    information_schema.columns col
                JOIN
                    information_schema.tables tab ON tab.table_schema = col.table_schema
                        AND tab.table_name = col.table_name
                        AND tab.table_type = 'BASE TABLE'
                WHERE
                    col.data_type IN ('double precision', 'numeric')
                    AND col.table_schema NOT IN ('information_schema', 'pg_catalog')
                    AND col.table_name NOT LIKE 'ir%'
                    AND col.table_name NOT IN ('uom_uom', 'crm_lead', 'account_invoice_extract_words')
                    AND (
                        col.table_name <> 'dyn_saleorderlines'
                        OR (
                                col.table_name = 'dyn_saleorderlines'
                                AND col.column_name = 'sales_price'
                            )
                    )
                ORDER BY
                    col.table_schema,
                    col.table_name,
                    col.ordinal_position;

                     """
        )

        table_columns_list_set = self.env.cr.fetchall()

        table_columns_dict = {}
        for table, column in table_columns_list_set:
            if table in table_columns_dict:
                table_columns_dict[table].append(column)
            else:
                table_columns_dict[table] = [column]

        def check_columns(table, columns, runningLog):
            # all_columns_query = """SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}';""".format(table, col)
            column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');"""
            col_exists = []
            for col in columns:
                col_query = column_exists_query.format(table, col)
                self.env.cr.execute(col_query)
                is_col_exist = self.env.cr.fetchone()
                runningLog += "\n\nQUERY: %s OUTPUT: %s" % (col_query, is_col_exist)
                if is_col_exist[0]:
                    col_exists.append(col)
                # log("column %s exists in table %s:" % (col, table))
                else:
                    # runningLog += "\ncolumn %s does NOT exist in table %s" % (col, table)
                    _logger.info(
                        "\ncolumn %s does NOT exist in table %s" % (col, table)
                    )
            return col_exists, runningLog

        for table, columns in table_columns_dict.items():
            old_columns = list(columns)
            columns, runningLog = check_columns(table, columns, runningLog)

            runningLog += (
                "\n\nGoing Through Table: %s  for Columns: %s of which these columns are existing: %s"
                % (table, str(old_columns), str(columns))
            )

            _logger.info("\nColumns that exist in table %s: %s" % (table, columns))

            query = "SELECT id, {}  FROM {} ORDER BY id".format(
                ", ".join(['"%s"' % c for c in columns]), table
            )
            self.env.cr.execute(query)
            tab_data = self.env.cr.fetchall()
            _logger.info(
                "\n\nGoing Through Table: %s  for Columns: %s with %s records"
                % (table, str(columns), len(tab_data))
            )

            if not columns:
                runningLog += "\nNo columns, skipping the table %s" % (table)
                continue

            self.env.cr.execute(
                "select is_decimal_encryption from ir_model where model = %s",
                (table.replace("_", "."),),
            )
            result = self.env.cr.fetchone()
            if result and not result[0]:
                _logger.info(
                    "\n \n =============== Skipping %s table as decrypting already done ===================",
                    table,
                )
                continue

            # Optimized: Use batch processing instead of one-by-one updates
            batch_size = 10000
            offset = 0
            
            # Get total record count for progress tracking
            self.env.cr.execute("SELECT COUNT(*) FROM {}".format(table))
            total_records = self.env.cr.fetchone()[0]
            
            _logger.info(
                "\n\nProcessing table %s with %s records in batches of %s"
                % (table, total_records, batch_size)
            )
            
            records_processed = 0
            while offset < total_records:
                query = "SELECT id, {} FROM {} ORDER BY id LIMIT {} OFFSET {}".format(
                    ", ".join(['"%s"' % c for c in columns]), table, batch_size, offset
                )
                
                self.env.cr.execute(query)
                batch_data = self.env.cr.fetchall()
                
                if not batch_data:
                    break
                
                # Prepare batch update queries using proper parameterization
                update_queries = []
                update_params = []
                
                for row_data in batch_data:
                    record_id = row_data[0]
                    set_parts = []
                    values = []
                    
                    for col, col_value in zip(columns, row_data[1:]):
                        if col_value is not None and isinstance(col_value, (int, float)):
                            set_parts.append('"%s" = %%s' % col)
                            values.append(col_value / 5)
                    
                    if set_parts:
                        update_query = 'UPDATE {} SET {} WHERE id = %%s'.format(
                            table, ', '.join(set_parts)
                        )
                        values.append(record_id)
                        update_queries.append(update_query)
                        update_params.append(tuple(values))
                
                # Execute batch updates
                if update_queries and update_params:
                    try:
                        for update_query, params in zip(update_queries, update_params):
                            self.env.cr.execute(update_query, params)
                        
                        records_processed += len(update_params)
                        
                        # Commit every batch
                        self.env.cr.commit()
                        
                        if records_processed % 50000 == 0:
                            _logger.info(
                                "Processed %s/%s records from table %s"
                                % (records_processed, total_records, table)
                            )
                    except Exception as e:
                        runningLog += "\n\nERROR in table %s: %s\nFailed at offset %s" % (
                            table, str(e), offset
                        )
                        _logger.error(runningLog)
                        self.env.cr.rollback()
                        # Continue with next batch instead of breaking
                
                offset += batch_size
            
            # Mark table as decrypted after all records are processed
            try:
                self.env.cr.execute(
                    "UPDATE ir_model SET is_decimal_encryption = 'f' WHERE model = %s",
                    (table.replace("_", "."),),
                )
                self.env.cr.commit()
                _logger.info(
                    "Completed decrypting table %s. Processed %s records."
                    % (table, records_processed)
                )
            except Exception as e:
                _logger.error("Error marking table %s as decrypted: %s" % (table, str(e)))

        _logger.info(runningLog)

    def decrypt_json_field(self):
        KEY = ""
        with open('/home/odoo/decryption.txt', 'r') as file:
            KEY = file.read()
            file.close()
        if not KEY:
            _logger.error("Key Missing")
            return
        KEY = KEY.strip()
        runningLog = "DECRYPTING CHAR FIELDS V2\n\n"
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        self.env.cr.commit()

        self.env.cr.execute(
            """ 
                SELECT 
                    col.table_name,
                    col.column_name
                FROM information_schema.columns col
                JOIN
                    information_schema.tables tab ON tab.table_schema = col.table_schema
                    AND tab.table_name = col.table_name
                    AND tab.table_type = 'BASE TABLE'
                JOIN
                    ir_model_fields imf ON imf.model = REPLACE(col.table_name, '_', '.') 
                    AND imf.name = col.column_name
                JOIN
                    ir_model im on im.model = REPLACE(col.table_name, '_', '.')
                    AND im.transient = 'f'
                WHERE 
                    col.data_type IN ('jsonb')
                AND imf.ttype != 'selection'
                AND col.table_schema NOT IN ('information_schema', 'pg_catalog')
                AND col.table_name NOT LIKE 'ir%'
                AND (col.character_maximum_length > 64 OR col.character_maximum_length IS NULL)
                AND tab.table_name NOT LIKE 'mail%'
                AND col.table_name NOT LIKE 'report%'
                -- AND col.table_name in ('res_company')
                AND col.table_name NOT IN ('res_config_settings', 'res_country_group', 'res_lang', 'knowledge_article', 'stock_rule')
                AND col.column_name NOT LIKE 'analytic%'
                ORDER BY col.table_name, col.ordinal_position;"""
        )

        table_columns_list_set = self.env.cr.fetchall()

        table_columns_dict = {}
        for table, column in table_columns_list_set:
            if table in table_columns_dict and column not in table_columns_dict[table]:
                table_columns_dict[table].append(column)
            else:
                table_columns_dict[table] = [column]

        runningLog += "\n MASTER TABLE GROUPED DICT: %s" % (str(table_columns_dict))

        excluded_tables_columns = {
            "project_task_burndown_chart_report": [
                "date_group_by",
            ],
            "res_partner": [
                "contact_address_complete",
            ],
            "account_move": [
                "sequence_prefix",
            ],
        }
        columns_missing = []
        tables_missing = []
        tables_skipped = []

        def check_column(table, col):
            # all_columns_query = """SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}';""".format(table, col)
            column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');""".format(
                table, col
            )
            self.env.cr.execute(column_exists_query)
            col_exists = self.env.cr.fetchone()

            if col_exists[0]:
                # log("column %s exists in table %s:" % (col, table))
                return True
            else:
                # log("column %s does NOT exist in table %s" % (col, table))
                return False

        for table, columns in table_columns_dict.items():
            runningLog += "\n\n\nGoing Through Table: %s  for Columns: %s" % (
                table,
                str(columns),
            )

            table_exists_query = """SELECT EXISTS (SELECT FROM information_schema.tables WHERE  table_schema = 'public' AND table_name = '{}');""".format(
                table
            )
            column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');"""
            columns_exists = []
            self.env.cr.execute(table_exists_query)
            table_exists = self.env.cr.fetchone()
            if table_exists[0] is False:
                tables_missing.append(table)
                runningLog += "\n Skipping table %s as it doesn't exist in this db" % (
                    table,
                )
                tables_skipped.append(table)
                continue

            for each_col in columns:
                if (
                    table in excluded_tables_columns
                    and each_col in excluded_tables_columns[table]
                ):
                    runningLog += (
                        "\n Skipping column %s from table %s as it is present in the excluded list %s"
                        % (each_col, table, excluded_tables_columns)
                    )
                    continue
                col_query = column_exists_query.format(table, each_col)
                self.env.cr.execute(col_query)
                col_exists = self.env.cr.fetchone()
                if col_exists[0]:
                    columns_exists.append(each_col)
                else:
                    columns_missing.append((table, each_col))
                    runningLog += (
                        "\n Skipping column %s from table %s as it is not present in this db"
                        % (each_col, table)
                    )
            if not columns_exists:
                tables_skipped.append(table)
                runningLog += (
                    "\n Skipping table as no columns present: table %s  cloumns %s"
                    % (table, columns)
                )
                continue

            if not check_column(table, "id"):
                runningLog += "\n Skipping table  %s  as it doesn't have id column" % (
                    table
                )
                _logger.info(
                    "\n Skipping table  %s  as it doesn't have id column" % (table)
                )
                continue
            query = "SELECT id, {}  FROM {} ORDER BY id".format(
                ", ".join(['"%s"' % c for c in columns_exists]), table
            )
            self.env.cr.execute(query)
            table_data = self.env.cr.fetchall()
            _logger.info(
                "\n\nGoing Through Table: %s  for Columns: %s with %s records"
                % (table, str(columns_exists), len(table_data))
            )

            for index, col_data in enumerate(table_data):
                id = col_data[0]
                set_data = []

                for col, col_data in zip(columns_exists, col_data[1:]):
                    if not col_data:
                        # runningLog += "\n Skipped Record with id %s as no field has data to be updated: %s " %(id, col_data)
                        continue
                    col_data = col_data.get("en_US")
                    # Remove wrapped p tags if present
                    col_data = col_data.lstrip("<p>").rstrip("</p>")

                    if col_data.startswith("\\xc30"):
                        # Check for common elements being inserted and skip if thats the case.
                        if (
                            "<br>" in col_data.lower()
                            or "<br/>" in col_data.lower()
                            or "..." in col_data.lower()
                            or "@" in col_data.lower()
                        ):
                            runningLog += (
                                "\n Skipped Record with id %s in column %s as encrypted data seems corrupted: %s "
                                % (id, col, col_data)
                            )
                            _logger.info(
                                "\n Skipped Record with id %s in  %s.%s as encrypted data seems corrupted: %s "
                                % (id, table, col, col_data)
                            )
                            continue
                        set_data.append((col, col_data))

                if not set_data:
                    continue
                set_data_str = ", ".join(
                    [
                        """"%s" = json_build_object('en_US',(concat('',pgp_sym_decrypt('%s', '%s'), '')))"""
                        % (col, col_data, KEY)
                        for col, col_data in set_data
                    ]
                )

                query = """ UPDATE %s SET %s  where id = %s ;""" % (
                    table,
                    set_data_str,
                    id,
                )
                self.env.cr.execute(query)
                if (index + 1) % 100000 == 0:  # We save every 100k records
                    self.env.cr.commit()
                    _logger.info(
                        "Saved %s records of %s from table %s"
                        % (index + 1, len(table_data), table)
                    )
            runningLog += "\n\nUpdate %s records from table %s with columns %s" % (
                len(set_data),
                table,
                columns_exists,
            )

            _logger.info("Comitting changes for table: %s" % table)
            self.env.cr.commit()

        runningLog += "\n\ntables_missing:\n %s" % tables_missing
        runningLog += "\n\ntables_skipped:\n %s" % tables_skipped
        runningLog += "\n\ncolumns_missing:\n %s" % columns_missing
        _logger.info(runningLog)
