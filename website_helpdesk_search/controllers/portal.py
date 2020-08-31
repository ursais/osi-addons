# Copyright (C) 2020 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json


from odoo import http, _
from odoo.http import request
from odoo.tools import consteq
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortal(CustomerPortal):

    @http.route(
        '/portal/attachment/add', type='http', auth='public',
        methods=['POST'], website=True)
    def attachment_add(self, name, file, res_model,
                       res_id, access_token=None, **kwargs):
        """Process a file uploaded from.

        The portal chatter and create the
        corresponding `ir.attachment`.

        The attachment will be created "pending" until the associated message
        is actually created, and it will be garbage collected otherwise.

        :param name: name of the file to save.
        :type name: string

        :param file: the file to save
        :type file: werkzeug.FileStorage

        :param res_model: name of the model of the original document.
            To check access rights only, it will not be saved here.
        :type res_model: string

        :param res_id: id of the original document.
            To check access rights only, it will not be saved here.
        :type res_id: int

        :param access_token: access_token of the original document.
            To check access rights only, it will not be saved here.
        :type access_token: string

        :return: attachment data {id, name, mimetype, file_size, access_token}
        :rtype: dict
        """
        try:
            self._document_check_access(res_model, int(res_id),
                                        access_token=access_token)
        except (AccessError, MissingError) as e:
            raise UserError(
                _("The document does not exist or you do not have the "
                    "rights to access it."))

        ir_attachment = request.env['ir.attachment']
        access_token = False

        # Avoid using sudo or creating access_token when not necessary:
        # internal
        # users can create attachments, as opposed to public and portal users.
        if not request.env.user.has_group('base.group_user'):
            ir_attachment = ir_attachment.sudo().with_context(
                binary_field_real_user=ir_attachment.env.user)
            access_token = ir_attachment._generate_access_token()

        # At this point the related message does not exist yet, so we assign
        # those specific res_model and res_is. They will be correctly set
        # when the message is created: see `portal_chatter_post`,
        # or garbage collected otherwise: see  `_garbage_collect_attachments`.
        attachment = ir_attachment.create({
            'name': name,
            'datas': base64.b64encode(file.read()),
            'res_model': 'mail.compose.message',
            'res_id': 0,
            'access_token': access_token,
        })
        return request.make_response(
            data=json.dumps(attachment.read(
                ['id', 'name', 'mimetype', 'file_size', 'access_token'])[0]),
            headers=[('Content-Type', 'application/json')]
        )

    def _document_check_access(self, model_name,
                               document_id, access_token=None):
        document = request.env[model_name].browse([document_id])
        document_sudo = document.sudo().exists()
        if not document_sudo:
            raise MissingError(_("This document does not exist."))
        try:
            document.check_access_rights('read')
            document.check_access_rule('read')
        except AccessError:
            if not access_token or not document_sudo.access_token or not \
                    consteq(document_sudo.access_token, access_token):
                raise
        return document_sudo

    @http.route('/portal/attachment/remove', type='json', auth='public')
    def attachment_remove(self, attachment_id, access_token=None):
        """Remove the given `attachment_id`, only if it is in a "pending"
        state.

        The user must have access right on the attachment or provide a valid
        `access_token`.
        """
        try:
            attachment_sudo = self._document_check_access(
                'ir.attachment', int(attachment_id), access_token=access_token)
        except (AccessError, MissingError) as e:
            raise UserError(
                _("The attachment does not exist or you do not have the "
                    "rights to access it."))

        if attachment_sudo.res_model != 'mail.compose.message' or \
                attachment_sudo.res_id != 0:
            raise UserError(
                _("The attachment %s cannot be removed because it is not in "
                    "a pending state.") % attachment_sudo.name)

        if attachment_sudo.env['mail.message'].search([
                ('attachment_ids', 'in', attachment_sudo.ids)]):
            raise UserError(
                _("The attachment %s cannot be removed because it "
                    "is linked to a message.") % attachment_sudo.name)

        return attachment_sudo.unlink()
