from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class access_domain_ah(models.Model):
    _name = 'access.domain.ah'
    _description = 'Access Domain'

    model_id = fields.Many2one(
        'ir.model', string='Model', index=True, required=True, ondelete='cascade')
    model_name = fields.Char(string='Model Name', related='model_id.model', readonly=True, store=True)
    apply_domain = fields.Boolean('Apply Filter')
    domain = fields.Char(string='Filter', default='[]',
                         help="The create customised domain rule where we can customise rule by selecting specific fields and records")

    access_management_id = fields.Many2one('access.management', 'Access Management')

    read_right = fields.Boolean('Read', default=True, help="The set 'Read' access of the selected model for the specified users")
    create_right = fields.Boolean('Create', help="The set 'Create' access of the selected model for the specified users")
    write_right = fields.Boolean('Write', help="The set 'Write' access of the selected model for the specified users")
    delete_right = fields.Boolean('Delete', help="The set 'Delete' access of the selected model for the specified users")

    @api.onchange('apply_domain')
    def _check_domain(self):
        for rec in self:
            if not rec.apply_domain:
                rec.domain = False

    @api.onchange('read_right')
    def _check_read(self):
        for rec in self:
            if not rec.read_right:
                rec.update({
                'create_right': False,
                'write_right': False,
                'delete_right': False,
                'apply_domain': True,
                'domain': '[["id","=",False]]'
            })

    @api.onchange('create_right')
    def _check_create(self):
        for rec in self:
            if rec.create_right:
                rec.read_right = True
            else:
                rec.delete_right = False

    @api.onchange('write_right')
    def _check_write(self):
        for rec in self:
            if rec.write_right:
                rec.read_right = True
            else:
                rec.delete_right = False

    @api.onchange('delete_right')
    def _check_delete(self):
        for rec in self:
            if rec.delete_right:
                rec.update({'read_right': True, 'write_right': True})
