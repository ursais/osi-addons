'''
Created on May 14, 2019

@author: Zuhair Hammadi
'''
from odoo import models
from odoo.http import request

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        res = super(Http, self).session_info()

        if request and request.session.impersonate_uid:  # @UndefinedVariable
            res['impersonate'] = bool(request.session.impersonate_uid)  # @UndefinedVariable

        return res
