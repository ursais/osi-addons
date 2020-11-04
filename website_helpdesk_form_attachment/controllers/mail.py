# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http, _
from odoo.http import request
from odoo.tools import consteq, plaintext2html
from odoo.exceptions import AccessError, MissingError, UserError
from .portal import CustomerPortal
from odoo.addons.portal.controllers.mail import PortalChatter


def _check_special_access(res_model, res_id, token='', _hash='', pid=False):
    record = request.env[res_model].browse(res_id).sudo()
    if token:  # Token Case: token is the global one of the document
        token_field = request.env[res_model]._mail_post_token_field
        return (token and record and consteq(record[token_field], token))
    # Signed Token Case: hash implies token is signed by partner pid
    elif _hash and pid:
        return consteq(_hash, record._sign_token(pid))
    else:
        raise Forbidden()


def _message_post_helper(res_model, res_id, message,
                         token='', _hash=False, pid=False,
                         nosubscribe=True, **kw):
    """ Generic chatter function, allowing to write on *any* object that
        inherits mail.thread. We distinguish 2 cases:
            1/ If a token is specified, all logged in users will be able to
            write a message regardless of access rights; if the user is the
            public user, the message will be posted under the name
            of the partner_id of the object (or the public user if there is no
            partner_id on the object).

            2/ If a signed token is specified (`hash`) and also a partner_id
            (`pid`), all post message will
            be done under the name of the partner_id (as it is signed). This
            should be used to avoid leaking
            token to all users.

        Required parameters
        :param string res_model: model name of the object
        :param int res_id: id of the object
        :param string message: content of the message

        Optional keywords arguments:
        :param string token: access token if the object's model uses some kind
        of public access
                             using tokens (usually a uuid4) to bypass access
                             rules
        :param string hash: signed token by a partner if model uses some token
        field to bypass access right
                            post messages.
        :param string pid: identifier of the res.partner used to sign the hash
        :param bool nosubscribe: set False if you want the partner to be set
        as follower of the object when posting (default to True)

        The rest of the kwargs are passed on to message_post()
    """
    record = request.env[res_model].browse(res_id)

    # check if user can post with special token/signed token. The "else" will
    # try to post message with the
    # current user access rights (_mail_post_access use case).
    if token or (_hash and pid):
        pid = int(pid) if pid else False
        if _check_special_access(res_model, res_id, token=token,
                                 _hash=_hash, pid=pid):
            record = record.sudo()
        else:
            raise Forbidden()

    # deduce author of message
    author_id = request.env.user.partner_id.id if request.env.user.partner_id \
        else False

    # Token Case: author is document customer (if not logged) or itself even
    # if user has not the access
    if token:
        if request.env.user._is_public():
            # TODO : After adding the pid and sign_token in access_url when
            # send invoice by email, remove this line
            # TODO : Author must be Public User (to rename to 'Anonymous')
            author_id = record.partner_id.id if hasattr(
                record, 'partner_id') and record.partner_id.id else author_id
        else:
            if not author_id:
                raise NotFound()
    # Signed Token Case: author_id is forced
    elif _hash and pid:
        author_id = pid

    email_from = None
    if author_id and 'email_from' not in kw:
        partner = request.env['res.partner'].sudo().browse(author_id)
        email_from = partner.email_formatted if partner.email else None

    message_post_args = dict(
        body=message,
        message_type=kw.pop('message_type', "comment"),
        subtype=kw.pop('subtype', "mt_comment"),
        author_id=author_id,
        **kw
    )

    # This is necessary as mail.message checks the presence
    # of the key to compute its default email from
    if email_from:
        message_post_args['email_from'] = email_from

    return record.with_context(mail_create_nosubscribe=nosubscribe).\
        message_post(**message_post_args)


class PortalChatter(PortalChatter):

    def _portal_post_filter_params(self):
        return ['token', 'hash', 'pid']

    def _portal_post_check_attachments(self, attachment_ids,
                                       attachment_tokens):
        if len(attachment_tokens) != len(attachment_ids):
            raise UserError(
                _("An access token must be provided for each attachment."))
        for (attachment_id, access_token) in zip(attachment_ids,
                                                 attachment_tokens):
            try:
                CustomerPortal._document_check_access(
                    self, 'ir.attachment', attachment_id, access_token)
            except (AccessError, MissingError):
                raise UserError(
                    _("""The attachment %s does not exist or you do not have
                        the rights to access it.""") % attachment_id)

    @http.route(['/mail/chatter_post'], type='http', methods=['POST'],
                auth='public', website=True)
    def portal_chatter_post(self, res_model, res_id,
                            message, redirect=None, attachment_ids='',
                            attachment_tokens='', **kw):
        """Create a new `mail.message` with the given `message` and/or
        `attachment_ids` and redirect the user to the newly created message.

        The message will be associated to the record `res_id` of the model
        `res_model`. The user must have access rights on this target
        document or must provide valid identifiers through `kw`.
        See `_message_post_helper`.
        """
        url = redirect or (
            request.httprequest.referrer and
            request.httprequest.referrer + "#discussion") or '/my'

        res_id = int(res_id)

        attachment_ids = [int(attachment_id) for attachment_id in
                          attachment_ids.split(',') if attachment_id]
        attachment_tokens = [attachment_token for attachment_token in
                             attachment_tokens.split(
                                 ',') if attachment_token]
        self._portal_post_check_attachments(attachment_ids, attachment_tokens)

        if message or attachment_ids:
            # message is received in plaintext and saved in html
            if message:
                message = plaintext2html(message)
            post_values = {
                'res_model': res_model,
                'res_id': res_id,
                'message': message,
                'send_after_commit': False,
                'attachment_ids': attachment_ids,
            }
            post_values.update((fname, kw.get(fname))
                               for fname in self._portal_post_filter_params())
            message = _message_post_helper(**post_values)

        return request.redirect(url)
