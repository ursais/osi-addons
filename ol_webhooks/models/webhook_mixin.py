# Import Python libs
import copy

# Import Odoo libs
from odoo.osv import expression
from odoo import models, api, fields
from odoo.addons.ol_base.models.tools import operator_value_to_raw_sql


class WebhookMixin(models.AbstractModel):
    _name = "webhook.mixin"
    _description = "Webhook Mixin"

    # COLUMNS #####
    webhook_broadcast_date = fields.Datetime(
        string="Webhook Broadcast Date",
        help="Datetime of the last webhook call for this record",
        compute="_compute_webhook_broadcast_date",
        search="_search_webhook_broadcast_date",
    )
    # END #########

    def _compute_webhook_broadcast_date(self):
        query = """
        SELECT
            DISTINCT ON (odoo_model, odoo_id)
            odoo_id,
            create_date
        FROM
            webhook_broadcast_date
        WHERE
            odoo_model = %(odoo_model)s
            AND odoo_id IN %(odoo_ids)s
        ORDER BY odoo_model, odoo_id, create_date DESC;
        """
        query_args = {"odoo_model": self._name, "odoo_ids": tuple(self.ids)}
        self.env.cr.execute(query, query_args)
        results_dict = {
            x["odoo_id"]: x["create_date"] for x in self.env.cr.dictfetchall()
        }
        for rec in self:
            rec.webhook_broadcast_date = results_dict.get(rec.id, False)

    def _search_webhook_broadcast_date(self, operator, value):
        """Search for pickings with or without delivery holds"""
        if operator not in ("=", "!=", ">", ">=", "<", "<="):
            raise NotImplementedError(
                f"Invalid operator for field webhook_broadcast_date: {operator}"
            )

        query = f"""
        SELECT
            DISTINCT ON
            (odoo_model,
            odoo_id)
                    odoo_id,
            create_date
        FROM
            webhook_broadcast_date
        WHERE
            odoo_model = %(odoo_model)s
            AND {operator_value_to_raw_sql(field_name="create_date", operator=operator, value=value)}
        ORDER BY
            odoo_model,
            odoo_id,
            create_date DESC;
        """
        query_args = {"odoo_model": self._name}
        self.env.cr.execute(query, query_args)
        results = self.env.cr.dictfetchall()
        record_ids = [x["odoo_id"] for x in results]
        return [("id", "in", record_ids)]

    # CREATE #######

    @api.model
    def create(self, values):
        """Add webhooks into the `create` method"""
        res = super().create(values)
        res.sudo()._event_create(values)
        return res

    def _event_create(self, values):
        """
        Trigger related webhook events
        """
        if (
            not self.env["ir.config_parameter"]
            .sudo()
            .get_as_boolean("ol_webhooks.webhooks_enabled")
            or not self.exists()
        ):
            # Call the webhook only if
            #   - webhooks are enabled
            #   - the record was successfully created
            return

        # Prep the values first
        create_values = self.copy_and_clean_values(values)

        # Filter records
        eligible_records = self._create_filter(create_values)

        # Trigger Webhook
        self.trigger_event(
            records=eligible_records, values=create_values, operation="create"
        )

    def _create_filter(self, _):
        """
        This function is intended to be overridden in later modules
        :param list vaol_list:
            list of dictionaries: [{'field_name': field_value, ...}, ...]
            OR just a dictionary
            IMPORTANT: If you override this function you will need to handle both cases!
        """
        return self

    # WRITE #######

    def write(self, vals):
        res = super().write(vals=vals)
        # Prep the values first
        write_values = self.copy_and_clean_values(vals)
        self.sudo()._event_update(write_values)
        return res

    # TODO: We keep this commented out section here,
    #       until we have proved that calling normal write with the queue_job inverse identify key trick is enough
    #       to prevent the timing edge cases where the Webhok Call->Webhook Service->GQL Query is done faster than
    #       odoo can write the final result of the current function chain to the database.
    def _write(self, vals):
        """
        IMPORTANT:  Notice this is not `write` but `_write`!
                    We intentionally hook also into the low level implementation of the write function.
                    We do this as this way `_event_update` is also called after the current cache was already flushed and persisted in the database
                    which means by the time the webhook call is made all of the data gathered is already available in the database.
        """
        res = super()._write(vals=vals)

        # Prep the values first
        write_values = self.copy_and_clean_values(vals)
        self.sudo()._event_update(write_values)
        return res

    def _event_update(self, values):
        """Trigger related webhook events"""

        if (
            not self.env["ir.config_parameter"]
            .sudo()
            .get_as_boolean("ol_webhooks.webhooks_enabled")
        ):
            # Call the webhook only if webhooks are enabled
            return

        # Filter records
        eligible_records = self._update_filter(values)

        # Call Webhook
        self.trigger_event(records=eligible_records, values=values, operation="update")

    def _update_filter(self, values):
        """This function is intended to be overridden in later modules"""
        return self.base_filter(values)

    # DELETE #######

    def unlink(self):
        """Add webhooks into the `unlink` method"""
        self.sudo()._event_delete()
        res = super().unlink()
        return res

    def toggle_active(self):
        """
        Add webhooks into the Archive/Unarchive method
        """
        for record in self:
            if record.active:
                # If the record is changed to be archived send a delete message
                record.sudo()._event_delete()
            else:
                # If the record is changed to be active send an update message
                # other systems should have upsert meaning if the given record was missing
                # they will trigger a create instead of an update
                record.sudo().trigger_webhook()
        super().toggle_active()

    def _event_delete(self):
        """Trigger related webhook events"""

        if (
            not self.env["ir.config_parameter"]
            .sudo()
            .get_as_boolean("ol_webhooks.webhooks_enabled")
        ):
            # Call the webhook only if webhooks are enabled
            return

        # Filter records
        eligible_records = self._delete_filter()

        # Trigger Webhook
        self.with_context(webhook_no_delay=True).trigger_event(
            records=eligible_records, values={}, operation="delete"
        )

    def _delete_filter(self):
        """This function is intended to be overridden in later modules"""
        empty_recordset = self.env[self._name]
        if self.env.context.get("skip_webhooks"):
            # If the context variable is set
            # we should not trigger webhooks
            return empty_recordset
        return self

    @staticmethod
    def copy_and_clean_values(values):
        """
        As class implementations of WebhookMixin could
        potentially manipulate the create/write values
        but we don't want to alter the original values
        as those could still be used in "real" create/write calls
        we copy the dictionary.
        We also want to remove certain fields that are automatically added by core odoo.
        """

        # As values could be a `<class 'odoo.tools.misc.frozendict'>` we first copy the dictionary
        values_copy = values.copy()
        fields_to_filter = ["create_date", "create_uid", "write_date", "write_uid"]
        for field in fields_to_filter:
            values_copy.pop(field, None)
        return values_copy

    @staticmethod
    def get_webhook_trigger_computed_fields():
        """
        If any of these fields is in values we should potentionaly trigger a webhook.
        This method is designed to be extended by other modules.
        """
        return []

    @staticmethod
    def get_webhook_trigger_computed_models():
        """
        If related fields for any of these objects changes we want to trigger a webhook
        This method is designed to be extended by other modules.
        """
        return []

    def webhook_computed_field_triggers(self, values):
        """
        Logic to determine which computed fields we should allow to trigger webhooks
        """

        # The fields of this object
        fields = self._fields

        trigger_fields = self.get_webhook_trigger_computed_fields()
        trigger_models = self.get_webhook_trigger_computed_models()

        if not trigger_fields and not trigger_models:
            # If none of these is defined we can return False
            return False

        for field_name, _ in values.items():
            field = fields.get(field_name, False)

            if not field:
                # We only care about fields that exist on this model
                continue

            if field in trigger_fields:
                # If this field is marked as a trigger_field
                # return True as we potentionaly need to trigger a webhook
                return True

            if (
                field.related
                and field.related_field
                and field.related_field.model_name in trigger_models
            ):
                # If this field related to any trigger models
                # return True as we potentionaly need to trigger a webhook
                return True

        return False

    def base_filter(self, values):
        """
        Basic record filtering that should happen for all records.
        These can be escaped by overriding this function
        or adding the relevant context variables `webhook_skip_NAME_check`
        """
        empty_recordset = self.env[self._name]

        if any(
            rec for rec in self if isinstance(rec.id, models.NewId)
        ) or self.env.context.get("skip_webhooks"):
            # If self is a pseudo model
            # or the context variable is set
            # we should not trigger webhooks
            return empty_recordset

        if (
            # Don't do this if `values` contains any computed fields we consider as webhook triggers
            not self.webhook_computed_field_triggers(values)
            and not self.env.context.get("webhook_skip_computed_fields_check")
            and self.all_computed_fields(fields=list(values.keys()))
        ):
            # If all changed fields are computed we don't want to trigger webhooks
            return empty_recordset

        return self

    # METHODS #######

    def trigger_event(self, records, values, operation):
        # Trigger any custom events

        records, values = self.trigger_custom_events(records, values, operation)

        if records.skip_trigger(values, operation):
            return False

        # Find the event based on the model and operation
        webhook_event = self.get_event(operation)

        if webhook_event:
            webhook_event.trigger(records=records)

        return True

    def skip_trigger(self, values, operation):
        # Don't do anything if we don't have any eligible records left
        # or all of the values have been handled (ir. values dict is empty)

        if self.env.context.get("force_webhook_trigger", False) and self:
            return False

        if not self or (operation not in ["delete"] and not values):
            return True

        return False

    def trigger_custom_events(self, records, values, operation):
        """
        This function is intended to be overridden in later modules.

        Example function:

        def trigger_custom_events(self, records, values, operation):

            # Filter the records based on any record/business logic
            filtered_records = records.filtered(
                lambda record: record.SOME_FIELD != SOME_VALUE
            )

            # Find the specific `webhook.even` XML record
            webhook_event = self.env.ref(f"ol_webhooks.SOME_XML_PRETAG_{operation}")

            if filtered_records and webhook_event:
                # If the filter returned any records and we found the `webhook.event`
                webhook_event.trigger(records=filtered_records)

            # Decide if we want to allow all records to be passed on, or remove some
            remaining_records = records - filtered_records
            return remaining_records, remaining_values

        """
        return records, values

    def get_event(self, operation, include_custom_events=False):
        """
        Get the Webhook Event for the given Odoo model and operation
        Only get one event, even if there are multiple defined
        """

        domain = [
            ("model_id.model", "=", self._name),
            ("operation", "=", operation),
        ]

        if include_custom_events:
            # Include custom events
            domain = expression.AND([domain, [("is_custom", "=", True)]])
        else:
            domain = expression.AND([domain, [("is_custom", "=", False)]])

        return self.env["webhook.event"].search(
            domain,
            limit=1,
            order="id ASC",
        )

    def trigger_webhook(self, operation="write"):
        if operation == "create":
            return self.with_context(force_webhook_trigger=True)._event_create({})
        if operation == "delete":
            return self.with_context(force_webhook_trigger=True)._event_delete({})

        return self.with_context(force_webhook_trigger=True)._event_update({})
