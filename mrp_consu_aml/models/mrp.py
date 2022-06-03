# Copyright (C) 2019 Open Source Integrators
# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
from collections import defaultdict
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import date_utils, float_compare, float_round, float_is_zero


class OSIaml(models.Model):
	_inherit = "account.move.line"

	osi_is_consu= fields.Boolean(string="Is Consumable")

class OSImrp(models.Model):
	_inherit = "mrp.production"

	def run_consu_aml(self):
		pc_array=self.env['report.mrp_account_enterprise.mrp_cost_structure'].get_lines(self)
		#temp=[]
		#for p in pc_array:
		#	if p['product']['type']=='consu':
		#		temp.append(p)
		#pc_array=temp
		je=self.env['account.move'].search([('ref','ilike',self.name),('state','=','posted')],limit=1,order='id desc')
		if len(je)==0:
			return False
		move_line_ids=je.mapped('line_ids').filtered(lambda x: x['osi_is_consu']==True)
		self.env.context.check_move_validity=False
		total_cost=sum(x['total_cost'] for x in pc_array)
		to_make=[]
		for pc in pc_array['raw_material_moves']:
			product=pc['product_id']
			cost=pc['cost']
			found=False
			for line in move_line_ids:
				if product['id']==line['product_id']['id'] and cost!=line['credit'] and line['debit']==0:
					line['credit']=cost
					found=True
					break
			if not found:
				if product.property_account_expense_id.id:
					account_id=product.property_account_expense_id.id
				elif product.categ_id.property_account_expense_categ_id.id:
					account_id=product.categ_id.property_account_expense_categ_id.id
				else:
					raise UserError(("Missing account for product %s") % product['name'])
				to_make.append({
				'account_id':account_id,
				'credit':cost,
				'product_id':product['id'],
				'move_id':je.id,
				'osi_is_consu':True,
				'company_id':self.company_id.id,
				'name':self.name + ' - ' + product['name'],
				})
			out_line=move_line_ids.filtered(lambda x: x['debit']!=0 and x['product_id']['id']==product['id'])
			if len(out_line)>0:
				out_line.write({'debit':cost/len(out_line)})
			else:
				to_make.append({
				'account_id':je.mapped('line_ids').filtered(lambda x: x['debit']!=0)[0]['account_id']['id'],
				'debit':cost,
				'product_id':product['id'],
				'move_id':je.id,
				'osi_is_consu':True,
				'company_id':self.company_id.id,
                                'name':self.name + ' - ' + product['name'],
				})
		je.button_draft()
		self.env.context.check_move_validity=False
		self.env['account.move.line'].create(to_make)
		je.action_post()
		return False
	
	def button_mark_done(self):
		self.ensure_one()
		self._check_company()
		for wo in self.workorder_ids:
			if wo.time_ids.filtered(lambda x: (not x.date_end) and (x.loss_type in ('productive', 'performance'))):
				raise UserError(_('Work order %s is still running') % wo.name)
		self._check_lots()

		self.post_inventory()
		# Moves without quantity done are not posted => set them as done instead of canceling. In
		# case the user edits the MO later on and sets some consumed quantity on those, we do not
		# want the move lines to be canceled.
		(self.move_raw_ids | self.move_finished_ids).filtered(lambda x: x.state not in ('done', 'cancel')).write({
			'state': 'done',
			'product_uom_qty': 0.0,
		})
		self.run_consu_aml()
		return self.write({'date_finished': fields.Datetime.now()})

class OSImrp(models.Model):
	_inherit = "mrp.unbuild"
	
	def action_unbuild(self):
		self.ensure_one()
		self._check_company()
		if self.product_id.tracking != 'none' and not self.lot_id.id:
			raise UserError(_('You should provide a lot number for the final product.'))

		if self.mo_id:
			if self.mo_id.state != 'done':
				raise UserError(_('You cannot unbuild a undone manufacturing order.'))

		consume_moves = self._generate_consume_moves()
		consume_moves._action_confirm()
		produce_moves = self._generate_produce_moves()
		produce_moves._action_confirm()

		finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
		consume_moves -= finished_moves

		if any(produce_move.has_tracking != 'none' and not self.mo_id for produce_move in produce_moves):
			raise UserError(_('Some of your components are tracked, you have to specify a manufacturing order in order to retrieve the correct components.'))

		if any(consume_move.has_tracking != 'none' and not self.mo_id for consume_move in consume_moves):
			raise UserError(_('Some of your byproducts are tracked, you have to specify a manufacturing order in order to retrieve the correct byproducts.'))

		for finished_move in finished_moves:
			if finished_move.has_tracking != 'none':
				self.env['stock.move.line'].create({
					'move_id': finished_move.id,
					'lot_id': self.lot_id.id,
					'qty_done': finished_move.product_uom_qty,
					'product_id': finished_move.product_id.id,
					'product_uom_id': finished_move.product_uom.id,
					'location_id': finished_move.location_id.id,
					'location_dest_id': finished_move.location_dest_id.id,
				})
			else:
				finished_move.quantity_done = finished_move.product_uom_qty

		# TODO: Will fail if user do more than one unbuild with lot on the same MO. Need to check what other unbuild has aready took
		qty_already_used = defaultdict(float)
		for move in produce_moves | consume_moves:
			if move.has_tracking != 'none':
				original_move = move in produce_moves and self.mo_id.move_raw_ids or self.mo_id.move_finished_ids
				original_move = original_move.filtered(lambda m: m.product_id == move.product_id)
				needed_quantity = move.product_uom_qty
				moves_lines = original_move.mapped('move_line_ids')
				if move in produce_moves and self.lot_id:
					moves_lines = moves_lines.filtered(lambda ml: self.lot_id in ml.produce_line_ids.lot_id)  # FIXME sle: double check with arm
				for move_line in moves_lines:
					# Iterate over all move_lines until we unbuilded the correct quantity.
					taken_quantity = min(needed_quantity, move_line.qty_done - qty_already_used[move_line])
					if taken_quantity:
						self.env['stock.move.line'].create({
							'move_id': move.id,
							'lot_id': move_line.lot_id.id,
							'qty_done': taken_quantity,
							'product_id': move.product_id.id,
							'product_uom_id': move_line.product_uom_id.id,
							'location_id': move.location_id.id,
							'location_dest_id': move.location_dest_id.id,
						})
						needed_quantity -= taken_quantity
						qty_already_used[move_line] += taken_quantity
			else:
				move.quantity_done = float_round(move.product_uom_qty, precision_rounding=move.product_uom.rounding)

		finished_moves._action_done()
		consume_moves._action_done()
		produce_moves._action_done()
		produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.qty_done > 0)
		consume_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
		if self.mo_id:
			unbuild_msg = _(
				"%s %s unbuilt in", self.product_qty, self.product_uom_id.name) + " <a href=# data-oe-model=mrp.unbuild data-oe-id=%d>%s</a>" % (self.id, self.display_name)
			self.mo_id.message_post(
				body=unbuild_msg,
				subtype_id=self.env.ref('mail.mt_note').id)
		self.mo_id.run_consu_aml()
		return self.write({'state': 'done'})
