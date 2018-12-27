# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError

template = "Hi, \n" \
           "\nA Purchase {request} created with the following information: " \
           "\n\n\tSupplier: \t\t {partner_name} " \
           "\n\tVendor Reference: \t {partner_ref} " \
           "\n\tScheduled Date: \t {date_planned} " \
           "\n\tPayment Term: \t\t {payment_term} " \
           "\n\tAmount Total: \t\t {total} " \
           "\n\nThank you," \
           "\n{user_name}"

user_approve_error = "User does not have access to approve purchase order " \
                     "or the order amount is higher."


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('purchase rfq', 'Purchase Request'),
        ('draft', 'Draft Order/RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'Purchase Approve'),
        ('co approve', 'Purchase Co-approval'),
        ('purchase', 'Purchase Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False,
        default='purchase rfq', track_visibility='onchange',
    )
    po_type = fields.Selection(
        selection=[('inventory', 'Inventory'),
                   ('non-inventory', 'Non Inventory')],
        string='PO Type',
        default='inventory',
        required=True,
    )

    @api.multi
    def copy(self, default=None):
        new_po = super(PurchaseOrder, self).copy(default=default)
        # not generic
        if not new_po.partner_id.generic_flag and new_po.state == 'draft':
            new_po.write({'state': 'draft'})
        return new_po

    @api.multi
    def check_manager_approval_chain(self, employee, amount_total):
        # Find approval manager from the list of approval managers.
        parent_id = employee.parent_id
        cc = ''
        while (parent_id):
            if parent_id.user_id:
                # Set domain
                domain = [('user_id', '=', parent_id.user_id.id),
                          ('po_type', '=', self.po_type)]
                # Search Purchase approval
                purchase_approvals_ids = self.env['purchase.approval'].search(
                    domain)
                if purchase_approvals_ids:
                    for purchase_approval in purchase_approvals_ids:
                        if amount_total <= purchase_approval.approval_amount:
                            found = True
                        else:
                            found = False
                    if found:
                        return (parent_id.work_email, cc)
                    else:
                        if cc:
                            cc += ',' + parent_id.work_email
                        else:
                            cc = parent_id.work_email
                        parent_id = parent_id.parent_id
                else:
                    parent_id = False
            else:
                parent_id = False
        return

    @api.multi
    def check_supervisor_chain(self, approval_list):
        user_email = self.env.user.email

        # Check whether logged User has email address or not
        if not user_email:
            raise UserError(_(
                "Unable to send email to supervisor, please configure the "
                "sender's email address or alias."))
        new_approval_list = approval_list

        # Search for Employee's Manager and send email to him
        domain = [('user_id', '=', self.env.user.id)]
        employee_ids = self.env['hr.employee'].search(domain)

        supervisor_id = employee_ids.parent_id
        while supervisor_id:

            found = False
            for purchase_approval in approval_list:
                if (not found and
                        purchase_approval.employee_id == supervisor_id and
                        supervisor_id.work_email):
                    new_approval_list = []
                    new_approval_list.append(purchase_approval)
                    found = True
            if not found:
                supervisor_id = supervisor_id.parent_id
            else:
                break

        return new_approval_list

    @api.multi
    def send_supervisor_email(self, res):
        user_email = self.env.user.email

        # Check whether logged User has email address or not
        if not user_email:
            raise UserError(_(
                "Unable to send email to supervisor, please configure the "
                "sender's email address or alias."))

        # Search for Employee's Manager and send email to him
        domain = [('user_id', '=', self.env.user.id)]
        employee_ids = self.env['hr.employee'].search(domain)
        mail_ids = email_cc_list = []

        for employee in employee_ids:
            if employee.parent_id:
                # Send email to department manager for review PO
                if res.state == 'purchase rfq':
                    email_to = employee.parent_id.work_email
                else:
                    # Check Manager chain to approve PO
                    email_to, email_cc_list = \
                        self.check_manager_approval_chain(employee,
                                                          res.amount_total)
                if not email_to:
                    return
                # Build body content
                body = template.format(
                    request='request',
                    partner_name=res.partner_id.name,
                    partner_ref=res.partner_ref or '',
                    date_planned=res.date_planned,
                    payment_term=res.payment_term_id.name or '',
                    total=res.amount_total,
                    user_name=self.env.user.name
                )
                # Prepare email
                mail_vals = {
                    'state': 'outgoing',
                    'subject': 'Re: Need your approval for Purchase (%s) '
                               'request' % str(res.name),
                    'body_html': '<pre>%s</pre>' % str(body),
                    'email_to': email_to,
                    'email_from': user_email,
                    'model': 'purchase.order',
                    'res_id': res.id,
                }

                if email_cc_list:
                    mail_vals.update({'email_cc': email_cc_list})

                # Create mail message and send email
                mail_ids.append(self.env['mail.mail'].create(mail_vals))
                mail_ids[0].send(auto_commit=True)
                # Add message to chatter area
                for purchase in res:
                    purchase.message_post(
                        body=_('Sent email to supervisor - %s for PR approval.'
                               '') % employee.parent_id.name)
                break
        return

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        # Check head department create Purchase order
        if self.user_has_groups(
                'osi_purchase_workflow_customization.'
                'group_purchase_approve_request'):
            res.state = 'draft'
            return res
        # Send email to supervisor
        self.send_supervisor_email(res)
        return res

    @api.multi
    def button_draft_po(self):
        for purchase in self:
            # Supervisor approves the purchase request
            purchase.write({'state': 'draft'})
            # Add message to chatter area
            purchase.message_post(
                body=_('Request approved by %s') % (self.env.user.name))
        return {}

    @api.multi
    def co_approval_is_needed(self, amount):

        domain = [
            ('co_approval_amount', '<', amount),
            ('co_approval_amount', '!=', 0),
            ('po_type', '=', self.po_type)
        ]
        purchase_approvals_ids = self.env['purchase.approval'].search(domain)
        if purchase_approvals_ids:
            return True
        else:
            return False

    @api.multi
    def button_to_request_approve(self):
        # Search for User and PO type related Purchase approvals
        domain = [('user_id', '=', self.env.user.id),
                  ('po_type', '=', self.po_type)]
        purchase_approvals_ids = self.env['purchase.approval'].search(domain)

        # User does not have coapprove access
        if not purchase_approvals_ids:
            raise UserError(_("%s") % user_approve_error)

        # Compare Purchase amount total with Employee's Purchase
        # Approval amount
        for purchase_approval in purchase_approvals_ids:
            # Request is valid
            if self.amount_total <= purchase_approval.approval_amount:
                self.write({'state': 'to approve'})
            # User does not have approve amount
            else:
                # Send email to supervisor
                self.send_supervisor_email(self)
        return {}

    @api.multi
    def button_to_approve(self):
        # Restrict to approves own non inventory items
        if (self.env.user == self.create_uid and
                self.po_type == 'non-inventory'):
            raise UserError(_("You are not allowed to approve your own PO's "
                              "for non inventory items!"))
        # Search for User and PO type related Purchase approvals
        domain = [('user_id', '=', self.env.user.id),
                  ('po_type', '=', self.po_type)]
        purchase_approvals_ids = self.env['purchase.approval'].search(domain)

        # User does not have coapprove access
        if not purchase_approvals_ids:
            raise UserError(_("%s") % user_approve_error)

        # Compare Purchase amount total with Employee's Purchase
        # Approval amount
        for purchase_approval in purchase_approvals_ids:
            # PO first approve
            if self.amount_total <= purchase_approval.approval_amount:
                # Check for co-approval
                if self.co_approval_is_needed(self.amount_total):
                    self.write({'state': 'co approve'})
                    # Add message to chatter area
                    self.message_post(body=_(
                        'Purchase order approved by %s') % self.env.user.name)
                # No co-approval is needed, so order is automatically
                # confirmed on 1st approval
                else:
                    self.with_context(check_not_needed=True).button_confirm()
            # User does not have approve amount
            else:
                raise UserError(_("%s") % user_approve_error)
        return {}

    @api.multi
    def button_co_approve(self):
        # Search for User and PO type related Purchase approvals
        domain = [('user_id', '=', self.env.user.id),
                  ('po_type', '=', self.po_type)]
        purchase_approvals_ids = self.env['purchase.approval'].search(domain)

        # User does not have coapprove access
        if not purchase_approvals_ids:
            raise UserError(_("%s") % user_approve_error)

        # Compare Purchase amount total with Employee's Purchase
        # Co Approval amount
        if purchase_approvals_ids:
            for purchase_approval in purchase_approvals_ids:
                # PO co-approve, PO is automatically confirmed.
                if self.amount_total <= purchase_approval.co_approval_amount:
                    self.write({'state': 'draft'})
                    # Add message to chatter area
                    self.message_post(body=_(
                        'Purchase order co-approved by %s'
                        '') % self.env.user.name)
                    self.with_context(check_not_needed=True).button_confirm()
                # User does not have co-approval amount needed
                else:
                    raise UserError(_("%s") % user_approve_error)
        return {}

    @api.multi
    def check_approval(self):
        # Restrict to approves own non inventory items
        if (self.env.user == self.create_uid and
                self.po_type == 'non-inventory'):
            raise UserError(_("You are not allowed to approve your own PO's "
                              "for non inventory items!"))

        approved = False
        coapproved = False

        # Search for User and PO type related Purchase approvals
        domain = [('user_id', '=', self.env.user.id),
                  ('po_type', '=', self.po_type),
                  ('approval_amount', '>=', self.amount_total)]

        self_purchase_approvals_ids = self.env['purchase.approval'].search(
            domain)

        # Search for Purchase Appovals users whose amount is greater
        # than Purchase request amount and PO type
        domain = [('approval_amount', '>=', self.amount_total),
                  ('po_type', '=', self.po_type)]

        purchase_approvals_ids = self.env['purchase.approval'].search(
            domain)

        if not purchase_approvals_ids:
            raise UserError(_(
                'Approvals list undefined.'))

        # Compare Purchase amount total with Employee's Purchase
        # Approval amount
        for purchase_approval in self_purchase_approvals_ids:

            # Everything ok
            if self.amount_total <= purchase_approval.approval_amount:
                if self.co_approval_is_needed(self.amount_total):
                    self.write({'state': 'co approve'})
                    self.message_post(
                        body=_('Purchase order sent for co-approval.'))
                    coapproved = True
                else:
                    approved = True

        # Send email for a high authority Users for PO request approval
        if not approved and not coapproved:
            user_email = self.env.user.email

            # Check whether logged User has email address or not
            if not user_email:
                raise UserError(_(
                    "Unable to send email, please configure the sender's "
                    "email address or alias."))

            # check for supervisor chain on the approvals_ids
            purchase_approvals_ids = self.check_supervisor_chain(
                purchase_approvals_ids)
            if purchase_approvals_ids:
                for purchase_approval in purchase_approvals_ids:
                    # Check for Employee work email address
                    if purchase_approval.employee_id.work_email:
                        # Build body content
                        body = template.format(
                            request='order',
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
                            'subject': 'Purchase order (%s) needs your '
                                       'approval' % str(self.name),
                            'body_html': '<pre>%s</pre>' % str(body),
                            'email_to':
                                purchase_approval.employee_id.work_email,
                            'email_from': user_email,
                            'model': 'purchase.order',
                            'res_id': self.id,
                        }

                        # Create mail message
                        mail = self.env['mail.mail'].create(mail_vals)

                        mail.send(auto_commit=True)

                        # Add message to chatter area
                        self.message_post(body=_(
                            'Purchase order sent for approval to %s.') % (
                                purchase_approval.employee_id.name))

                self.write({'state': 'to approve'})

            else:
                self.message_post(
                    body=_('No approvers found for this PO'))

        return approved

    @api.multi
    def button_confirm(self):

        if not self.env.context.get('check_not_needed', False):
            is_approve = self.check_approval()
        else:
            is_approve = True

        if is_approve:
            # Core method doesn't allow "to approve" state PO's to be confirmed
            if self.state not in ('draft', 'sent'):
                self.state = 'draft'
            return super(PurchaseOrder, self).button_confirm()
        else:
            return False
