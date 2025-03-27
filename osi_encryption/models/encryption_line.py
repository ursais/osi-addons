# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EncryptLine(models.Model):
    _name = "encrypt.line"
    _description = "Encryption Line"

    state = fields.Selection(
        selection=[
            ("decrypted", "Decrypted"),
            ("encrypted", "Encrypted"),
            ("excluded", "Excluded"),
            ("in_progress", "In Progress"),
            ("unsanitized", "Unsanitized"),
            ("sanitized", "Sanitized"),
            ("error", "Error"),
        ],
        default="decrypted",
    )
    line_action = fields.Selection(
        selection=[
            ("encrypt_decrypt", "Encryption"),
            ("sanitize_unsanitize", "Sanitization"),
        ],
        default="encrypt_decrypt",
    )
    table_id = fields.Many2one("ir.model", string="Table")
    model = fields.Char("Model Name", related="table_id.model", store=True)
    name = fields.Char("Model", related="table_id.name", store=True)
    included_char_column_ids = fields.Many2many(
        "ir.model.fields",
        "encryp_included_line_field_id_rel",
        string="Included Char/Text Columns",
    )
    excluded_char_column_ids = fields.Many2many(
        "ir.model.fields",
        "encryp_excluded_line_field_id_rel",
        string="Excluded Char/Text Columns",
    )
    exclude_ids = fields.Char("Exclude Ids")
    num_records = fields.Integer("# of Updated Fields")
    total_num_records = fields.Integer("Total # of Records")
    encrypt_time = fields.Float(string="Time to Encrypt (Sec)")
    decrypt_time = fields.Float(string="Time to Decrypt (Sec)")
    log_notes = fields.Text(string="Log")
    exclude_reason = fields.Char(string="Exclude Reason")
    indexes = fields.Char(string="Indexes")
    dropped_indexes = fields.Char(string="Dropped Indexes")
    export_include_column_format = fields.Char(
        string="Included Column Names",
        compute="_compute_export_fields",
        store=True,
    )
    export_exclude_column_format = fields.Char(
        string="Excluded Column Names",
        compute="_compute_export_fields",
        store=True,
    )

    _sql_constraints = [
        (
            'table_id_line_action_uniq',
            'unique (table_id, line_action)',
            "An encryption line with the same action for this table already exists!",
        ),
    ]

    @api.depends('included_char_column_ids', 'excluded_char_column_ids')
    def _compute_export_fields(self):
        for rec in self:
            i = len(rec.included_char_column_ids)
            in_column_name = ""
            for in_column in rec.included_char_column_ids:
                if i > 1:
                    in_column_name += in_column.name + ", "
                else:
                    in_column_name += in_column.name + ""
                i -= 1
            rec.export_include_column_format = in_column_name

            i = len(rec.excluded_char_column_ids)
            ex_column_name = ""
            for ex_column in rec.excluded_char_column_ids:
                col_name = ex_column.name
                if ex_column.related:
                    col_name += " (Related)"
                elif not ex_column.store:
                    col_name += " (Not Stored)"
                if i > 1:
                    ex_column_name += col_name + ", "
                else:
                    ex_column_name += col_name + ""
                i -= 1
            rec.export_exclude_column_format = ex_column_name

    @api.onchange("line_action")
    def line_action_onchange(self):
        for rec in self:
            if rec.line_action == "encrypt_decrypt" and rec.state == "unsanitized":
                rec.state = 'decrypted'
            if rec.line_action == "sanitize_unsanitize" and rec.state == "decrypted":
                rec.state = 'unsanitized'
            if rec.line_action == "encrypt_decrypt" and rec.state in ("sanitized", "in_progress"):
                raise UserError("Can't change action to Encrypt/Decrypt because the state doesn't allow it.")
            if rec.line_action == "encrypt_decrypt" and rec.state in ("encrypted", "in_progress"):
                raise UserError(
                    "Can't change action to Sanitize/Desanitize because the state doesn't allow it."
                )

    @api.onchange("included_char_column_ids", "excluded_char_column_ids")
    def included_char_column_ids_onchange(self):
        if self.included_char_column_ids != self._origin.included_char_column_ids:
            lines = []
            move_lines_to_exclude = []
            for item in self._origin.included_char_column_ids.ids:
                if item not in self.included_char_column_ids.ids:
                    lines.append(item)
            move_lines_to_exclude = self.env['ir.model.fields'].search([('id', 'in', lines)])
            self.excluded_char_column_ids = [(4, ml.id) for ml in move_lines_to_exclude]
        if self.excluded_char_column_ids != self._origin.excluded_char_column_ids:
            lines = []
            move_lines_to_include = []
            for item in self._origin.excluded_char_column_ids.ids:
                if item not in self.excluded_char_column_ids.ids:
                    lines.append(item)
            move_lines_to_include = (
                self.env['ir.model.fields']
                .search([('id', 'in', lines)])
                .filtered(lambda x: x.store and not x.related)
            )
            self.included_char_column_ids = [(4, ml.id) for ml in move_lines_to_include]

    def button_exclude(self):
        for rec in self:
            if rec.state not in ('encrypted', 'in progress', 'sanitized'):
                rec.write({'state': 'excluded'})

    def button_include(self):
        for rec in self:
            if rec.state == 'excluded':
                if rec.line_action == 'sanitize_unsanitize':
                    rec.write({'state': 'unsanitized'})
                else:
                    rec.write({'state': 'decrypted'})

    def button_get_number_of_rows(self):
        # Update number of records
        # Note this is estimate as it pulls numbers from last VACUUM/ANALYZE
        for rec in self:
            total_record_num = 0
            self.env.cr.execute(
                "SELECT reltuples::bigint AS estimate FROM pg_class WHERE oid = 'public."
                + self.table_id.model.replace(".", "_")
                + "'::regclass;"
            )
            get_total_record_num = self.env.cr.fetchall()
            total_record_num = int(
                float(str(get_total_record_num[0]).replace(',', '').replace('(', '').replace(')', ''))
            )
            # Sometimes -1 is returned so clean that up setting to zero
            if total_record_num < 0:
                total_record_num = 0
            rec.write({'total_num_records': total_record_num})

    def button_drop_index_wizard(self):
        wizard = self.env.ref(
            "osi_encryption.drop_index_wizard_view",
            raise_if_not_found=False,
        )
        return {
            "name": "Drop Index",
            "view_type": "form",
            "view_mode": "form",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "res_model": "drop.index.wizard",
            "type": "ir.actions.act_window",
            "context": {"default_line_id": self.id},
            "target": "new",
        }

    def encrypt_sanitize_char_data_wizard(self):
        wizard = self.env.ref(
            "osi_encryption.encrypt_lines_wizard_view",
            raise_if_not_found=False,
        )
        active_ids = self.env.context.get('active_ids')
        return {
            "name": "Encrypt/Sanitize Wizard",
            "view_type": "form",
            "view_mode": "form",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "res_model": "encrypt.lines.wizard",
            "type": "ir.actions.act_window",
            "context": {"default_char_line_ids": active_ids or [(6, 0, [self.id])]},
            "target": "new",
        }

    def decrypt_unsanitize_char_data_wizard(self):
        wizard = self.env.ref(
            "osi_encryption.decrypt_lines_wizard_view",
            raise_if_not_found=False,
        )
        active_ids = self.env.context.get('active_ids')
        return {
            "name": "Decrypt/Unsanitize Wizard",
            "view_type": "form",
            "view_mode": "form",
            "views": [(wizard.id, "form")],
            "view_id": wizard.id,
            "res_model": "decrypt.lines.wizard",
            "type": "ir.actions.act_window",
            "context": {"default_char_line_ids": active_ids or [(6, 0, [self.id])]},
            "target": "new",
        }

    def unlink(self):
        """Prevent deleting an encrypted line."""
        for line in self:
            if line.state == "encrypted":
                raise Warning(
                    _('You cannot delete a line that has been encrypted. Please decrypt first then delete.')
                )
        return super().unlink()
