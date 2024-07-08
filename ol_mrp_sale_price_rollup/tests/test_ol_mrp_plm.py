# Copyright 2020 Sergio Teruel <sergio.teruel@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.tests import common, tagged,Form
from odoo.addons.base.tests.common import DISABLED_MAIL_CONTEXT
from odoo.tools import float_compare, float_round, float_repr


@tagged("-at_install", "post_install")
class TestSaleTierValidation(common.TransactionCase):

    @classmethod
    def _create_product(cls, name, price,lst_price):
        return cls.Product.create({
            'name': name,
            'type': 'product',
            'standard_price': price,
            'lst_price':lst_price
        })

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.groups_id += cls.env.ref('uom.group_uom')
        cls.env.user.groups_id += cls.env.ref('mrp.group_mrp_byproducts')  # Enables by-products.

        # Required for `product_id ` to be visible in the view
        cls.env.user.groups_id += cls.env.ref('product.group_product_variant')
        cls.Product = cls.env['product.product']
        cls.Bom = cls.env['mrp.bom']


        # Products.
        cls.dining_table = cls._create_product('Dining Table', 1000,0.0)
        cls.table_head = cls._create_product('Table Head', 300,800)
        cls.screw = cls._create_product('Screw', 10,60)
        cls.leg = cls._create_product('Leg', 25,125)
        cls.glass = cls._create_product('Glass', 100,600)

        # Unit of Measure.
        cls.unit = cls.env.ref("uom.product_uom_unit")
        cls.dozen = cls.env.ref("uom.product_uom_dozen")


        bom_form = Form(cls.Bom)
        # bom_form.product_id = cls.dining_table
        bom_form.product_tmpl_id = cls.dining_table.product_tmpl_id
        bom_form.product_qty = 1.0
        bom_form.product_uom_id = cls.unit
        bom_form.type = 'normal'
        with bom_form.bom_line_ids.new() as line:
            line.product_id = cls.table_head
            line.product_qty = 1
        with bom_form.bom_line_ids.new() as line:
            line.product_id = cls.screw
            line.product_qty = 5
        with bom_form.bom_line_ids.new() as line:
            line.product_id = cls.leg
            line.product_qty = 4
        with bom_form.bom_line_ids.new() as line:
            line.product_id = cls.glass
            line.product_qty = 1
        cls.bom_1 = bom_form.save()

        # cls.dining_table.button_bom_sale_price()

