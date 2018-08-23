# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, fields, models
import codecs
import csv
from io import StringIO

_logger = logging.getLogger(__name__)


class SupplierCostPriceWizard(models.TransientModel):
    _name = 'supplier.cost.price.wizard'
    _description = 'Wizard to update supplier cost price for Product'

    @api.multi
    def _get_default_product_uom(self):
        return self.env.ref('product.product_uom_unit')

    csv_file = fields.Binary(
        string='Import File (csv):',
        filename="*.csv",
        required=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True
    )
    product_uom = fields.Many2one(
        'product.uom',
        string='UoM',
        default=_get_default_product_uom
    )

    @api.multi
    def _prepare_supplierinfo_product(
            self, product_id, partner_id, product_uom, price):
        return {
            'name': partner_id and partner_id.id,
            'sequence': 10,
            'delay': 1,
            'min_qty': 1.0,
            'company_id': self.env.user.company_id.id,
            'product_uom': product_uom.id,
            'product_tmpl_id': product_id.product_tmpl_id.id,
            'price': price
        }

    @api.multi
    def action_update_supplier_cost_price(self):
        for wizard in self:
            csv.field_size_limit(1000000000)
            data = codecs.decode(wizard.csv_file, 'base64')
            input = StringIO.StringIO(data)
            input.seek(0)
            rows = csv.DictReader(input)
            for row in rows:
                if row['Cost Price']:
                    if float(row['Cost Price']) > 0.0:
                        # Search product reference
                        product_id = self.env['product.product'].search(
                            [('default_code', '=', row['Internal Reference'])])
                        if product_id:
                            # Check whether product has suppliers
                            if product_id.seller_ids:
                                product_supplierinfo = \
                                    self.env['product.supplierinfo'].search(
                                        [('name', '=', wizard.partner_id.id),
                                         ('product_tmpl_id', '=',
                                          product_id.product_tmpl_id.id)])
                                if product_supplierinfo:
                                    # Update pricelist partner information
                                    product_supplierinfo.write({
                                        'min_qty': 1,
                                        'price': float(row['Cost Price'])})
                                    product_id._cr.commit()
                                    _logger.info(
                                        u"IMPORT supplier price of %s from %s "
                                        u"to %s $.", product_id.name,
                                        wizard.partner_id.name,
                                        row['Cost Price'])
                                # Create supplier information
                                else:
                                    # Update product supplier information
                                    product_id.write({
                                        'seller_ids': [(
                                            0, 0,
                                            self._prepare_supplierinfo_product(
                                                product_id,
                                                wizard.partner_id,
                                                wizard.product_uom,
                                                float(row['Cost Price'])))]})
                                    product_id._cr.commit()
                                    _logger.info(u"IMPORT supplier price of %s"
                                                 u" from %s to %s $.",
                                                 product_id.name,
                                                 wizard.partner_id.name,
                                                 row['Cost Price'])
                            else:
                                # Update product supplier information
                                product_id.write({
                                    'seller_ids': [(
                                        0, 0,
                                        self._prepare_supplierinfo_product(
                                            product_id,
                                            wizard.partner_id,
                                            wizard.product_uom,
                                            float(row['Cost Price'])))]})
                                product_id._cr.commit()
                                _logger.info(u"IMPORT supplier price of %s "
                                             u"from %s to %s $.",
                                             product_id.name,
                                             wizard.partner_id.name,
                                             row['Cost Price'])
        return True
