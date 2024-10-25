# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    mrp_batch_id = fields.Many2one("mrp.production.batch",string="MRP Batch", domain="[('state', 'not in', ('done','cancel','hold'))]", copy=False)
    mrp_batch_state = fields.Selection(related='mrp_batch_id.state', readonly=True, string="Batch Status")

    def action_remove_batch(self):
        if self.filtered(lambda batch: not batch.mrp_batch_id):
            raise UserError("No batch found to remove or batch has already been removed.")
        if self.mapped('mrp_batch_id').filtered(lambda batch: batch.state in ('done','cancel','hold')):
            raise UserError("Some manufacting Batch you can't removed.")
        self.mrp_batch_id = False
    
    def action_open_wizard(self):
        if all([record.mrp_batch_id for record in self]):
                raise UserError("A batch has already been created for this record.")
        for record in self:
            if record.state in ['done', 'cancel'] :
                raise UserError("You cannot create a batch for records that are in 'Done' or 'Cancel' state.")
            return {
                'name': 'Create Batch',
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production.batch.wizard',
                'view_mode': 'form',
                'target': 'new',
            }