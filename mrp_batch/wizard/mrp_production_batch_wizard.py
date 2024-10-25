from odoo import fields, models
class MRPProductionBatchwizard(models.TransientModel):
    _name = 'mrp.production.batch.wizard'
    
    responsible_id =fields.Many2one('res.users', string="Responsible" ,required=True)
    tag_ids = fields.Many2many('mrp.production.batch.tag',string="Tags")
    date_scheduled = fields.Datetime(string="Scheduled Date")

    def action_confirm(self):
        active_ids = self._context.get('active_ids')
        records = self.env['mrp.production'].browse(active_ids)
        allows_records = records.filtered(lambda m: m.state in ['progress', 'draft'])
        vals = {'responsible_id':self.responsible_id.id,
                'tag_ids':self.tag_ids.ids,
                'date_scheduled':self.date_scheduled,
                'production_ids':allows_records}          
        self.env['mrp.production.batch'].create(vals)

    