# Import Python libs
import os
import logging
import uuid as uuid_lib
from unittest import mock
from unittest.mock import patch
from datetime import datetime

# Import Odoo libs
from odoo.tests.common import Form
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.ol_base.tests.common import OnLogicBaseTransactionCase
from odoo.addons.ol_webhooks.models.stock_quant import StockQuant

_logger = logging.getLogger(__name__)


class TestWebhook(OnLogicBaseTransactionCase):
    def setUp(self):
        """Setup for test cases"""

        try:
            # Remove Environment variables
            del os.environ["TEST_QUEUE_JOB_NO_DELAY"]
            del os.environ["ODOO_ONLOGIC_WEBHOOKS_DISABLED"]
        except:
            pass

        _logger.info("Setting Up")

        super(TestWebhook, self).setUp()

        self.timestamp = datetime.timestamp(datetime.now())

        self.api_client = self.env.ref("ol_api.webhook_client_onlogic")
        self.api_client.write({"webhook_url_hostname": "test_url"})

        self.sale_create_event = self.env.ref("ol_webhooks.sale_order_create")
        self.sale_update_event = self.env.ref("ol_webhooks.sale_order_update")
        self.sale_unlink_event = self.env.ref("ol_webhooks.sale_order_delete")
        self.sale_order_webhook = self.env.ref("ol_webhooks.sale_order_webhook")
        self.sale_order = self.env["sale.order"]

        self.product_stock_event = self.env.ref(
            "ol_webhooks.product_template_stock_quantity_changed"
        )
        self.product_system_stock_event = self.env.ref(
            "ol_webhooks.system_stock_quantity_changed"
        )
        self.product_cost_event = self.env.ref(
            "ol_webhooks.product_template_cost_changed"
        )
        self.product_stock_webhook = self.env.ref(
            "ol_webhooks.product_template_stock_webhook"
        )
        self.product_system_stock_webhook = self.env.ref(
            "ol_webhooks.system_stock_quantity_webhook"
        )
        self.product_cost_webhook = self.env.ref(
            "ol_webhooks.product_template_cost_webhook"
        )
        # Setup dummy objects
        self.product_template = self.env["product.template"].create(
            {"name": "test product"}
        )
        self.product = self.env.ref("ol_base.ts32gmts800")
        self.location_customer = self.browse_ref("stock.stock_location_customers")
        warehouse = self.env["stock.warehouse"]
        self.us_warehouse = warehouse.search([("company_id", "=", self.us_company.id)])
        self.location_us_warehouse = self.us_warehouse.lot_stock_id
        self.stock_quant = self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location_us_warehouse.id,
            }
        )

    def tearDown(self):
        """
        We need to have working QUEUE_JOBS for Webhook tests
        """
        super(TestWebhook, self).tearDown()
        # Set Environment variables
        os.environ["TEST_QUEUE_JOB_NO_DELAY"] = "1"
        os.environ["ODOO_ONLOGIC_WEBHOOKS_DISABLED"] = "1"

    def get_mocking_webhook_data(self, webhook, event, records):
        # Populate data with values for webhook, but ignore the event and timestamp in comparison
        data = webhook.get_webhook_data(
            event=event,
            operation=False,
            timestamp=self.timestamp,
            records=records,
            transaction_id=mock.ANY,
            broadcast_options={},
        )
        data.update(
            {
                "timestamp": mock.ANY,
                "event": "update",
            }
        )
        return data

    @mock.patch("requests.post")
    def test_generic_actions_webhook(self, mock_post):
        # Test create webhook
        self.sale_order = (
            self.env["sale.order"]
            .with_context(webhook_no_delay=True)
            .create(
                {
                    "partner_id": self.env.ref("ol_base.customer_us").id,
                }
            )
        )
        data = self.get_mocking_webhook_data(
            self.sale_order_webhook, self.sale_create_event, self.sale_order
        )

        mock_post.assert_called_with(
            headers=mock.ANY,
            json=data,
            timeout=mock.ANY,
            url=self.sale_order_webhook.url,
        )

        # Test update webhook
        self.sale_order.with_context(webhook_no_delay=True).write({"name": "test"})
        data = self.get_mocking_webhook_data(
            self.sale_order_webhook, self.sale_update_event, self.sale_order
        )
        mock_post.assert_called_with(
            headers=mock.ANY,
            json=data,
            timeout=mock.ANY,
            url=self.sale_order_webhook.url,
        )

        # TODO: hunt down bug that is causing errors when unlinking
        # Test delete webhook
        # self.sale_order.with_context(webhook_no_delay=True).unlink()

        # Test webhook with bad data to ensure the assertions work properly
        self.sale_order.with_context(webhook_no_delay=True).write({"name": "bad data"})
        # Purposely set bad data to compare the correct webhook post with
        data = self.get_mocking_webhook_data(
            self.product_cost_webhook, self.sale_create_event, self.product
        )
        with self.assertRaises(AssertionError):
            mock_post.assert_called_with(
                headers=mock.ANY,
                json=data,
                timeout=mock.ANY,
                url=self.sale_order_webhook.url,
            ), "Failed Assertion Error. mock_post.assert_called_with failed"

    @mock.patch("requests.post")
    def test_purchase_cost(self, mock_post):
        # Test product cost changed webhook
        #   field: purchase_cost
        self.product_template.with_context(webhook_no_delay=True).write(
            {"purchase_cost": 100.0}
        )
        data = self.get_mocking_webhook_data(
            self.product_cost_webhook, self.product_cost_event, self.product_template
        )
        mock_post.assert_called_with(
            headers=mock.ANY,
            json=data,
            timeout=mock.ANY,
            url=self.product_cost_webhook.url,
        )

    @mock.patch("requests.post")
    def test_product_stock(self, mock_post):
        # Test component stock webhook

        self.stock_quant.with_context(
            webhook_no_delay=True, test_queue_job_no_delay=True
        ).write({"quantity": 100})
        data = self.get_mocking_webhook_data(
            self.product_stock_webhook,
            self.product_stock_event,
            self.stock_quant.product_id,
        )
        mock_post.assert_called_with(
            headers=mock.ANY,
            json=data,
            timeout=mock.ANY,
            url=self.product_stock_webhook.url,
        )

        # The above actions also should add System Stock State Queue items
        # that will be used to trigger System Stock webhooks via the related cron
        system_stock_queue_item = self.env["product.stock.queue"].search([])

        self.assertEqual(
            len(system_stock_queue_item),
            1,
            "Wrong number of System Stock State Queue items were created",
        )

        self.assertEqual(
            system_stock_queue_item.product_id,
            self.stock_quant.product_id,
            "System Stock State Queue item has the wrong product",
        )

        if self.stock_quant.company_id:
            self.assertEqual(
                system_stock_queue_item.company_id,
                self.stock_quant.company_id,
                "System Stock State Queue item has the wrong company",
            )

        systems = self.stock_quant.product_id.get_systems_containing_these_components()

        self.assertFalse(
            systems.system_stock_state,
            "System Stock State field value should not be set yet",
        )

        data = self.get_mocking_webhook_data(
            self.product_system_stock_webhook, self.product_system_stock_event, systems
        )
        # Mimic the `System Stock State Re-calculation` cron triggering
        self.env["product.stock.queue"].with_context(
            webhook_no_delay=True, test_queue_job_no_delay=True
        ).run()
        self.assertTrue(
            systems.system_stock_state,
            "System Stock State field value should be set!",
        )
        mock_post.assert_called_with(
            headers=mock.ANY,
            json=data,
            timeout=mock.ANY,
            url=self.product_system_stock_webhook.url,
        )

    def test_broadcast_error_handling(self):
        # Test Error Handling
        self.api_client.write({"webhook_url_hostname": False})
        with Form(self.sale_order_webhook) as form:
            form.client_id = self.api_client
        transaction_id = str(uuid_lib.uuid4())
        with self.assertRaises((ValidationError, RetryableJobError)):
            self.sale_order_webhook.broadcast(
                event=self.sale_update_event,
                records=self.sale_order,
                timestamp=self.timestamp,
                operation=self.sale_update_event.operation,
                transaction_id=transaction_id,
                options={},
            ),

        self.api_client.write({"webhook_secret": False})
        with Form(self.sale_order_webhook) as form:
            form.client_id = self.api_client
        with self.assertRaises((ValidationError, RetryableJobError)):
            self.sale_order_webhook.broadcast(
                event=self.sale_update_event,
                records=self.sale_order,
                timestamp=self.timestamp,
                operation=self.sale_update_event.operation,
                transaction_id=transaction_id,
                options={},
            )
