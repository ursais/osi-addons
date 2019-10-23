# Copyright (C) 2019 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo.tests import common
from datetime import datetime


class TestStockRequest(common.TransactionCase):

    def setUp(self):
        super(TestStockRequest, self).setUp()

        # common models
        self.test_location = self.env.ref('fieldservice.test_location')

        self.request_order = self.env['stock.request.order']
        self.main_company = self.env.ref('base.main_company')
        self.warehouse = self.env.ref('stock.warehouse0')

        self.product_id = self.env['product.product'].create(
            dict(name='CODEA1', default_code='Product A1',
                 uom_id=self.env.ref('uom.product_uom_unit').id,
                 company_id=self.main_company.id, type='product'))

        self.order = self.env['fsm.order'].create(
            {'location_id': self.test_location.id})

        self.stock_request = self.env['stock.request'].create({
            'picking_policy': 'direct',
            'product_id': self.product_id.id,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 1.0,
            'warehouse_id': self.warehouse.id,
            'expected_date': datetime.today(),
            'direction': 'outbound',
            'location_id': self.test_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id
        })

    def test_fsm_location(self):
        vals = {
            'fsm_order_id': self.order.id,
            'picking_policy': 'direct',
            'product_id': self.product_id.id,
            'product_uom_id': self.env.ref('uom.product_uom_unit').id,
            'product_uom_qty': 1.0,
            'warehouse_id': self.warehouse.id,
            'expected_date': datetime.today(),
            'direction': 'outbound',
            'location_id': self.test_location.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id
        }
        self.order.write({
            'stock_request_ids': [(6, 0, self.env['stock.request'].
                                   create(vals).ids)]
        })
        # Check the Location on the SR is equal to the Location on the Order
        self.assertEqual(self.order.stock_request_ids[0].fsm_location_id,
                         self.order.location_id)
        # Check the Location on the SRO is equal to the Location on the Order
        self.assertEqual(self.order.stock_request_ids[0].
                         order_id.fsm_location_id, self.order.location_id)
