from odoo import http
from odoo.exceptions import UserError
from odoo.addons.web.controllers.export import Export
from odoo.http import request

class Export(Export):

    def fields_get(self, model):
        fields=super().fields_get(model)
        invisible_field_ids = request.env['hide.field'].sudo().search(
                        [('access_management_id.company_ids', 'in', request.env.company.id),
                         ('model_id.model', '=', model), ('access_management_id.active', '=', True),
                        ('access_management_id.user_ids', 'in', request.env.user.id),
                         ('invisible','=',True)])
        if not invisible_field_ids:
            return fields
        else :
            for key, value in list(fields.items()):
                for invisible_field in invisible_field_ids.field_id:
                    if key == invisible_field.name and key != "id":
                        del fields[key]
            return fields
