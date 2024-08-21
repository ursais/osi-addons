# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import os
import logging
import time
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EncryptWizard(models.TransientModel):
    _name = "encrypt.lines.wizard"
    _description = "Encrypt Lines Wizard"

    key = fields.Char(
        "Encryption Key",
        help="Enter the encryption key to use for encrypting the data.",
    )
    char_line_ids = fields.Many2many(
        "encrypt.line",
        string="Lines to Encrypt",
        help="These are the items that are going to be encrypted. "
        "If they have already been encrypted, excluded or don't contain columns then they will be skipped.",
    )
    file_location = fields.Char(
        "Files Location",
        default="/home/odoo/",
        help="Enter the file location where the CSV files will be kept. Write permissions are needed and make sure the location is persistant.",
    )
    show_key = fields.Boolean("Show Key", compute="_show_fields_compute")
    show_file_location = fields.Boolean(
        "Show File Location", compute="_show_fields_compute"
    )
    create_csv = fields.Boolean(
        "Create CSV",
        default=True,
        help="Creates CSV file and drop the temporary tables. Otherwise the temporary tables will be kept.",
    )

    @api.depends("char_line_ids")
    def _show_fields_compute(self):
        """ """
        for rec in self:
            rec.show_key = False
            rec.show_file_location = False
            if any(line.line_action == "encrypt_decrypt" for line in rec.char_line_ids):
                rec.show_key = True
            if (
                any(
                    line.line_action == "sanitize_unsanitize"
                    for line in rec.char_line_ids
                )
                and self.create_csv
            ):
                rec.show_file_location = True

    def test_query(self):
        for line in self.char_line_ids:
            # Allows testing the query using the current added line columns
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
                    col.data_type IN ('character varying', 'character', 'text', '"char"', 'name')
                AND imf.ttype != 'selection'
                AND col.table_schema NOT IN ('information_schema', 'pg_catalog')"""
                + column_names
            )
            self.env.cr.execute(query)
            table_columns_list_set = self.env.cr.fetchall()

            table_columns_dict = {}
            for table, column in table_columns_list_set:
                if (
                    table in table_columns_dict
                    and column not in table_columns_dict[table]
                ):
                    table_columns_dict[table].append(column)
                else:
                    table_columns_dict[table] = [column]
            raise UserError(table_columns_dict.items())

    def sanitize_char_data(self):
        sanitize_lines = self.char_line_ids.filtered(
            lambda x: x.line_action == "sanitize_unsanitize"
        )
        for line in sanitize_lines:
            if line.line_action == "sanitize_unsanitize" and line.state not in (
                "encrypted",
                "decrypted",
                "sanitized",
                "excluded",
            ):
                # Pre check for exclusions
                if line.state == "excluded":
                    runningLog = "This table has been marked to be excluded. No encryption tasks have been performed."
                    line.write({"log_notes": runningLog})
                    continue
                # Pre check for already sanitized (or encrypted incase it was somehow added)
                if line.state in ("encrypted", "sanitized"):
                    continue
                # Pre check if not columns added to be processed
                if not line.included_char_column_ids:
                    line.write(
                        {
                            "log_notes": "No columns to encrypt. Moving to 'Excluded' state.",
                            "exclude_reason": "No Columns to Encrypt",
                            "state": "excluded",
                        }
                    )
                    continue

                # ============================ SANITIZE THE DATA ============================
                if line.line_action == "sanitize_unsanitize":
                    runningLog = "SANITIZING FIELDS: "
                    start_time = time.time()
                    table = line.table_id.model.replace(".", "_")
                    temp_table = "temp_" + table

                    # Remove previous temp table if exists, failed sanitation for example
                    drop_query = "DROP TABLE IF EXISTS " + temp_table + ";"
                    self.env.cr.execute(drop_query)
                    self.env.cr.commit()

                    # Create temporary table
                    try:
                        temp_table_query = (
                            "CREATE TABLE "
                            + temp_table
                            + " AS SELECT * FROM "
                            + table
                            + ";"
                        )
                        self.env.cr.execute(temp_table_query)
                        self.env.cr.commit()
                    except Exception as e:
                        raise UserError("Error during creating temp table: \n %s" % e)

                    # Export to CSV File
                    # TODO pg_dump is a better option here, CSV requires same table columsn which may change
                    if self.create_csv:
                        try:
                            export_table_query = (
                                "COPY "
                                + temp_table
                                + " TO '"
                                + self.file_location
                                + temp_table
                                + ".csv' CSV HEADER;"
                            )
                            self.env.cr.execute(export_table_query)
                            self.env.cr.commit()
                        except Exception as e:
                            raise UserError(
                                "Error during crating temp table: \n %s" % e
                            )

                    # Sanitize the data with random characters taking char max size into consideration
                    i = len(line.included_char_column_ids)
                    column_names = ""
                    for column in line.included_char_column_ids:
                        char_limit = column.size or 33
                        if i > 1:
                            column_names += (
                                column.name
                                + "=substr(md5(random()::text), 0, "
                                + str(char_limit)
                                + "), "
                            )
                        else:
                            column_names += (
                                column.name
                                + "=substr(md5(random()::text), 0, "
                                + str(char_limit)
                                + ")"
                            )
                        i -= 1
                    try:
                        sanitize_data_query = (
                            "UPDATE " + table + " SET " + column_names + ";"
                        )
                        self.env.cr.execute(sanitize_data_query)
                        self.env.cr.commit()
                    except Exception as e:
                        raise UserError("Error during sanitizing data: \n %s" % e)
                    line.write(
                        {
                            "num_records": line.total_num_records,
                            "encrypt_time": time.time() - start_time,
                            "log_notes": runningLog,
                            "state": "sanitized",
                        }
                    )

                    # Drop temp table if CSV is created
                    if self.create_csv:
                        try:
                            drop_query = "DROP TABLE IF EXISTS " + temp_table + ";"
                            self.env.cr.execute(drop_query)
                            self.env.cr.commit()
                        except Exception as e:
                            raise UserError(
                                "Error during dropping temp table: \n %s" % e
                            )

    def encrypt_char_data(self):
        encrypt_lines = self.char_line_ids.filtered(
            lambda x: x.line_action == "encrypt_decrypt"
        )
        for line in encrypt_lines:
            # If no columns to encrypt then set line as excluded since there is nothing to do.
            if not line.included_char_column_ids:
                line.write(
                    {
                        "state": "excluded",
                        "exclude_reason": "Excluded due to no lines to encrypt.",
                    }
                )
                continue

            if line.line_action == "encrypt_decrypt" and line.state not in (
                "encrypted",
                "unsanitized",
                "sanitized",
                "excluded",
            ):
                # Make sure pgcrypto extension exists and create if not
                self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                self.env.cr.commit()

                runningLog = "ENCRYPTING FIELDS: "
                start_time = time.time()

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
                    if (
                        table in table_columns_dict
                        and column not in table_columns_dict[table]
                    ):
                        table_columns_dict[table].append(column)
                    else:
                        table_columns_dict[table] = [column]

                for column in line.included_char_column_ids:
                    table = column.model_id.model.replace(".", "_")

                    # If column is varchar, then reset the value to allow room for encrypted data
                    if column.size > 0:
                        varchar_query = (
                            "UPDATE pg_attribute SET atttypmod = 100000 WHERE attrelid = '"
                            + table
                            + "'::regclass AND attname = '"
                            + column.name
                            + "';"
                        )
                        self.env.cr.execute(varchar_query)
                        runningLog += (
                            "\n Resized character_maximum_length for %s.%s from %s to 10000 \n"
                            % (
                                table,
                                column.name,
                                column.size,
                            )
                        )
                        self.env.cr.commit()

                # ============================ ENCRYPT DATA ============================
                line.write({"state": "in_progress"})
                runningLog += "MASTER TABLE GROUPED DICT: %s" % (
                    str(table_columns_dict)
                )
                log_excluded_ids = ""
                for table, columns in table_columns_dict.items():
                    query = "SELECT id, {}  FROM {} ORDER BY id".format(
                        ", ".join(['"%s"' % c for c in columns]), table
                    )
                    self.env.cr.execute(query)
                    table_data = self.env.cr.fetchall()

                    runningLog += (
                        "\n Going Through Table: %s  for Columns: %s with %s records"
                        % (
                            table,
                            str(columns),
                            len(table_data),
                        )
                    )

                    rec_updated_ids = []
                    skipped_ids = []
                    for col_data in table_data:
                        id = col_data[0]
                        set_data = []

                        for col, col_data in zip(columns, col_data[1:]):
                            if col_data:
                                # Don't update if id in excluded id's
                                if line.exclude_ids and str(
                                    id
                                ) in line.exclude_ids.split(","):
                                    continue

                                set_data.append(
                                    (
                                        col,
                                        col_data,
                                    )
                                )
                                rec_updated_ids.append(id)

                        if not set_data:
                            skipped_ids.append(id)
                            continue
                        set_data_str = ",".join(
                            [
                                """"%s" = pgp_sym_encrypt('%s', '%s')"""
                                % (col, col_data.replace("'", "''"), self.key)
                                for col, col_data in set_data
                            ]
                        )

                        try:
                            query = """ UPDATE %s SET %s  where id = %s ;""" % (
                                table,
                                set_data_str,
                                id,
                            )
                            self.env.cr.execute(query)

                        except Exception as e:
                            raise UserError(
                                "\nERROR: \n%s\n \nWHEN RUNNING QUERY: \n%s\n"
                                % (
                                    e,
                                    query,
                                )
                            )

                    if skipped_ids:
                        runningLog += (
                            "\n Skipped %s Record(s) as no field has data to be updated: %s "
                            % (
                                len(skipped_ids),
                                col_data,
                            )
                        )
                    runningLog += "\n Encrypted data for %s records from table %s" % (
                        len(rec_updated_ids),
                        table,
                    )
                    if log_excluded_ids != "":
                        runningLog += "\n IDs excluded: " % log_excluded_ids
                self.env.cr.commit()
                line.write(
                    {
                        "num_records": len(rec_updated_ids),
                        "encrypt_time": time.time() - start_time,
                        "log_notes": runningLog,
                        "state": "encrypted",
                    }
                )
                self.env.cr.commit()
                _logger.info(runningLog)

    def encrypt_sanitize_char_data(self):
        if any(x.line_action == "encrypt_decrypt" for x in self.char_line_ids):
            if not self.key:
                raise UserError(
                    "Missing Key! Please enter an encryption key to continue."
                )
            self.encrypt_char_data()
        if any(x.line_action == "sanitize_unsanitize" for x in self.char_line_ids):
            if self.create_csv and not os.path.isdir(self.file_location):
                raise UserError("Folder not found.")
            self.sanitize_char_data()
