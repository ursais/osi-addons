# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

class SaleEstimateJob(models.Model):
    _name = "sale.estimate.job"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Sales Estimate Job"
    _rec_name = 'number'
    _order = 'id desc'
    
    number = fields.Char(
        'Number',
        copy=False,
    )
    estimate_date = fields.Date(
        'Date',
        required=True,
        copy=False,
        default = fields.date.today(),
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.user.company_id,
        string='Company',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Estimate Sent'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('quotesend', 'Quotation Created'),
        ('cancel', 'Cancelled')],
        default='draft',
        track_visibility='onchange',
        copy='False',
    )
    pricelist_id = fields.Many2one(
        'product.pricelist', 
        string='Pricelist', 
        required=True, 
        help="Pricelist for current sales estimate."
    )
    payment_term_id = fields.Many2one(
        'account.payment.term', 
        string='Payment Terms', 
        oldname='payment_term'
    )
    description = fields.Text(
        string='Description of Work'
    )
    note = fields.Text(
        string='Note'
    )
    currency_id = fields.Many2one(
        "res.currency", 
        related='pricelist_id.currency_id', 
        string="Currency", 
        readonly=True, 
        #required=True,
        store=True,
    )
    estimate_ids = fields.One2many(
        'sale.estimate.line.job',
        'estimate_id',
        'Estimate Lines',
        copy=False,
        domain=[('job_type','=','material')],
    )
    reference = fields.Char(
        string='Customer Reference'
    )
    source = fields.Char(
        string='Source Document'
    )
    total = fields.Float(
        compute='_compute_totalestimate', 
        string='Total Material Estimate', 
        store=True
    )
    user_id = fields.Many2one(
        'res.users',
        'Sales Person',
        default=lambda self: self.env.user,
    )
    team_id = fields.Many2one(
        'crm.team',
        'Sales Team',
    )
    quotation_id = fields.Many2one(
        'sale.order',
        'Sales Quotation',
        readonly=True,
        copy=False,
    )
    
    @api.depends(
        'total',
        'labour_total',
        'overhead_total'
    )
    def _compute_job_estimate_total(self):
        for rec in self:
            rec.estimate_total = rec.total + rec.labour_total + rec.overhead_total
            
    @api.depends('labour_estimate_line_ids.price_subtotal')
    def _compute_labour_total(self):
        for rec in self:
            for line in rec.labour_estimate_line_ids:
                rec.labour_total += line.price_subtotal
                
    @api.depends('overhead_estimate_line_ids.price_subtotal')
    def _compute_overhead_total(self):
        for rec in self:
            for line in rec.overhead_estimate_line_ids:
                rec.overhead_total += line.price_subtotal

    project_id = fields.Many2one(
        'project.project',
        string="Project"
    )
    labour_estimate_line_ids = fields.One2many(
        'sale.estimate.line.job',
        'estimate_id',
        copy=False,
        domain=[('job_type','=','labour')],
    )
    overhead_estimate_line_ids = fields.One2many(
        'sale.estimate.line.job',
        'estimate_id',
        copy=False,
        domain=[('job_type','=','overhead')],
    )
    analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        store=True,
        related="project_id.analytic_account_id",
    )
    labour_total = fields.Float(
        compute='_compute_labour_total', 
        string='Total Labour Estimate', 
        store=True
    )
    overhead_total = fields.Float(
        compute='_compute_overhead_total', 
        string='Total Overhead Estimate', 
        store=True
    )
    estimate_total = fields.Float(
        string='Total Job Estimate',
        compute='_compute_job_estimate_total',
        store=True,
    )
    job_type_ids = fields.Many2many(
        'estimate.job.type',
        string='Job Types',
    )
    @api.depends('estimate_ids.price_subtotal')
    def _compute_totalestimate(self):
        for rec in self:
            for line in rec.estimate_ids:
                rec.total += line.price_subtotal
        
    @api.onchange('partner_id')
    def _onchange_customer_id(self):
        for rec in self:
            partner = self.env['res.partner'].browse(rec.partner_id.id)
            rec.pricelist_id = partner.property_product_pricelist.id
            rec.payment_term_id = partner.property_payment_term_id.id
            
    @api.multi
    def estimate_send(self):
        for rec in self:
            rec.state = 'sent'
            
    @api.multi
    def estimate_confirm(self):
        for rec in self:
            if not rec.estimate_ids:
                raise UserError(_('Please enter Estimation Lines!'))
            rec.state = 'confirm'
            
    @api.multi
    def estimate_approve(self):
        for rec in self:
            rec.state = 'approve'
            
    @api.multi
    def estimate_quotesend(self):
        for rec in self:
            rec.state = 'quotesend'
            
    @api.multi
    def estimate_cancel(self):
        for rec in self:
            rec.state = 'cancel'
        
    @api.multi
    def estimate_reject(self):
        for rec in self:
            rec.state = 'reject'
            
    @api.multi
    def reset_todraft(self):
        for rec in self:
            rec.state = 'draft'
            
    @api.model
    def create(self, vals):
        number = self.env['ir.sequence'].next_by_code('product.estimate.seq.job')
        vals.update({
            'number': number
            })
        res = super(SaleEstimateJob, self).create(vals)
        return res
        
    @api.multi
    def action_estimate_send(self):
        if self.state == 'sent' or self.state == 'approve' or self.state == 'quotesend' or self.state == 'confirm':
            '''
            This function opens a window to compose an email, with the edi sale template message loaded by default
            '''
            #self.state = 'sent'
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('job_cost_estimate_customer', 'email_template_estimate_job')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict()
            ctx.update({
                'default_model': 'sale.estimate.job',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                #'custom_layout': "sale.mail_template_data_notification_email_sale_order"
            })
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
        if self.state == 'draft':
            '''
            This function opens a window to compose an email, with the edi sale template message loaded by default
            '''
            self.state = 'sent'
            self.ensure_one()
            ir_model_data = self.env['ir.model.data']
            try:
                template_id = ir_model_data.get_object_reference('job_cost_estimate_customer', 'email_template_estimate_job')[1]
            except ValueError:
                template_id = False
            try:
                compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
            except ValueError:
                compose_form_id = False
            ctx = dict()
            ctx.update({
                'default_model': 'sale.estimate.job',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_composition_mode': 'comment',
                'mark_so_as_sent': True,
                #'custom_layout': "sale.mail_template_data_notification_email_sale_order"
            })
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
                'context': ctx,
            }
        
    @api.multi
    def _prepare_quotation_line(self,quotation):
        quo_line_obj = self.env['sale.order.line']
        for rec in self:
            for line in rec.estimate_ids:
                vals1 = {
                                'product_id':  line.product_id.id,
                                'product_uom_qty': line.product_uom_qty,
                                'product_uom': line.product_uom.id,
                                'price_unit' : line.price_unit,
                                'price_subtotal': line.price_subtotal,
                                'name' : line.product_description,
                                'price_total' : self.total,
                                'discount' : line.discount,
                                'order_id':quotation.id,
                                }
                quo_line = quo_line_obj.create(vals1)
            for line in rec.labour_estimate_line_ids:
                vals1 = {
                                'product_id':  line.product_id.id,
                                'product_uom_qty': line.product_uom_qty,
                                'product_uom': line.product_uom.id,
                                'price_unit' : line.price_unit,
                                'price_subtotal': line.price_subtotal,
                                'name' : line.product_description,
                                'price_total' : self.total,
                                'discount' : line.discount,
                                'order_id':quotation.id,
                                }
                quo_line = quo_line_obj.create(vals1)
                
            for line in rec.overhead_estimate_line_ids:
                vals1 = {
                                'product_id':  line.product_id.id,
                                'product_uom_qty': line.product_uom_qty,
                                'product_uom': line.product_uom.id,
                                'price_unit' : line.price_unit,
                                'price_subtotal': line.price_subtotal,
                                'name' : line.product_description,
                                'price_total' : self.total,
                                'discount' : line.discount,
                                'order_id':quotation.id,
                                }
                quo_line = quo_line_obj.create(vals1)
        
    @api.multi
    def estimate_to_quotation(self):
        quo_obj = self.env['sale.order']
        quo_line_obj = self.env['sale.order.line']
        for rec in self:
            vals = {
                'partner_id':rec.partner_id.id,
                'origin': rec.number,
                'project_id':rec.analytic_id.id
                }
            quotation = quo_obj.create(vals)
            rec._prepare_quotation_line(quotation)
            rec.quotation_id = quotation.id
        rec.state = 'quotesend'
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
