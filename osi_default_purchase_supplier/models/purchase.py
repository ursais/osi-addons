# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from lxml import etree
from odoo.osv.orm import setup_modifiers
from odoo.exceptions import UserError, ValidationError, Warning

template = "Hi, \n" \
           "\nA Purchase order is ready with the following information: \n" \
           "\n\tSupplier: \t\t {partner_name} " \
           "\n\tVendor Reference: \t {partner_ref} " \
           "\n\tScheduled Date: \t {date_planned} " \
           "\n\tPayment Term: \t\t {payment_term} " \
           "\n\tAmount Total: \t\t {total} " \
           "\n\nPlease review and clear the final verification flag." \
           "\n\nThank you," \
           "\n{user_name}"


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _get_generic_partner(self):
        generic_partner_ids = self.env['res.partner'].search(
            [('generic_flag', '=', True)], limit=1)
        if generic_partner_ids:
            return generic_partner_ids
        else:
            raise UserError(
                _('At least one generic supplier must be defined.'))

    @api.model
    def _get_print_btn_flag(self):
        self.print_btn_flag = False
        self.confirm_btn_flag = False
        if self.user_has_groups('purchase.group_purchase_user'):
            self.print_btn_flag = True
            self.confirm_btn_flag = True

    @api.model
    def _compute_am_i_requester(self):
        if self.create_uid == self.env.user:
            self.am_i_requester = True
        else:
            self.am_i_requester = False

    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True,
        states={'confirmed': [('readonly', True)],
                'approved': [('readonly', True)],
                'done': [('readonly', True)]},
        default=_get_generic_partner,
        track_visibility='onchange'
    )
    print_btn_flag = fields.Boolean(
        default='_get_print_btn_flag',
        string="Print Button Flag",
        copy=False
    )
    confirm_btn_flag = fields.Boolean(
        default='_get_print_btn_flag',
        string="Confirm Button Flag",
        copy=False
    )
    final_verification_flag = fields.Boolean(
        default=False,
        string="Verify Order before confirmation",
        copy=False,
        track_visibility='onchange'
    )
    am_i_requester = fields.Boolean(
        compute='_compute_am_i_requester',
        string="Requester ?",
        copy=False
    )

    @api.onchange('partner_id', 'company_id')
    def onchange_partner_id(self):
        """ If partner is generic than set flag for hiding buttons """
        super(PurchaseOrder, self).onchange_partner_id()

        self.print_btn_flag = False
        self.confirm_btn_flag = False

        if self.partner_id.generic_flag:
            self.print_btn_flag = True
            self.confirm_btn_flag = True

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False,
                        submenu=False):
        """ Only purchase manager can select any partner and
            purchase user can not select any other partner
        """
        res = super(PurchaseOrder, self).fields_view_get(view_id=view_id,
                                                         view_type=view_type,
                                                         toolbar=toolbar,
                                                         submenu=submenu)

        doc = etree.XML(res['arch'])

        manager = self.user_has_groups('purchase.group_purchase_manager')
        user = self.user_has_groups('purchase.group_purchase_user')
        admins = self.env['res.users'].search([('login', 'ilike', 'admin')])

        for field in res['fields']:
            if field == 'partner_id':
                if manager or user or self.env.uid in admins:
                    for node in doc.xpath("//field[@name='partner_id']"):
                        node.set('readonly', '0')
                        setup_modifiers(node, res['fields']['partner_id'])
                else:
                    for node in doc.xpath("//field[@name='partner_id']"):
                        node.set('readonly', '1')
                        setup_modifiers(node, res['fields']['partner_id'])
        res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def generic_lines(self):
        res = False
        for line in self.order_line:
            if (line.product_id.generic_flag or
                    line.product_id.product_tmpl_id.generic_flag):
                res = True
                break
        return res

    @api.multi
    def button_confirm(self):

        res = False

        if self.generic_lines():
            raise ValidationError(
                _('Generic product exists. Order cannot be confirmed.'))

        # Order requires final verification by the requester
        # before it can be confirmed
        if self.final_verification_flag:

            mail_ids = []

            body = template.format(
                partner_name=self.partner_id.name,
                partner_ref=self.partner_ref or '',
                date_planned=self.date_planned,
                payment_term=self.payment_term_id.name or '',
                total=self.amount_total,
                user_name=self.env.user.name
            )

            # Prepare email
            mail_vals = {
                'state': 'outgoing',
                'subject': 'Purchase order (%s) ready for verification'
                           '' % str(self.name),
                'body_html': '<pre>%s</pre>' % str(body),
                'email_to': self.create_uid.email,
                'email_from': self.env.user.email,
                'res_id': self.id,
                'model': 'purchase.order'
            }

            # Create mail message
            mail_ids.append(self.env['mail.mail'].create(mail_vals))

            if mail_ids:

                # Send mail one by one
                for mail in mail_ids:
                    mail.send(auto_commit=True)

                # Add message to chatter area
                self.message_post(body=_(
                    'Purchase order ready for final verification by '
                    'requester.'))

            raise Warning(_('Requester needs to verify order. '
                            'Email sent to requester.'))

        else:
            res = super(PurchaseOrder, self).button_confirm()
            self.write({
                'print_btn_flag': False,
                'confirm_btn_flag': False
            })

        return res

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}

        default['print_btn_flag'] = False
        default['confirm_btn_flag'] = False
        default['group_id'] = False

        new_po = super(PurchaseOrder, self).copy(default=default)

        return new_po

    @api.model
    def create(self, vals):

        # To make sure that a PO generated by Scheduler enables user to confirm
        # If not set properly, user can't confirm that PO.
        res = super(PurchaseOrder, self).create(vals)

        if not res.partner_id.generic_flag:
            res.print_btn_flag = False
            res.confirm_btn_flag = False

        return res
