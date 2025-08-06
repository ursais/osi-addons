
from odoo.addons.web.controllers.domain import Domain
from odoo import http, _

class Domain(Domain):

    @http.route('/web/domain/validate', type='json', auth="user")
    def validate(self, model, domain):
        result = super(Domain,self).validate(model, domain)
        if not result:
            for dom in domain:
                if 'date_filter' in dom:
                    result = True
        return result