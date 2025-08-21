from odoo import api, fields, models, tools, _
from odoo.addons.advanced_web_domain_widget.models.domain_prepare import prepare_domain_v2

class BaseModel(models.AbstractModel):
    _inherit = 'base'

    # @api.model
    # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs):
    #     res = super().search_read(domain, fields, offset, limit, order, **read_kwargs)
    #     if self._context.get('web_domain_widget') and hasattr(self, 'company_id'):
    #         for rec in res:
    #             rec.update({'company_name': self.browse(rec.get('id')).company_id.name})

    #     return res

    @api.model
    def domain_name_search(self, name='', args=None, operator='ilike', limit=100):
        if self.env.user.has_group('base.group_system'):
            res = self.sudo().name_search(name, args, operator, limit)
        else:
            res = self.name_search(name, args, operator, limit)
        return res
    
    @api.model
    def get_widget_count(self, args):
        # return self.sudo().search_count(args)
        domain_list = []
        for domain in args:
            if isinstance(domain, tuple) or isinstance(domain, list):
                domain_list += prepare_domain_v2(domain)
        if self.env.user.has_group('base.group_system'):
            res = self.sudo().search_count(domain_list)
        else:
            res = self.search_count(domain_list)
        return res