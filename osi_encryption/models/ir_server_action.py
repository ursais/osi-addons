# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

import os


class IrActionsServer(models.Model):
    _inherit = "ir.actions.server"

    def encrypt_char_fields(self):
        KEY = os.environ.get("KEY_ENCY_DESCY")
        runningLog = "ENCRYPTING CHAR FIELDS V2\n\n"

        # self.env.cr.execute("ALTER TABLE  res_partner  ALTER COLUMN fax TYPE varchar(200)")
        # self.env.cr.execute("ALTER TABLE  account_incoterms  ALTER COLUMN code TYPE varchar(200)")
        # self.env.cr.execute("ALTER TABLE  account_account  ALTER COLUMN code TYPE varchar(200)")
        # table_columns_list_set = [('res_partner','name'),('res_partner','ref'),('res_partner','street'),('res_partner','street2'),('res_partner','zip'),('res_partner','city'),('res_partner','email'),('res_partner','display_name')]
        # and tab.table_name = 'res_partner'

        # Index drop

        self.env.cr.execute(
            "drop index IF EXISTS  account_move_line_partner_id_ref_idx;"
        )
        self.env.cr.execute("drop index IF EXISTS  account_move_line_ref_index;")
        self.env.cr.commit()
        self.env.cr.execute(
            """ SELECT 
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
                AND col.table_name NOT IN ('res_config_settings', 'res_country', 'res_country_group', 'res_groups', 'res_lang', 'res_users')
                AND (
                      col.table_name <> 'dyn_customer'
                      OR (col.table_name = 'dyn_customer' AND col.column_name IN ('js_first_name', 'js_middle_name', 'js_last_name', 'phone', 'js_street_1', 'email'))
                  )
                AND (
                  col.table_name <> 'dyn_saleorderlines'
                      OR (col.table_name = 'dyn_saleorderlines' AND col.column_name IN ('sales_id', 'delivery_state', 'sales_responsible', 'name'))
                  )
                AND (
                      col.table_name <> 'dyn_continuity_history'
                      OR (col.table_name = 'dyn_continuity_history' AND col.column_name IN ('prnt_so', 'delivery_name', 'delivery_street', 'sales_responsible', 'item_name', 'price') )
                  )
                ORDER BY col.table_name, col.ordinal_position;
                """
        )

        table_columns_list_set = self.env.cr.fetchall()

        table_columns_dict = {}
        for table, column in table_columns_list_set:
            if table in table_columns_dict and column not in table_columns_dict[table]:
                table_columns_dict[table].append(column)
            else:
                table_columns_dict[table] = [column]

        _logger.info(str(table_columns_dict))
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        self.env.cr.commit()

        runningLog += "\n MASTER TABLE GROUPED DICT: %s" % (str(table_columns_dict))

        for table, columns in table_columns_dict.items():
            runningLog += "\n\nGoing Through Table: %s  for Columns: %s" % (
                table,
                str(columns),
            )
            # REMOVE LIMIT FROM PROD RUN

            query = "SELECT id, {}  FROM {} ORDER BY id".format(
                ", ".join(['"%s"' % c for c in columns]), table
            )
            self.env.cr.execute(query)
            table_data = self.env.cr.fetchall()

            _logger.info(
                "\n\nGoing Through Table: %s  for Columns: %s with %s records"
                % (table, str(columns), len(table_data))
            )

            rec_updated_ids = []
            for col_data in table_data:
                id = col_data[0]
                set_data = []

                for col, col_data in zip(columns, col_data[1:]):
                    if col_data:
                        set_data.append(
                            (
                                col,
                                col_data,
                            )
                        )
                        rec_updated_ids.append(id)

                if not set_data:
                    runningLog += (
                        "\n Skipped Record with id %s as no field has data to be updated: %s "
                        % (id, col_data)
                    )
                    continue
                set_data_str = ",".join(
                    [
                        """"%s" = pgp_sym_encrypt('%s', '%s')"""
                        % (col, col_data.replace("'", "''"), KEY)
                        for col, col_data in set_data
                    ]
                )

                # try:
                query = """ UPDATE %s SET %s  where id = %s ;""" % (
                    table,
                    set_data_str,
                    id,
                )
                self.env.cr.execute(query)

                # except Exception as e:
                # runningLog += "\n \n ERROR: %s \n WHEN RUNNING QUERY: \n%s\n\n" % (
                #     e,
                #     query,
                # )
                # _logger.info(runningLog)
            # , rec_updated_ids
            _logger.info(
                "Updated data for %s records from table %s with id:"
                % (len(rec_updated_ids), table)
            )
        self.env.cr.commit()
        _logger.info(runningLog)

    def decrypt_char_field(self):
        KEY = os.environ.get("KEY_ENCY_DESCY")
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
                AND col.table_name NOT IN ('res_config_settings', 'res_country', 'res_country_group', 'res_groups', 'res_lang', 'res_users')
                AND (
                      col.table_name <> 'dyn_customer'
                      OR (col.table_name = 'dyn_customer' AND col.column_name IN ('js_first_name', 'js_middle_name', 'js_last_name', 'phone', 'js_street_1', 'email'))
                  )
                AND (
                  col.table_name <> 'dyn_saleorderlines'
                      OR (col.table_name = 'dyn_saleorderlines' AND col.column_name IN ('sales_id', 'delivery_state', 'sales_responsible', 'name'))
                  )
                AND (
                      col.table_name <> 'dyn_continuity_history'
                      OR (col.table_name = 'dyn_continuity_history' AND col.column_name IN ('prnt_so', 'delivery_name', 'delivery_street', 'sales_responsible', 'item_name', 'price') )
                  )
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
                        """"%s" = pgp_sym_decrypt('%s', '%s')""" % (col, col_data, KEY)
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

    def encrypting_numeric_fields(self):
        runningLog = "ENCRYPTING NUMERIC FIELDS V2\n\n"

        self.env.cr.execute(
            """
                SELECT
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
                    AND col.table_name NOT IN ('uom_uom', 'crm_lead')
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
        runningLog += "\nTABLE GROUPED DICT: %s" % (str(table_columns_dict))

        for table, columns in table_columns_dict.items():
            runningLog += "\n\nGoing Through Table: %s  for Columns: %s" % (
                table,
                str(columns),
            )
            _logger.info(runningLog)

            # REMOVE LIMIT FROM PROD RUN
            query = "SELECT id, {}  FROM {} ORDER BY id".format(
                ", ".join(columns), table
            )

            self.env.cr.execute(query)
            table_data = self.env.cr.fetchall()

            runningLog += "\n\nUpdating %s records in Table: %s for Columns: %s" % (
                len(table_data),
                table,
                str(columns),
            )

            for col_data in table_data:
                id = col_data[0]

                set_data = []
                for col, col_data in zip(columns, col_data[1:]):
                    if col_data:
                        set_data.append(
                            (
                                col,
                                isinstance(col_data, (int, float))
                                and col_data * 5
                                or col_data,
                            )
                        )

                if not set_data:
                    runningLog += (
                        "\n Skipped Record with id %s as no field has data to be updated: %s "
                        % (id, col_data)
                    )
                    continue

                set_data_str = ",".join(
                    ["%s = %s" % (col, col_data) for col, col_data in set_data]
                )
                try:
                    query = """ UPDATE %s SET %s where id = %s ;""" % (
                        table,
                        set_data_str,
                        id,
                    )
                    self.env.cr.execute(query)
                    self.env.cr.commit()
                except Exception as e:
                    runningLog += "\n \n ERROR: %s \n WHEN RUNNING QUERY: %s" % (
                        e,
                        query,
                    )
                    _logger.info(runningLog)
                    break

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
                    AND col.table_name NOT IN ('uom_uom', 'crm_lead')
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

            if not columns:
                runningLog += "\nNo columns, skipping the table %s" % (table)
                continue

            # REMOVE LIMIT FROM PROD RUN
            query = "SELECT id, {}  FROM {} ORDER BY id".format(
                ", ".join(columns), table
            )

            self.env.cr.execute(query)
            table_data = self.env.cr.fetchall()
            runningLog += "\n\nUpdating %s records in Table: %s for Columns: %s" % (
                len(table_data),
                table,
                str(columns),
            )
            for col_data in table_data:
                id = col_data[0]

                set_data = []
                for col, col_data in zip(columns, col_data[1:]):
                    if col_data and isinstance(col_data, (int, float)):
                        set_data.append((col, col_data / 5))

                if not set_data:
                    runningLog += (
                        "\n Skipped Record with id %s as no field has data to be updated: %s "
                        % (id, col_data)
                    )
                    continue

                set_data_str = ",".join(
                    ["%s = %s" % (col, col_data) for col, col_data in set_data]
                )
                try:
                    query = """ UPDATE %s SET %s where id = %s ;""" % (
                        table,
                        set_data_str,
                        id,
                    )
                    self.env.cr.execute(query)
                    self.env.cr.commit()
                except Exception as e:
                    runningLog += "\n \n ERROR: %s \n WHEN RUNNING QUERY: %s" % (
                        e,
                        query,
                    )
                    _logger.info(runningLog)
                    break

        self.env.cr.commit()

        _logger.info(runningLog)
