import datetime
from odoo.addons.sale_subscription.tests.common_sale_subscription \
    import TestSubscriptionCommon


class TestInvoice(TestSubscriptionCommon):

    def setUp(self, *args, **kwargs):
        super(TestInvoice, self).setUp(*args, **args)

        import pudb; pu.db
        Product = self.env['product.product']
        self.prod_toilet_paper = Product.create({'name': 'Toilet Paper'})
        self.prod_hand_soap = Product.create({'name': 'Hand Soap'})

        AnalyticLine = self.env['account.analytic.line']
        today = datetime.date.today()
        days = datetime.timedelta(days=1)

        # Line 0 is before billing period
        self.line_0 = AnalyticLine.create({
            'name': 'Line 0',
            'date': today - days * 1,
            'account_id': self.account_1,
            'product_id': self.prod_toilet_paper,
            'amount': 25.0,
        })
        self.line_1 = AnalyticLine.create({
            'name': 'Line 1',
            'date': today,
            'account_id': self.account_1,
            'product_id': self.prod_toilet_paper,
            'amount': 30.0,
        })
        self.line_2 = AnalyticLine.create({
            'name': 'Line 2',
            'date': today + days * 2,
            'account_id': self.account_1,
            'product_id': self.prod_hand_soap,
            'amount': 40.0,
        })
        self.line_3 = AnalyticLine.create({
            'name': 'Line 3',
            'date': today + days * 3,
            'account_id': self.account_1,
            'product_id': self.prod_hand_soap,
            'amount': 50.0,
        })
        # Line 4 is after billing period
        self.line_4 = AnalyticLine.create({
            'name': 'Line 4',
            'date': today + days * 400,
            'account_id': self.account_1,
            'product_id': self.prod_hand_soap,
            'amount': 60.0,
        })

    def test_variable(self):
        # On Sale Order, set the Analytic Account and Confirm
        self.sale_order.analytic_account_id = self.account_1
        self.sale_order.action_confirm()

        subscription = self.sale_order_line[0].subscription_id
        subscription.recurring_invoice()

        InvLines = self.env['accoutn.invoice.line']
        inv_lines = InvLines.search(
            [('product_id', '=', self.prod_toilet_paper)])
        self.AssertEqual(
            sum(x.price_subtotal for x in inv_lines),
            30.0,
            'Invoice Line 1, inside billing period')

        inv_lines = InvLines.search(
            [('product_id', '=', self.prod_hand_soap)])
        self.AssertEqual(
            sum(x.price_subtotal for x in inv_lines),
            90.0,
            'Invoice Line 2 and 3, inside billing period')
        self.AssertEqual(
            len(inv_lines),
            1,
            'Same product lines (2 and 3) should be in a single invoice line')
