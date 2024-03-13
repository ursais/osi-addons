# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import os
import logging
from odoo.exceptions import UserError, Warning

_logger = logging.getLogger(__name__)


class GenerateEncryptLinesWizard(models.TransientModel):
    _name = "generate.encrypt.lines.wizard"
    _description = "Generate Encryption Lines Wizard"

    include_char = fields.Boolean("Char", default=True)
    include_varchar = fields.Boolean("VarChar (Size Limit)", default=True)
    include_text = fields.Boolean(string="Text", default=True)
    exclude_ir = fields.Boolean(string="Exclude ir_ models")
    exclude_mail = fields.Boolean(string="Exclude mail models")
    exclude_report = fields.Boolean(string="Exclude report models")
    exclude_tables = fields.Many2many("ir.model", string="Excluded Tables")
    query_preview = fields.Text(
        string="Query: Edit for custom query",
    )

    @api.onchange(
        "include_char",
        "include_varchar",
        "include_text",
        "exclude_ir",
        "exclude_mail",
        "exclude_report",
        "exclude_tables",
    )
    def _onchange_generate_query(self):
        self.query_preview = self.generate_query()

    def generate_query(self):
        query = """SELECT
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
            col.data_type IN ("""
        if self.include_char:
            query += "'character', 'char',"
        if self.include_varchar:
            query += "'character varying',"
        if self.include_text:
            query += "'text',"
        query += """'name')
          AND imf.ttype != 'selection'
          AND col.table_schema NOT IN ('information_schema', 'pg_catalog')"""
        if self.exclude_ir:
            query += """
            AND col.table_name NOT LIKE 'ir%'"""
        if self.exclude_mail:
            query += """
            AND tab.table_name NOT LIKE 'mail%'"""
        if self.exclude_report:
            query += """
            AND col.table_name NOT LIKE 'report%'"""
        if self.exclude_tables:
            i = len(self.exclude_tables)
            query += """
                AND col.table_name NOT IN ("""
            for table in self.exclude_tables:
                if i > 1:
                    query += "'" + table.model.replace(".", "_") + "',"
                else:
                    query += "'" + table.model.replace(".", "_") + "')"
                i -= 1
        query += """
        ORDER BY col.table_name, col.ordinal_position;"""
        return query

    def test_query(self):
        self.env.cr.execute(self.query_preview)
        result = self.env.cr.fetchall()
        raise UserError("Query Returned: \n %s" % result)

    def compute_number_of_records(self):
        pass

    def generate_lines(self):
        try:
            self.env.cr.execute(self.query_preview)
        except Exception as e:
            raise Warning("ERROR: %s \n WHEN RUNNING QUERY: \n%s\n" % (e, self.query_preview))

        table_columns_list_set = self.env.cr.fetchall()

        table_columns_dict = {}
        for table, column in table_columns_list_set:
            if table in table_columns_dict and column not in table_columns_dict[table]:
                table_columns_dict[table].append(column)
            else:
                table_columns_dict[table] = [column]
        for table, columns in table_columns_dict.items():
            table_id = self.env["ir.model"].search([("model", "=", table.replace("_", "."))])

            # Don't include the encryption module models
            if "decrypt" in table_id.model or "encrypt" in table_id.model:
                continue

            # Plase the column in its proper place
            column_ids = []
            exclude_column_ids = []
            indexes = []
            existing_line = self.env["encrypt.line"].search([("table_id", "=", table_id.id)])
            if existing_line.state in ("encrypted", "sanitized"):
                continue
            for col in columns:
                col_id = self.env["ir.model.fields"].search(
                    [("model_id", "=", table_id.id), ("name", "=", col)]
                )
                if (
                    col_id not in existing_line.excluded_char_column_ids
                    and col_id.store
                    and not col_id.related
                ):
                    column_ids.append(col_id.id)
                else:
                    exclude_column_ids.append(col_id.id)
                if col_id.index:
                    # Get indexes
                    table = table_id.model.replace(".", "_")
                    get_index_query = (
                        "SELECT indexname FROM pg_indexes WHERE tablename = '"
                        + table
                        + "' AND indexdef LIKE '%"
                        + col_id.name
                        + "%';"
                    )
                    self.env.cr.execute(get_index_query)
                    indexes.append(self.env.cr.fetchall())

            # For complete reporting, we want to go ahead and throw all the other fields into excluded
            other_table_columns = self.env["ir.model.fields"].search(
                [
                    ("model_id", "=", table_id.id),
                    ('ttype', 'in', ('char', 'text', 'html')),
                ]
            )
            for co in other_table_columns:
                if co.id not in column_ids and co.id not in exclude_column_ids:
                    exclude_column_ids.append(co.id)

            # Get number of records
            total_record_num = 0
            self.env.cr.execute(
                "SELECT reltuples::bigint AS estimate FROM pg_class WHERE oid = 'public."
                + table_id.model.replace(".", "_")
                + "'::regclass;"
            )
            get_total_record_num = self.env.cr.fetchall()
            total_record_num = int(
                float(str(get_total_record_num[0]).replace(',', '').replace('(', '').replace(')', ''))
            )
            # Sometimes -1 is returned so clean that up setting to zero
            if total_record_num < 0:
                total_record_num = 0

            # Check for existing line that should be modified instead,
            # create on if doesn't exist
            if not existing_line:
                self.env["encrypt.line"].create(
                    {
                        "table_id": table_id.id,
                        "included_char_column_ids": [(6, 0, column_ids)],
                        "excluded_char_column_ids": [(6, 0, exclude_column_ids)],
                        "indexes": indexes or False,
                        "total_num_records": total_record_num,
                    }
                )
            else:
                existing_line.write(
                    {
                        "table_id": table_id.id,
                        "included_char_column_ids": [(6, 0, column_ids)],
                        "excluded_char_column_ids": [(6, 0, exclude_column_ids)],
                        "indexes": indexes,
                        "total_num_records": total_record_num,
                    }
                )
        return {"type": "ir.actions.client", "tag": "reload"}