class TestBomPrice(TestSaleTierValidation):
    def test_00_compute_price(self):
        """Test multi-level BoM cost"""
        self.assertEqual(self.dining_table.standard_price, 1000, "Initial price of the Product should be 1000")
        self.dining_table.button_bom_sale_price()
        self.dining_table.button_bom_cost()
        self.assertEqual(self.dining_table.standard_price, 550, "After computing price from BoM price should be 550")

    def test_01_bom_report(self):
        """ Simulate a crumble receipt with mrp and open the bom structure
        report and check that data insde are correct.
        """
        uom_kg = self.env.ref('uom.product_uom_kgm')
        uom_unit = self.env.ref('uom.product_uom_unit')
        uom_litre = self.env.ref('uom.product_uom_litre')
        crumble = self.env['product.product'].create({
            'name': 'Crumble',
            'type': 'product',
            'uom_id': uom_kg.id,
            'uom_po_id': uom_kg.id,
        })
        butter = self.env['product.product'].create({
            'name': 'Butter',
            'type': 'product',
            'uom_id': uom_kg.id,
            'uom_po_id': uom_kg.id,
            'standard_price': 7.01
        })
        biscuit = self.env['product.product'].create({
            'name': 'Biscuit',
            'type': 'product',
            'uom_id': uom_kg.id,
            'uom_po_id': uom_kg.id,
            'standard_price': 1.5
        })
        bom_form_crumble = Form(self.env['mrp.bom'])
        bom_form_crumble.product_tmpl_id = crumble.product_tmpl_id
        bom_form_crumble.product_qty = 11
        bom_form_crumble.product_uom_id = uom_kg
        bom_crumble = bom_form_crumble.save()

        workcenter = self.env['mrp.workcenter'].create({
            'costs_hour': 10,
            'name': 'Deserts Table'
        })

        # Required to display `operation_ids` in the form view
        self.env.user.groups_id += self.env.ref("mrp.group_mrp_routings")
        with Form(bom_crumble) as bom:
            with bom.bom_line_ids.new() as line:
                line.product_id = butter
                line.product_uom_id = uom_kg
                line.product_qty = 5
            with bom.bom_line_ids.new() as line:
                line.product_id = biscuit
                line.product_uom_id = uom_kg
                line.product_qty = 6
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Prepare biscuits'
                operation.time_cycle_manual = 5
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Prepare butter'
                operation.time_cycle_manual = 3
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Mix manually'
                operation.time_cycle_manual = 5

        # TEST BOM STRUCTURE VALUE WITH BOM QUANTITY
        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=11, searchVariant=False)
        # 5 min 'Prepare biscuits' + 3 min 'Prepare butter' + 5 min 'Mix manually' = 13 minutes for 1 biscuits so 13 * 11 = 143 minutes
        self.assertEqual(report_values['lines']['operations_time'], 143.0, 'Operation time should be the same for 1 unit or for the batch')
        # Operation cost is the sum of operation line.
        self.assertEqual(float_compare(report_values['lines']['operations_cost'], 23.84, precision_digits=2), 0, '143 minute for 10$/hours -> 23.84')

        for component_line in report_values['lines']['components']:
            # standard price * bom line quantity * current quantity / bom finished product quantity
            if component_line['product'].id == butter.id:
                # 5 kg of butter at 7.01$ for 11kg of crumble -> 35.05$
                self.assertEqual(float_compare(component_line['bom_cost'], (7.01 * 5), precision_digits=2), 0)
            if component_line['product'].id == biscuit.id:
                # 6 kg of biscuits at 1.50$ for 11kg of crumble -> 9$
                self.assertEqual(float_compare(component_line['bom_cost'], (1.5 * 6), precision_digits=2), 0)
        # total price = 35.05 + 9 + operation_cost(23.84) = 67.89
        self.assertEqual(float_compare(report_values['lines']['bom_cost'], 67.89, precision_digits=2), 0, 'Product Bom Price is not correct')
        self.assertEqual(float_compare(report_values['lines']['bom_cost'] / 11.0, 6.17, precision_digits=2), 0, 'Product Unit Bom Price is not correct')

        # TEST BOM STRUCTURE VALUE BY UNIT
        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=1, searchVariant=False)
        # 5 min 'Prepare biscuits' + 3 min 'Prepare butter' + 5 min 'Mix manually' = 13 minutes
        self.assertEqual(report_values['lines']['operations_time'], 13.0, 'Operation time should be the same for 1 unit or for the batch')
        # Operation cost is the sum of operation line.
        operation_cost = float_round(5 / 60 * 10, precision_digits=2) * 2 + float_round(3 / 60 * 10, precision_digits=2)
        self.assertEqual(float_compare(report_values['lines']['operations_cost'], operation_cost, precision_digits=2), 0, '13 minute for 10$/hours -> 2.16')

        for component_line in report_values['lines']['components']:
            # standard price * bom line quantity * current quantity / bom finished product quantity
            if component_line['product'].id == butter.id:
                # 5 kg of butter at 7.01$ for 11kg of crumble -> / 11 for price per unit (3.19)
                self.assertEqual(float_compare(component_line['bom_cost'], (7.01 * 5) * (1 / 11), precision_digits=2), 0)
            if component_line['product'].id == biscuit.id:
                # 6 kg of biscuits at 1.50$ for 11kg of crumble -> / 11 for price per unit (0.82)
                self.assertEqual(float_compare(component_line['bom_cost'], (1.5 * 6) * (1 / 11), precision_digits=2), 0)
        # total price = 3.19 + 0.82 + operation_cost(0.83 + 0.83 + 0.5 = 2.16) = 6,17
        self.assertEqual(float_compare(report_values['lines']['bom_cost'], 6.17, precision_digits=2), 0, 'Product Unit Bom Price is not correct')

        # TEST OPERATION COST WHEN PRODUCED QTY > BOM QUANTITY
        report_values_12 = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=12, searchVariant=False)
        report_values_22 = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=22, searchVariant=False)

        #Operation cost = 47.66 € = 256 (min) * 10€/h
        self.assertEqual(float_compare(report_values_22['lines']['operations_cost'], 47.66, precision_digits=2), 0, 'Operation cost is not correct')

        # Create a more complex BoM with a sub product
        cheese_cake = self.env['product.product'].create({
            'name': 'Cheese Cake 300g',
            'type': 'product',
        })
        cream = self.env['product.product'].create({
            'name': 'cream',
            'type': 'product',
            'uom_id': uom_litre.id,
            'uom_po_id': uom_litre.id,
            'standard_price': 5.17,
        })
        bom_form_cheese_cake = Form(self.env['mrp.bom'])
        bom_form_cheese_cake.product_tmpl_id = cheese_cake.product_tmpl_id
        bom_form_cheese_cake.product_qty = 60
        bom_form_cheese_cake.product_uom_id = uom_unit
        bom_cheese_cake = bom_form_cheese_cake.save()

        workcenter_2 = self.env['mrp.workcenter'].create({
            'name': 'cake mounting',
            'costs_hour': 20,
            'time_start': 10,
            'time_stop': 15
        })

        self.env['mrp.workcenter.capacity'].create({
            'product_id': cheese_cake.id,
            'workcenter_id': workcenter_2.id,
            'time_start': 12,
            'time_stop': 16,
        })

        with Form(bom_cheese_cake) as bom:
            with bom.bom_line_ids.new() as line:
                line.product_id = cream
                line.product_uom_id = uom_litre
                line.product_qty = 3
            with bom.bom_line_ids.new() as line:
                line.product_id = crumble
                line.product_uom_id = uom_kg
                line.product_qty = 5.4
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter
                operation.name = 'Mix cheese and crumble'
                operation.time_cycle_manual = 10
            with bom.operation_ids.new() as operation:
                operation.workcenter_id = workcenter_2
                operation.name = 'Cake mounting'
                operation.time_cycle_manual = 5

        # TEST CHEESE BOM STRUCTURE VALUE WITH BOM QUANTITY
        report_values = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_cheese_cake.id, searchQty=60, searchVariant=False)
        # Operation time = 15 min * 60 + capacity_time_start + capacity_time_stop = 928
        self.assertEqual(report_values['lines']['operations_time'], 928.0, 'Operation time should be the same for 1 unit or for the batch')
        # Operation cost is the sum of operation line : (60 * 10)/60 * 10€ + (10 + 15 + 60 * 5)/60 * 20€ + (1 + 2)/60 * 20€ = 209,33€
        self.assertEqual(float_compare(report_values['lines']['operations_cost'], 209.33, precision_digits=2), 0)

        for component_line in report_values['lines']['components']:
            # standard price * bom line quantity * current quantity / bom finished product quantity
            if component_line['product'].id == cream.id:
                # 3 liter of cream at 5.17$ for 60 unit of cheese cake -> 15.51$
                self.assertEqual(float_compare(component_line['bom_cost'], (3 * 5.17), precision_digits=2), 0)
            if component_line['product'].id == crumble.id:
                # 5.4 kg of crumble at the cost of a batch.
                crumble_cost = self.env['report.mrp.report_bom_structure']._get_report_data(bom_id=bom_crumble.id, searchQty=5.4, searchVariant=False)['lines']['bom_cost']
                self.assertEqual(float_compare(component_line['bom_cost'], crumble_cost, precision_digits=2), 0)
        # total price = Cream (15.51€) + crumble_cost (34.63 €) + operation_cost(209,33) = 259.47€
        self.assertEqual(float_compare(report_values['lines']['bom_cost'], 259.47, precision_digits=2), 0, 'Product Bom Price is not correct')



