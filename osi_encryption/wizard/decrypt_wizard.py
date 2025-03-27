# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import os
import logging
import time
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DecryptWizard(models.TransientModel):
    _name = "decrypt.lines.wizard"
    _description = "decrypt Lines Wizard"

    key = fields.Char(
        "Encryption Key",
        help="Enter the encryption key that was used to encrypt the data.",
    )
    char_line_ids = fields.Many2many(
        "encrypt.line",
        string="Lines to Decrypt",
        help="These are the items that are going to be decrypted. "
        "If they are not encrypted, excluded or don't contain columns then they will be skipped.",
    )
    file_location = fields.Char(
        "Files Location",
        default="/home/odoo/",
        help="If CSV's were created during sanitization, enter the file location where the CSV files exist from when sanitization was run.",
    )
    show_key = fields.Boolean("Show Key", compute="_show_fields_compute")
    show_file_location = fields.Boolean("Show File Location", compute="_show_fields_compute")
    create_csv = fields.Boolean(
        "Use CSV Files to Restore",
        default=True,
        help="If CSV files were created during sanitization, then use them to restore since the temp tables would have been auto dropped.",
    )

    @api.depends('char_line_ids')
    def _show_fields_compute(self):
        for rec in self:
            rec.show_key = False
            rec.show_file_location = False
            if any(line.line_action == "encrypt_decrypt" for line in rec.char_line_ids):
                rec.show_key = True
            if any(line.line_action == "sanitize_unsanitize" for line in rec.char_line_ids):
                rec.show_file_location = True

    def unsanitize_char_data(self):
        sanitized_lines = self.char_line_ids.filtered(lambda x: x.line_action == "sanitize_unsanitize")
        for line in sanitized_lines:
            if line.line_action == "sanitize_unsanitize" and line.state not in (
                "encrypted",
                "decrypted",
                "unsanitized",
                "excluded",
            ):
                runningLog = "\n\nDESANITIZING DATA: "
                start_time = time.time()
                table = line.table_id.model.replace(".", "_")
                temp_table = "temp_" + table

                # Check if CSV File exists
                if self.create_csv and not os.path.isfile(self.file_location + temp_table + ".csv"):
                    raise UserError("CSV file " + self.file_location + temp_table + ".csv not found.")

                # Remove previous table if exists, failed sanitation for example
                if self.create_csv:
                    drop_query = "DROP TABLE IF EXISTS " + temp_table + ";"
                    self.env.cr.execute(drop_query)
                    self.env.cr.commit()

                    # Create empty temp table to restore CSV into
                    try:
                        temp_table_query = (
                            "CREATE TABLE " + temp_table + "(LIKE " + table + " INCLUDING ALL);"
                        )
                        self.env.cr.execute(temp_table_query)
                        self.env.cr.commit()
                    except Exception as e:
                        raise UserError("Error during creating empty temp table: \n %s" % e)

                    # Restore from CSV to temp table
                    try:
                        restore_query = (
                            "COPY "
                            + temp_table
                            + " FROM '"
                            + self.file_location
                            + temp_table
                            + ".csv' DELIMITER ',' CSV HEADER;"
                        )
                        self.env.cr.execute(restore_query)
                        self.env.cr.commit()
                    except Exception as e:
                        raise UserError("Error during copying data to temp table from CSV: \n %s" % e)

                # ============================ DESANITIZE DATA ============================
                i = len(line.included_char_column_ids)
                column_names = ""
                for column in line.included_char_column_ids:
                    if i > 1:
                        column_names += column.name + "=tsm." + column.name + ", "
                    else:
                        column_names += column.name + "=tsm." + column.name
                    i -= 1
                try:
                    desanitize_data_query = (
                        "UPDATE "
                        + table
                        + " AS sm SET "
                        + column_names
                        + " FROM "
                        + temp_table
                        + " tsm WHERE sm.id=tsm.id;"
                    )
                    self.env.cr.execute(desanitize_data_query)
                    self.env.cr.commit()
                except Exception as e:
                    _logger.info("\n -----------------  %s  -----------------------" % (e))
                    raise UserError("Error during restoring data: \n %s" % e)
                runningLog += "\nCompleted Desanitization"
                if line.log_notes:
                    notes = line.log_notes + runningLog
                else:
                    notes = runningLog

                line.write(
                    {
                        "log_notes": notes,
                        "decrypt_time": time.time() - start_time,
                        "state": "unsanitized",
                    }
                )

                # Drop temp table
                try:
                    drop_query = "DROP TABLE IF EXISTS " + temp_table + ";"
                    self.env.cr.execute(drop_query)
                    self.env.cr.commit()
                except Exception as e:
                    raise UserError("Error during dropping temp table: \n %s" % e)

    def decrypt_char_data(self):
        encrypted_lines = self.char_line_ids.filtered(lambda x: x.line_action == "encrypt_decrypt")
        for line in encrypted_lines:
            if line.line_action == "encrypt_decrypt" and line.state not in (
                "decrypted",
                "sanitized",
                "unsanitized",
                "excluded",
            ):
                self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                self.env.cr.commit()

                runningLog = line.log_notes or ""
                start_time = time.time()
                runningLog += "\n\nDECRYPTING DATA: "
                i = len(line.included_char_column_ids)
                column_names = (
                    " AND (col.table_name = '"
                    + line.table_id.model.replace(".", "_")
                    + "' AND col.column_name IN ("
                )
                for column in line.included_char_column_ids:
                    if i > 1:
                        column_names += "'" + column.name + "',"
                    else:
                        column_names += " '" + column.name + "'"
                    i -= 1
                column_names += "))"
                query = (
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
                        col.table_schema NOT IN ('information_schema', 'pg_catalog')"""
                    + column_names
                )
                self.env.cr.execute(query)
                table_columns_list_set = self.env.cr.fetchall()

                table_columns_dict = {}
                for table, column in table_columns_list_set:
                    if table in table_columns_dict and column not in table_columns_dict[table]:
                        table_columns_dict[table].append(column)
                    else:
                        table_columns_dict[table] = [column]

                runningLog += "MASTER TABLE GROUPED DICT: %s" % (str(table_columns_dict))

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
                    column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');""".format(
                        table, col
                    )
                    self.env.cr.execute(column_exists_query)
                    col_exists = self.env.cr.fetchone()

                    if col_exists[0]:
                        return True
                    else:
                        return False

                line.write({"state": "in_progress"})
                for table, columns in table_columns_dict.items():
                    table_exists_query = """SELECT EXISTS (SELECT FROM information_schema.tables WHERE  table_schema = 'public' AND table_name = '{}');""".format(
                        table
                    )
                    column_exists_query = """SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name='{}' AND column_name='{}');"""
                    columns_exists = []
                    self.env.cr.execute(table_exists_query)
                    table_exists = self.env.cr.fetchone()
                    if table_exists[0] is False:
                        tables_missing.append(table)
                        runningLog += "\n Skipping table %s as it doesn't exist in this db" % (table,)
                        tables_skipped.append(table)
                        continue

                    for each_col in columns:
                        if table in excluded_tables_columns and each_col in excluded_tables_columns[table]:
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
                        runningLog += "\n Skipping table as no columns present: table %s  cloumns %s" % (
                            table,
                            columns,
                        )
                        continue

                    if not check_column(table, "id"):
                        runningLog += "\n Skipping table  %s  as it doesn't have id column" % (table)
                        _logger.info("\n Skipping table  %s  as it doesn't have id column" % (table))
                        continue
                    query = "SELECT id, {}  FROM {} ORDER BY id".format(
                        ", ".join(['"%s"' % c for c in columns_exists]), table
                    )
                    self.env.cr.execute(query)
                    table_data = self.env.cr.fetchall()
                    runningLog += "\n Going Through Table: %s  for Columns: %s with %s records" % (
                        table,
                        str(columns_exists),
                        len(table_data),
                    )

                    rec_updated_ids = []
                    for index, col_data in enumerate(table_data):
                        id = col_data[0]
                        set_data = []

                        for col, col_data in zip(columns_exists, col_data[1:]):
                            if not col_data:
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
                                rec_updated_ids.append(id)

                        if not set_data:
                            continue
                        set_data_str = ", ".join(
                            [
                                """"%s" = pgp_sym_decrypt('%s', '%s')""" % (col, col_data, self.key)
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
                            runningLog += "\n Saved %s records of %s from table %s" % (
                                index + 1,
                                len(table_data),
                                table,
                            )
                    runningLog += "\n Decrypted data for %s records from table %s with columns %s" % (
                        len(rec_updated_ids),
                        table,
                        columns_exists,
                    )

                    runningLog += "\n Comitting changes for table: %s" % table
                    self.env.cr.commit()
                if tables_missing:
                    runningLog += "\n tables_missing:\n %s" % tables_missing
                if tables_skipped:
                    runningLog += "\n tables_skipped:\n %s" % tables_skipped
                if columns_missing:
                    runningLog += "\n columns_missing:\n %s" % columns_missing

                # If column is varchar, then reset the value back to original to allow room for encrypted data
                for column in line.included_char_column_ids:
                    # Change the character_max_length back to what it was before encryption
                    if column.size > 0:
                        table = column.model_id.model.replace(".", "_")
                        varchar_query = (
                            "UPDATE pg_attribute SET atttypmod = "
                            + str(column.size)
                            + " WHERE attrelid = '"
                            + table
                            + "'::regclass AND attname = '"
                            + column.name
                            + "';"
                        )
                        self.env.cr.execute(varchar_query)
                        runningLog += "\n Resized character_maximum_length for %s.%s from 10000 to %s \n" % (
                            table,
                            column.name,
                            column.size,
                        )
                        self.env.cr.commit()

                line.write(
                    {
                        "log_notes": runningLog,
                        "decrypt_time": time.time() - start_time,
                        "state": "decrypted",
                    }
                )
                _logger.info(runningLog)

    def decrypt_unsanitize_char_data(self):
        if any(x.line_action == "encrypt_decrypt" for x in self.char_line_ids):
            if not self.key:
                raise UserError("Missing Key! Please enter an encryption key to continue.")
            self.decrypt_char_data()
        if any(x.line_action == "sanitize_unsanitize" for x in self.char_line_ids):
            if self.create_csv and not os.path.isdir(self.file_location):
                raise UserError('Folder not found.')
            self.unsanitize_char_data()
