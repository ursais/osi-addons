# Import Python libs
import logging
from unittest.mock import patch
from datetime import timedelta

# Import Odoo libs
from odoo.addons.ls_sale_workflow.tests.common import BaseSaleWorkflowTest

_logger = logging.getLogger(__name__)

_logger = logging.getLogger(__name__)
ONE_DAY = timedelta(1)
DATE_FORMAT = '%Y-%m-%d'


class TestSaleBooking(BaseSaleWorkflowTest):
    """ Test end date computation """

    @patch('odoo.addons.ls_sale_workflow.models.sale.SaleOrder.validate_for_confirm')
    @patch('odoo.addons.ls_sale_workflow.models.sale.SaleOrder.validate_quote')
    def test_sale_booking(self, validate_for_confirm, validate_quote):
        # Draft -> Customer Review (via pdf download)
        self.sale_order.action_quotation_pdf()
        # Customer Review -> Pending Confirm
        self.sale_order.action_validate()
        self.assertTrue(self.sale_order.booking_ids, 'No Sale Bookings were created')
        self.assertTrue(len(self.sale_order.booking_ids) == 1, 'No Sale Bookings were created')

        booking = self.sale_order.booking_ids
        self.assertEqual(
            booking.order_detailed_state,
            self.sale_order.detailed_state,
            'Sale Bookings has the wrong detailed state',
        )
