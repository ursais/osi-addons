# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.service import security
from odoo.addons.web.controllers import home as web_home

import logging
_logger = logging.getLogger(__name__)

class LoginAs(web_home.Home):
    
    @http.route('/web/login_as/<int:user_id>', type='http', auth='user', sitemap=False)
    def switch_to_user(self, user_id, **kwargs):  # @UnusedVariable
        uid = request.env.user.id  # @UndefinedVariable
        if request.env.user._is_system():  # @UndefinedVariable
            request.session.impersonate_uid = uid
            uid = request.session.uid = user_id
            # invalidate session token cache as we've changed the uid
            request.env.registry.clear_cache()
            request.session.session_token = security.compute_session_token(request.session, request.env)
            
            _logger.info('User %s Logged in as %s' % (request.env.user.name, request.env['res.users'].browse(user_id).name))

        return request.redirect(self._login_redirect(uid))

    @http.route('/web/login_back', type='http', auth='user', sitemap=False)
    def switch_back(self, **kwargs):  # @UnusedVariable
        uid = request.env.user.id  # @UndefinedVariable
        if request.session.impersonate_uid:  # @UndefinedVariable
            uid = request.session.uid = request.session.impersonate_uid  # @UndefinedVariable
            request.session.impersonate_uid = False
            # invalidate session token cache as we've changed the uid
            request.env.registry.clear_cache()
            request.session.session_token = security.compute_session_token(request.session, request.env)

        return request.redirect(self._login_redirect(uid) + '?debug=1')
