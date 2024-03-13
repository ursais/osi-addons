# Copyright (C) 2024 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _


class DropIndexWizard(models.TransientModel):
    _name = "drop.index.wizard"
    _description = "decrypt Lines Wizard"

    index_name = fields.Char("Index Name")
    line_id = fields.Many2one('encrypt.line')

    def drop_index(self):
        index_query = "drop index IF EXISTS " + self.index_name + ";"
        self.env.cr.execute(index_query)
        self.env.cr.commit()
        if self.line_id.dropped_indexes:
            if self.index_name not in self.line_id.dropped_indexes:
                self.line_id.write({"dropped_indexes": self.line_id.dropped_indexes + "," + self.index_name})
        else:
            self.line_id.write({"dropped_indexes": self.index_name})
