# Import Python libs
import os
import time
import logging
import requests
import uuid as uuid_lib
from datetime import datetime, timedelta

# Import Odoo libs
from odoo.tools import config
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.ol_base.models.tools import chunk_recordset

_logger = logging.getLogger(__name__)

OPERATION_PRIORITIES = ["create", "delete", "update", "custom"]
CLASS_PRIORITIES = ["res.partner", "sale.order"]


class Webhook(models.Model):
    """
    Basic Webhook
    """

    _name = "webhook"
    _description = "Webhook"

    _sql_constraints = [
        (
            "webhook_client_path_uniq",
            "UNIQUE(client_id, url_path, enabled)",
            "Must be unique by URL",
        )
    ]

    # COLUMNS #######
    client_id = fields.Many2one(
        string="API Client", comodel_name="api.client", required=True
    )
    url_hostname = fields.Char(
        string="Client Hostname",
        help=(
            "The base URL that will used to for the final webhook URL. Ex.:"
            " https://onlogic.com/odoo-webhooks/"
        ),
        related="client_id.webhook_url",
        readonly=True,
    )
    url_path = fields.Char(
        string="Url Path",
        help="The specific path for the given webhook",
        required=True,
        copy=False,
    )
    url = fields.Char(
        string="Url",
        help="The URL that will be called when any of the related events happen.",
        compute="_compute_url",
    )
    secret = fields.Char(
        string="Client Secret",
        help=(
            "The Secret is used to validate the Webhook call for any service/app that listens for the"
            " requests."
        ),
        related="client_id.webhook_secret",
        readonly=True,
    )
    enabled = fields.Boolean(string="Enabled", default=True)
    event_ids = fields.Many2many(
        string="Events",
        comodel_name="webhook.event",
        relation="webhook_webhook_events",
        column1="webhook_id",
        column2="webhook_event_id",
        required=True,
    )
    timeout = fields.Integer(
        string="Webhook Timeout",
        help="Maximum time we want to want to wait for a webhook call to be considered successful.",
        default=5,
    )
    delay_time = fields.Integer(
        string="Webhook Delay Time",
        help=(
            "Number of seconds to wait to group webhook calls. Webhooks fired during this time period for the"
            " same record and operation won't be all sent, instead only one will be sent. Last or first one"
            " based on the `ol_queue_job.reverse_identity_key` setting."
        ),
        default=5,
    )
    chunk_size = fields.Integer(
        string="Record Chunk Size",
        help="Recordsets will be split into chunks of this number. Each chunk is sent in one webhook call.",
        default=50,
    )
    # END COLUMNS ###

    @api.depends("client_id", "client_id.webhook_url", "url_hostname", "url_path")
    def _compute_url(self):
        """
        Compute the final URL based on the hostname and path
        """
        for webhook in self:
            if not webhook.url_hostname or not webhook.url_path:
                webhook.url = False
            else:
                webhook.url = f"{webhook.url_hostname}/{webhook.url_path}"

    def _compute_display_name(self):
        """
        Use `URL` as the name of the record
        """
        for record in self:
            record.display_name = f"{record.client_id.name} - {record.url_path}"

    def broadcast_all(self, event, records, operation_override=False):
        """
        Wrapper method around `broadcast`.
        This allows for a more convenient way to call the `broadcast` function with different helper functions.
        """

        if (
            os.getenv("ODOO_ONLOGIC_WEBHOOKS_DISABLED")
            or config.get("odoo_upgrade_instance", False)
            or not self.env["ir.config_parameter"]
            .sudo()
            .get_as_boolean("ol_webhooks.webhooks_enabled")
        ):
            # We don't want to trigger Webhooks During unit tests
            return True
        timestamp = datetime.timestamp(datetime.now())
        transaction_id = self.get_transaction_id()
        fields_to_sync = self.env.context.get("fields_to_sync", False)
        for webhook in self:
            operation = operation_override or event.operation
            # Run webhooks in chunks,
            # maximizing the amount of records in one webhook call
            chunked = self.get_record_chunks(records)
            wait_time = self.get_wait_time(operation)
            for webhook_records in chunked:
                if self.run_without_queue_job():
                    webhook.broadcast(
                        event=event,
                        records=webhook_records,
                        timestamp=timestamp,
                        operation=operation,
                        transaction_id=transaction_id,
                        options=self.get_broadcast_options(
                            defaults={"run_without_queue_job": True}
                        ),
                        fields_to_sync=fields_to_sync,
                    )
                else:
                    operation_priority = self.get_priority(records, operation)
                    channel = self.get_channel()
                    # By setting the `identity_key` and `eta` together we are getting
                    # a very simple but effective rate limit to webhooks.
                    # This ensures that the same record for the same operation is only broadcasted every X seconds defined by the `wait_time`.
                    # Setting priority based on the operation type allows us to make sure we broadcast events in a logical order.
                    # Ex. `Update`` won't be broadcasted before `Create`

                    identity_key = (
                        webhook.get_identity_key(event, webhook_records, operation)
                        if self.client_id.run_webhooks_delayed
                        else None
                    )
                    webhook.with_context(transaction_id=transaction_id).with_delay(
                        priority=operation_priority,
                        eta=wait_time,
                        identity_key=identity_key,
                        channel=channel,
                    ).broadcast(
                        event=event,
                        records=webhook_records,
                        timestamp=timestamp,
                        operation=operation,
                        transaction_id=transaction_id,
                        options=self.get_broadcast_options(),
                        fields_to_sync=fields_to_sync,
                    )

    def run_without_queue_job(self):
        """
        If certain context variables are set we want to run the webhook requests directly
        """
        if self.env.context.get("webhook_no_delay", False):
            return True
        return False

    def get_record_chunks(self, records):
        """
        Create n-sized chunks from the recordset
        """

        # Allow to control the webhook chunk size via context variables
        chunk_size = self.env.context.get("webhook_chunk_size", self.chunk_size)
        return chunk_recordset(records, chunk_size)

    def get_broadcast_options(self, defaults=False):
        # This function is intended to be overridden in later modules
        return defaults or {}

    def broadcast(
        self,
        event,
        records,
        timestamp,
        operation,
        transaction_id,
        options,
        fields_to_sync=False,
    ):
        """
        Call the given URL to trigger the WebHook.

        Example request (using `odoo-webhook-secret` as secret):
        """

        self._pre_broadcast_actions(
            event=event,
            records=records,
            timestamp=timestamp,
            operation=operation,
            transaction_id=transaction_id,
            broadcast_options=options,
            fields_to_sync=fields_to_sync,
        )

        if not self.url:
            msg = (
                "WEBHOOK Error: No URL set."
                f"Client: `{self.client_id.name}` "
                f"Hostname: `{self.url_hostname}` "
                f"Path: `{self.url_path}`"
            )
            _logger.warning(msg)
            raise ValidationError(msg)

        if not self.secret:
            msg = f"WEBHOOK Error: No Secret set. Client: `{self.client_id.name}` "
            _logger.warning(msg)
            raise ValidationError(msg)

        # Set the retry delay in seconds
        retry_delay = 180
        data = self.get_webhook_data(
            event=event,
            operation=operation,
            timestamp=timestamp,
            records=records,
            transaction_id=transaction_id,
            broadcast_options=options,
            fields_to_sync=fields_to_sync,
        )
        headers = self.get_webhook_header(data)
        timeout = self.get_timeout(records)
        log_data = (
            f"URL: {self.url} | Client: {self.client_id.name} | Event: {event.display_name} | Operation:"
            f" {operation} | Timeout: {timeout}s | TI: `{transaction_id}` | Records:"
            f" {records.mapped('uuid') if len(records) <= 50 else len(records)}"
        )

        try:
            start_time = datetime.now()
            # We set `timeout` as we don't want to wait too long
            response = self.trigger_webhook_request(
                url=self.url, headers=headers, data=data, timeout=timeout
            )
            log_data = (
                f"{log_data} | Response: [{response.status_code}]"
                f" {response.reason} {'' if response.ok else response.text}"
            )
            if response.ok:
                log_data = f"{log_data} Done in: {datetime.now() - start_time}s"
                _logger.info(f"WEBHOOK Succeeded: {log_data}")
                self._post_webhook_broadcast_success_actions(
                    event=event,
                    operation=operation,
                    webhook_data=data,
                    records=records,
                    broadcast_options=options,
                )
            else:
                msg = f"WEBHOOK Error: Invalid webhook response | {log_data}"
                # If we are running this method via a `queue.job`
                # we are using `RetryableJobError` that allows us to retry later
                # or `ValidationError` to cause the code to hard fail
                if options.get("run_without_queue_job", False):
                    raise ValidationError(msg)
                raise RetryableJobError(msg, seconds=retry_delay)
        except requests.exceptions.ReadTimeout as timeout_error:
            msg = f"WEBHOOK Timeout: {log_data} | Timeout: {timeout} | Exception: {timeout_error}"
            _logger.exception(msg)
            # If we are running this method via a `queue.job`
            # we are using `RetryableJobError` that allows us to retry later.
            # If we are running without a queue job we don't want to throw exceptions
            # as a result of Webhook problems, as that could block internal Odoo workflows
            if not options.get("run_without_queue_job", False):
                raise RetryableJobError(msg, seconds=retry_delay) from timeout_error
        except Exception as exception:
            msg = f"WEBHOOK Failed: {log_data} | Exception: {exception}"
            _logger.exception(msg)

            # If we are running this method via a `queue.job`
            # we are using `RetryableJobError` that allows us to retry later.
            # If we are running without a queue job we don't want to throw exceptions
            # as a result of Webhook problems, as that could block internal Odoo workflows
            if not options.get("run_without_queue_job", False):
                raise RetryableJobError(msg, seconds=retry_delay) from exception

    def _post_webhook_broadcast_success_actions(
        self, event, operation, webhook_data, records, broadcast_options
    ):
        """
        This function is intended to be overridden in later modules
        """
        self.env["webhook.broadcast.date"].record(
            webhook_event=event, operation=operation, records=records
        )

    def _pre_broadcast_actions(
        self,
        event,
        records,
        timestamp,
        operation,
        transaction_id,
        broadcast_options,
        fields_to_sync=False,
    ):
        """
        This function is intended to be overridden in later modules

        Allow to run other functionality that should be triggered
        before webhook broadcast is started
        """
        return True

    def trigger_webhook_request(self, url, headers, data, timeout):
        """
        Trigger the webhook
        """
        return requests.post(url=url, headers=headers, json=data, timeout=timeout)

    def get_transaction_id(self):
        """
        Get the transaction ID from the context or generate a new one
        We use `hex` to get the string value instead of passing the whole UUID object
        """
        return self.env.context.get("transaction_id", str(uuid_lib.uuid4()))

    def get_timeout(self, records):
        """
        Calculate the dynamic timeout based on the length of the records
        """
        # We assume the default timeout is enough for 2 records
        multiplier = len(records) / 2
        # Maximize the timeout in 10 minutes
        return min([600, max(multiplier * self.timeout, 5)])

    def get_webhook_data(
        self,
        event,
        operation,
        timestamp,
        records,
        transaction_id,
        broadcast_options,
        fields_to_sync=False,
    ):
        data = {
            "client": self.client_id.name,
            "model": event.model_name,
            # We allow `custom` events to broadcast any operation. ex. `custom` -> `update`
            "event": operation,
            "timestamp": timestamp,
            "fields": fields_to_sync or None,
            "transaction_id": transaction_id,
        }
        # Set the UUID
        if not records._fields.get("uuid", False):
            raise ValidationError(f"UUID not implemented for `{records._name}`")
        data.update({"records": [{"id": r.id, "uuid": r.uuid} for r in records]})
        return data

    def get_webhook_header(self, data):
        return {
            # TODO: Do we need any versioning?
            "X-Odoo-Webhook-Version": "0.01",
            "X-Odoo-Webhook-Signature": (
                f"{self.env['api'].generate_hmac_signature(key=self.secret, msg=data)}"
            ),
        }

    def get_identity_key(self, event, records, operation):
        """
        Create the queue identify key by hashing the key values of the webhook
        """

        if operation == "create":
            # We don't need identity key for create
            return None

        data = {
            "webhook_id": self.id,
            "model_name": event.model_name,
            "operation": operation,
            "record_ids": sorted(records.ids),
        }
        return self.env["api"].generate_hmac_signature(key=operation, msg=data)

    def get_wait_time(self, operation):
        """
        Get the webhook delay time
        """

        if operation == "create":
            # We don't want to delay/group create webhooks as we should always have only one for one record
            return None

        # Return the saved config value
        # or allow us to override the default webhook wait time via context
        return self.env.context.get("webhook_wait_time", self.delay_time)

    def get_priority(self, records, operation):
        """
        Priority of the job, 0 being the higher priority.
        Examples, with `class_priorities = ['res.partner', 'sale.order', 'helpdesk.rma']`:

            class_priority = class_priority * len(OPERATION_PRIORITIES)
            result = operation_priority + class_priority

            res.partner - create
                operation_priority = 0 (0 * 10)
                class_priority = 0 (0 * 4)
                result = 0 (0 + 0)
            res.partner - update
                operation_priority = 1 (1* 10)
                class_priority =0 (0 * 4)
                result = 1 (1 + 0)

            sale.order - create
                operation_priority = 0 (0 * 10)
                class_priority = 4 (1 * 4)
                result = 4 (0 + 4)
            sale.order - update
                operation_priority = 1 (1* 10)
                class_priority = 4 (1 * 4)
                result = 5 (1 + 4)

            helpdesk.rma - create
                operation_priority = 0 (0 * 10)
                class_priority = 8 (2 * 4)
                result = 8 (0 + 8)
            helpdesk.rma - update (1* 10)
                operation_priority = 1
                class_priority = 8 (2 * 4)
                result = 9 (1 + 8)

            account.move - create
                operation_priority = 0 (0 * 10)
                class_priority = 16 (4 * 4)
                result = 16 (0 + 16 )
            account.move - update (1* 10)
                operation_priority = 1
                class_priority = 16 (4 * 4)
                result = 17 (1 + 16)
        """

        # Get the operation priority or default to the len of the OPERATION_PRIORITIES
        # which is always going to be higher than the highest possible index in OPERATION_PRIORITIES
        # this ensures that if we receive an operation that has no defined operation priority,
        # that will be lower priority than ones that are defined in OPERATION_PRIORITIES
        operation_priority = (
            OPERATION_PRIORITIES.index(operation)
            if operation in OPERATION_PRIORITIES
            else len(OPERATION_PRIORITIES)
        )

        # Get the class priority or default to the len of the CLASS_PRIORITIES
        # which is always going to be higher than the highest possible index in CLASS_PRIORITIES
        # this ensures that if we receive class that has no defined class priority,
        # that will be lower priority than ones that are defined in CLASS_PRIORITIES
        # IMPORTANT:    Notice that `* len(OPERATION_PRIORITIES)` this ensures class priority outweights operation priority
        #               A higher priority class's update should should come before a lowe priority class's create
        class_priority = (
            CLASS_PRIORITIES.index(records._name)
            if records._name in CLASS_PRIORITIES
            else len(CLASS_PRIORITIES)
        ) * len(OPERATION_PRIORITIES)

        return operation_priority + class_priority + 10

    def get_channel(self):
        """
        Allow to separate webhook queue-job to different channels
        """
        return self.env.ref("ol_webhooks.channel_webhook").complete_name

    class WebhookBroadCastDate(models.Model):
        _name = "webhook.broadcast.date"
        _description = "Webhook Broadcast date"

        # COLUMNS #####
        event_id = fields.Many2one(
            comodel_name="webhook.event",
            string="Webhook Event",
            readonly=True,
        )
        operation = fields.Char(string="Webhook Operation", readonly=True)
        odoo_model = fields.Char(string="Odoo Model", readonly=True, index=True)
        odoo_id = fields.Integer(string="Odoo id", readonly=True, index=True)
        # END #####

        def record(self, webhook_event, operation, records):
            if not records:
                # Handle case if no records were received
                return self.env[self._name]
            create_vals = []
            for record in records:
                create_vals.append(
                    {
                        "event_id": webhook_event.id,
                        "operation": operation,
                        "odoo_model": record._name,
                        "odoo_id": record.id,
                    }
                )
            return self.create(create_vals)

        def autovacuum(self):
            """
            Clean up the 'webhook.broadcast.date' table
            Delete all items that are older than 30 days
            Called from a cron.
            """

            _logger.info("Running `webhook.broadcast.date` autovacuum.")

            deadline = datetime.now() - timedelta(days=int(30))

            # We always want to keep the last entry even if it's old
            # We find their IDs and exclude them in the search below
            query = """
            SELECT
                DISTINCT ON (odoo_model, odoo_id)
                id
            FROM
                webhook_broadcast_date
            ORDER BY odoo_model, odoo_id, create_date DESC
            """
            self.env.cr.execute(query)
            latest_record_ids = [row["id"] for row in self.env.cr.dictfetchall()]

            while True:
                records = self.sudo().search(
                    [
                        ("create_date", "<=", deadline),
                        ("id", "not in", latest_record_ids),
                    ],
                    limit=1000,
                )
                if records:
                    records.unlink()
                    self.env.cr.commit()
                else:
                    break
            return True
