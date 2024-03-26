# Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
# Copyright (C) Thinkopen Solutions <http://www.tkobr.com>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
import odoo
import pytz
from dateutil.relativedelta import relativedelta
from odoo import http, fields, SUPERUSER_ID, _
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons.web.controllers.home import Home
from odoo.addons.web.controllers.session import Session
from odoo.addons.web.controllers.utils import ensure_db

_logger = logging.getLogger(__name__)


class HomeTkobr(Home):

    @http.route('/web/login', type='http', auth="none")
    def web_login(self, redirect=None, **kw):
        if not request.registry.get('ir.sessions'):
            return super(HomeTkobr, self).web_login(redirect=redirect,
                                                    *args, **kw)
        request.params['login_success'] = False
        _logger.debug('Authentication method: HomeTkobr.web_login !')
        ensure_db()
        multi_ok = True
        calendar_set = 0
        calendar_ok = False
        calendar_group = ''
        unsuccessful_message = ''
        now = datetime.now()

        session_obj = request.env['ir.sessions']
        if request.httprequest.method == 'GET' and redirect and \
                request.session.uid:
            return request.redirect(redirect)

        if not request.uid:
            request.update_env(user=SUPERUSER_ID)

        values = request.params.copy()
        if not redirect:
            redirect = '/web?' + request.httprequest.query_string.decode(
                'utf-8')
        values['redirect'] = redirect

        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            uid = False
            if 'login' in request.params and 'password' in request.params:
                uid = request.session.authenticate(request.session.db,
                                                   request.params['login'],
                                                   request.params['password'])
            if uid is not False:
                user = request.env.user
                if uid is not SUPERUSER_ID:
                    # check for multiple sessions block
                    sessions = session_obj.search(
                        [('user_id', '=', uid), ('logged_in', '=', True)])

                    if sessions and user.multiple_sessions_block:
                        multi_ok = False

                    if multi_ok:
                        # check calendars
                        attendance_obj = request.env[
                            'resource.calendar.attendance']

                        # GET USER LOCAL TIME
                        if user.tz:
                            tz = pytz.timezone(user.tz)
                        else:
                            tz = pytz.timezone('GMT')
                        tzoffset = tz.utcoffset(now)
                        now = now + tzoffset
                        if user.login_calendar_id:
                            calendar_set += 1
                            # check user calendar
                            attendances = attendance_obj.search(
                                [('calendar_id', '=',
                                  user.login_calendar_id.id),
                                 ('dayofweek', '=',
                                  str(now.weekday())),
                                 ('hour_from', '<=',
                                  now.hour + now.minute / 60.0),
                                 ('hour_to', '>=',
                                  now.hour + now.minute / 60.0)])
                            if attendances:
                                calendar_ok = True
                            else:
                                unsuccessful_message = '''unsuccessful login
                                from '%s', user time out of allowed calendar
                                defined in user''' % request.params['login']
                        else:
                            # check user groups calendar
                            for group in user.groups_id:
                                if group.login_calendar_id:
                                    calendar_set += 1
                                    attendances = attendance_obj.search(
                                        [('calendar_id', '=',
                                          group.login_calendar_id.id),
                                         ('dayofweek', '=', str(
                                             now.weekday())),
                                         ('hour_from', '<=',
                                          now.hour + now.minute / 60.0),
                                         ('hour_to', '>=',
                                          now.hour + now.minute / 60.0)])
                                    if attendances:
                                        calendar_ok = True
                                    else:
                                        calendar_group = group.name
                                if sessions and group.\
                                        multiple_sessions_block and multi_ok:
                                    multi_ok = False
                                    unsuccessful_message = _('''unsuccessful login from %s,
                                    multisessions block defined in group %s
                                    ''') % (request.params['login'],
                                            group.name)
                                    break
                            if calendar_set > 0 and not calendar_ok:
                                unsuccessful_message = _('''unsuccessful login
                                from %s, user time out of allowed calendar
                                defined in group %s''') % (request.params[
                                    'login'], calendar_group)
                    else:
                        unsuccessful_message = _('''unsuccessful login from %s,
                        multisessions block defined in user
                        ''') % request.params['login']
            else:
                unsuccessful_message = _('''unsuccessful login from %s,
                wrong username or password''') % request.params['login']
            if not unsuccessful_message or uid is SUPERUSER_ID:
                self.save_session(
                    user.tz,
                    request.session.sid)
                return request.redirect(redirect)
            user = request.env.user
            self.save_session(
                user.tz,
                request.session.sid,
                unsuccessful_message)
            _logger.error(unsuccessful_message)
            request.update_env(user=old_uid)
            values['error'] = _('''Login failed due to one of the following
            reasons:''')
            values['reason1'] = _('- Wrong login/password')
            values['reason2'] = _('- User not allowed to have multiple logins')
            values['reason3'] = _('''- User not allowed to login at this
            specific time or day''')
        return request.render('web.login', values)

    def save_session(
            self,
            tz,
            sid,
            unsuccessful_message='',
    ):
        now = fields.datetime.now()
        session_obj = request.env['ir.sessions']
        cr = request.registry.cursor()

        # Get IP, check if it's behind a proxy
        ip = request.httprequest.headers.environ['REMOTE_ADDR']
        forwarded_for = ''
        if 'HTTP_X_FORWARDED_FOR' in request.httprequest.headers.environ and \
                request.httprequest.headers.environ['HTTP_X_FORWARDED_FOR']:
            forwarded_for = request.httprequest.headers.environ[
                'HTTP_X_FORWARDED_FOR'].split(', ')
            if forwarded_for and forwarded_for[0]:
                ip = forwarded_for[0]

        # for GeoIP
        geo_ip_resolver = None
        ip_location = ''
        try:
            import GeoIP
            geo_ip_resolver = GeoIP.open(
                '/usr/share/GeoIP/GeoIP.dat',
                GeoIP.GEOIP_STANDARD)
        except ImportError:
            geo_ip_resolver = False
        if geo_ip_resolver:
            ip_location = (str(geo_ip_resolver.country_name_by_addr(ip)) or '')

        # autocommit: our single update request will be performed atomically.
        # (In this way, there is no opportunity to have two transactions
        # interleaving their cr.execute()..cr.commit() calls and have one
        # of them rolled back due to a concurrent access.)
        cr._cnx.autocommit = True
        user = request.env.user
        logged_in = True
        uid = user.id
        if unsuccessful_message:
            uid = SUPERUSER_ID
            logged_in = False
            sessions = False
        else:
            sessions = session_obj.search([('session_id', '=', sid),
                                           ('ip', '=', ip),
                                           ('user_id', '=', uid),
                                           ('logged_in', '=', True)],
                                          )
        if not sessions:
            date_expiration = (now + relativedelta(
                seconds=user.session_default_seconds)).strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT)
            values = {
                'user_id': uid,
                'logged_in': logged_in,
                'session_id': sid,
                'session_seconds': user.session_default_seconds,
                'multiple_sessions_block': user.multiple_sessions_block,
                'date_login': now.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'date_expiration': date_expiration,
                'ip': ip,
                'ip_location': ip_location,
                'remote_tz': tz or 'GMT',
                'unsuccessful_message': unsuccessful_message,
            }
            session_obj.sudo().create(values)
            cr.commit()
        cr.close()


class SessionTkobr(Session):

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        if request.session:
            sessions = request.env['ir.sessions'].search(
                [('logged_in', '=', True),
                 ('user_id', '=', request.session.uid)])
            if sessions:
                sessions._on_session_logout(logout_type='ul')
        request.session.logout(keep_db=True)
        return super(SessionTkobr, self).logout(redirect=redirect)
