# Import Python Libs
from datetime import datetime
from psycopg2 import OperationalError

# Import Odoo Libs
from odoo import fields, models, tools
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.ol_graphql.schema.logger import GraphQLLogger


class GraphqlMixin(models.AbstractModel, GraphQLLogger):
    _name = "graphql.mixin"
    _description = "GraphQL Mixin"

    # COLUMNS #####
    origin_system = fields.Char(
        string="Origin System",
        help="System where this record was originally created",
        copy=False,
        index=True,
        default="ODOO",
    )
    is_graphql_placeholder = fields.Boolean(
        string="Placeholder Record",
        help="Record auto created by GraphQL by Odoo for a non existing related record.",
        default=False,
        index=True,
    )
    graphql_queue_ids = fields.One2many(
        comodel_name="graphql.queue", compute="_compute_last_graphql_queue_item_id"
    )
    last_graphql_queue_item_id = fields.Many2one(
        comodel_name="graphql.queue", compute="_compute_last_graphql_queue_item_id"
    )
    graphql_update_date = fields.Datetime(
        string="Datetime of the last update from graphql"
    )
    # END #########

    def get_graphql_queue_job_channel(self):
        """
        Get the specific GraphQL related Channel we should use
        to process a `queue.job`
        The values in the `channel_map` should match the `complete_name` in the `queue.job.channel` records
        defined in `ol_graphql/data/queue_job_channel.xml`

        We use separate channels for the record types to ensure problems in one channel are not blocking other channels.
        """
        channel_map = {
            "sale.order": "root.graphql_sale",
            "sale.booking": "root.graphql_sale",
            "res.customer": "root.graphql_customer",
            "res.partner": "root.graphql_customer",
            "product.template": "root.graphql_product",
            "product.pricelist.item": "root.graphql_product",
        }
        return channel_map.get(self._name, "root")

    def get_newer_graphql_queue_item(
        self, publish_time, transaction_id, message_source, throw_exception=False
    ):
        """
        Try to find any newer GraphQL Queue Item
        """

        for graphql_queue_id in self.graphql_queue_ids:
            if graphql_queue_id.transaction_id == transaction_id:
                # We should skip the current GraphQL Queue Item
                continue
            if graphql_queue_id.message_source != message_source:
                # We are only interested in messages from the same source system
                continue
            if graphql_queue_id.state in ["failed"]:
                # The given graphql queue has not the correct state
                # we don't care about it.
                continue
            if graphql_queue_id.publish_time >= publish_time:
                if throw_exception:
                    self.raise_ackable_exception(
                        f"Can't process {self._name} record with UUID: `{self.uuid}`!"
                        f"GraphQL Mutation Error: Can't process {self._name} record with UUID: `{self.uuid}`!"
                        " The record already has newer updates received. Existing update publish time:"
                        f" `{publish_time}` Message publish time:"
                        f" `{self.last_graphql_queue_item_id.publish_time}` This message will be acknowledged"
                        " as we don't wan't Pub/Sub to retry sending it!",
                        tid=transaction_id,
                    )
                else:
                    return graphql_queue_id

        return False

    def _compute_last_graphql_queue_item_id(self):
        # Some Odoo models use the `graphql.mixin` but don't have a UUID field
        has_uuid_field = hasattr(self.env[self._name], "uuid")

        for record in self:
            if has_uuid_field:
                queued_items = self.env["graphql.queue"].search(
                    [
                        ("odoo_class", "=", self._name),
                        ("record_uuid", "=", record.uuid),
                    ],
                    order="publish_time desc",
                )

                record.graphql_queue_ids = queued_items
                record.last_graphql_queue_item_id = (
                    queued_items[0] if queued_items else self.env["graphql.queue"]
                )
            else:
                record.graphql_queue_ids = self.env["graphql.queue"]
                record.last_graphql_queue_item_id = self.env["graphql.queue"]

    def write(self, vals):
        """
        Make sure we never override existing `origin_system` value
        """
        if "origin_system" in vals:
            vals.pop("origin_system")
        return super().write(vals)

    def get_related_res_company(self):
        """
        Return the related `res.company` record that is used by this model's record rules.
        This function should be overridden
        if we need to use other logic for specific odoo models!
        """

        res_company_field_name = "company_id"
        if self._fields.get(res_company_field_name, False):
            # SUDO is required here because the associated odoo company record might be in a different company than the current user!
            return getattr(self.sudo(), res_company_field_name)
        # In any other case return false
        return self.env["res.company"]

    def get_graphql_placeholder_values(
        self, message_field=False, message_values=False, transaction_id=False
    ):
        """
        This function is intended to be overridden in later modules
        """
        return {"is_graphql_placeholder": True}

    def _pre_graphql_create_actions(self, create_values):
        """
        This function is intended to be overridden in later modules
        """

    def _post_graphql_create_actions(self, **kwargs):
        """
        This function is intended to be overridden in later modules
        """

    def _pre_graphql_update_actions(self, write_values):
        """
        This function is intended to be overridden in later modules
        """

    def _post_graphql_update_actions(self, **kwargs):
        """
        This function is intended to be overridden in later modules
        """

    def persist_mutation_data(
        self,
        main_record_uuid,
        mutation_operation,
        actions,
        callback_functions,
        publish_time,
        transaction_id,
        message_source,
    ):
        try:
            # Try to get a GraphQL Queue Item that is newer than the one that triggered this function
            graphql_queue_id = self.get_newer_graphql_queue_item(
                publish_time=publish_time,
                transaction_id=transaction_id,
                message_source=message_source,
                throw_exception=False,
            )
            if graphql_queue_id:
                self.log_mutation_message(
                    "S:4 | Skipping further processing of current GraphQL Message"
                    f" (TI: `{transaction_id}`, PT: `{publish_time}`), as a newer GraphQL Message (TI:"
                    f" `{graphql_queue_id.transaction_id}`, PT: `{graphql_queue_id.publish_time}`) exists. |"
                    f" Record : {self} | UUID: {main_record_uuid}",
                    tid=transaction_id,
                    message_source=message_source,
                )
                # We simply return true so the related queue.job is registered successful
                # and no further processing happens
                return True

            mst = datetime.now()
            main_mutation_record = False

            self.log_mutation_message(
                f"S:3 | {mutation_operation.upper()} mutation data processing started for: "
                f"{self} | UUID: {main_record_uuid}",
                tid=transaction_id,
                message_source=message_source,
            )

            for action in actions:
                # Get the defaults
                current_record = False
                odoo_record = action["odoo_record"]
                function = action["function"]
                function_kwargs = action.get("function_kwargs", {})
                company = action.get("company", False)
                uuid = action.get("uuid", False)
                main_mutation_record_action = action.get(
                    "main_mutation_record_action", False
                )
                main_mutation_record_relationship_field_name = action.get(
                    "main_mutation_record_relationship_field_name", False
                )

                if (
                    # No odoo_record was defined,
                    # we don't use `not odoo_record` as an empty recordset is considered a valid input
                    odoo_record is None
                    # We don't have a valid function
                    or not function
                    # Company is missing
                    or not company
                ):
                    self.raise_graphql_error(
                        f"S:3 | Can't process action, vital action information is missing. | Action: {action}",
                        tid=transaction_id,
                        message_source=message_source,
                    )

                if (
                    main_mutation_record
                    and main_mutation_record_relationship_field_name
                ):
                    # Link the current odoo record to the main mutation record
                    # We can only do this if the `main_mutation_record` was already set,
                    #   that should happen in the first action (this why we use OdooMutationData.sort_actions())
                    function_kwargs[main_mutation_record_relationship_field_name] = (
                        main_mutation_record.id
                    )

                start_time = datetime.now()

                if (
                    not odoo_record  # The odoo record is false or an empty odoo recordset
                    and main_mutation_record  # The main mutation record was already created
                    and odoo_record._name
                    == main_mutation_record._name  # They are for the same model
                    and main_mutation_record.uuid == uuid  # The uuid is matching
                ):
                    # It's possible that this write is for the company dependent data of a newly created odoo record
                    # in that case the `odoo_record` would be an empty recordset, so instead of that we need to use
                    # the `main_mutation_record` which was set in the first create action
                    # We make sure we only do this during `write`, the odoo model and uuid are matching
                    odoo_record = odoo_record or main_mutation_record

                # Switch to the right Odoo company.
                # We are using `with_user` and `with_company` to ensure that we can write the data with the correct company for any follow-up actions
                odoo_record = (
                    odoo_record.with_user(company.company_user_id)
                    .with_company(company.id)
                    .with_context(transaction_id=transaction_id)
                )

                # Run the Odoo functionality associated with each function
                match function:
                    # Create
                    case "create":
                        current_record = odoo_record.with_context(
                            graphql_incoming_message=mutation_operation
                        ).create(function_kwargs)
                    # Write
                    case "update":
                        # TODO: do we want to reimplement the write optimization and use it here?
                        odoo_record.with_context(
                            graphql_incoming_message=mutation_operation
                        ).write(function_kwargs)
                        current_record = odoo_record
                    # Delete
                    case "delete":
                        # Depending if the given odoo record can be archived or not we trigger different functionality
                        if hasattr(odoo_record, "active"):
                            odoo_record.with_context(
                                graphql_incoming_message=mutation_operation
                            ).action_archive()
                        else:
                            odoo_record.with_context(
                                graphql_incoming_message=mutation_operation
                            ).unlink()
                        current_record = odoo_record
                    # Fallthrough
                    case _:
                        # Other Odoo specific functions
                        if hasattr(odoo_record, function):
                            assert isinstance(
                                function_kwargs, dict
                            ), f"Action function has invalid arguments: {function_kwargs}"
                            getattr(
                                odoo_record.with_context(
                                    graphql_incoming_message=function
                                ),
                                function,
                            )(**function_kwargs)
                        else:
                            self.raise_graphql_error(
                                f"Invalid function_name: `{function}` for `{odoo_record}`",
                                company=odoo_record.env.company.short_name.upper(),
                                tid=transaction_id,
                                message_source=message_source,
                            )

                if (
                    # If this action is for the main mutation record
                    main_mutation_record_action
                    # The value was not already set
                    and not main_mutation_record
                    # We have a record (empty recordset doesn't count)
                    and current_record
                    # We have a uuid
                    and uuid
                    # And the uuid matches the one of the main record
                    and uuid == main_record_uuid
                ):
                    main_mutation_record = current_record

                # Add a nice log entry
                if hasattr(odoo_record, "uuid") and odoo_record.uuid:
                    record_identifier = f" UUID: {odoo_record.uuid}"
                elif uuid:
                    record_identifier = f" UUID: {uuid}"
                else:
                    record_identifier = ""

                create_log_information = (
                    f"| Created record: {current_record}"
                    if function == "create"
                    else ""
                )
                write_log_information = (
                    "| Received message data matches existing Odoo values. No updates happened!"
                    if function == "update" and not function_kwargs
                    else ""
                )
                self.log_mutation_message(
                    f"S:3 | {function.upper()} action processed for:"
                    f" {odoo_record}{record_identifier} in"
                    f" {datetime.now() - start_time} {create_log_information} {write_log_information}",
                    company=odoo_record.env.company.short_name.upper(),
                    tid=transaction_id,
                    message_source=message_source,
                )

            if main_mutation_record:
                self.log_mutation_message(
                    "S:4 | Mutation data processing successful!"
                    f" [{main_mutation_record.display_name}] {main_mutation_record}| UUID:"
                    f" {main_mutation_record.uuid} | Done in {datetime.now() - mst}",
                    tid=transaction_id,
                    message_source=message_source,
                )

                # If callback functions were defined make sure we call them after we are done
                # we do this on main_mutation_record or self (this is needed in the case of a deletion)
                callback_record = main_mutation_record or self
                callback_record.run_queued_callback_functions(callback_functions)
                # Keep track when this record was last updated
                main_mutation_record.graphql_update_date = datetime.now()

        except OperationalError as operational_error:
            # For typical transaction serialization errors we don't want to log the error
            # as these errors will be handled by the `queue.job`
            if operational_error.pgcode not in PG_CONCURRENCY_ERRORS_TO_RETRY:
                # Add special log entry
                self.log_exception_message(
                    "S:3 | Can't process action. Non standard operational "
                    f"error: {operational_error.pgcode}. Error: `{operational_error}` | Action: "
                    f"{action}",
                    company=odoo_record.env.company.short_name.upper(),
                    tid=transaction_id,
                    message_source=message_source,
                )
                raise

            self.log_warning_message(
                "S:3 | could not process action as a result of an Odoo"
                f" Concurrency error: {tools.ustr(operational_error.pgerror, errors='replace')} | Action"
                f" Function: `{function}` | Record: {odoo_record}",
                company=odoo_record.env.company.short_name.upper(),
                tid=transaction_id,
                message_source=message_source,
            )

            raise RetryableJobError(
                "GraphQL Mutation Error | S:3 | Cant't process action. Odoo Concurrency error:"
                f" `{tools.ustr(operational_error.pgerror, errors='replace')}`. Error:"
                f" `{operational_error}` | Action: {action} | Record: {odoo_record} | Company:"
                f" {odoo_record.env.company.short_name.upper()} | MS: {message_source} | TI:"
                f" {transaction_id}",
                seconds=2,
            ) from operational_error
        except Exception as error:  # Get the odoo field names that we try to change
            # Add special log entry
            self.log_exception_message(
                f"S:3 | Can't process action. Error: `{error}` | Action:"
                f" {action} | Record: {odoo_record}",
                company=odoo_record.env.company.short_name.upper(),
                tid=transaction_id,
                message_source=message_source,
            )
            # Re-raise the exception
            raise

    def run_queued_callback_functions(self, callback_functions):
        """
        If a callback functions were defined make sure we call them
        """
        if not callback_functions:
            return

        for callback_function, callback_kwargs in callback_functions.items():
            if hasattr(self, callback_function):
                kwargs = callback_kwargs or {}
                assert isinstance(
                    kwargs, dict
                ), f"Passed callback arguments are not a dict: {kwargs}"
                getattr(self, callback_function)(**kwargs)

    def create_placeholder_record(
        self,
        values,
        field_name=False,
        log_field_name=False,
        transaction_id=False,
        prioritize_defaults=False,
    ):
        """
        Create a placeholder record using the provided message values and/or default values
        generated for this specific record. The logic will, by default, prioritize using the
        message values first in the placeholder unless 1. the Odoo field is not present in
        the message or 2. we have been asked to prioritize the generated default values over
        the ones in the message.

        For example, for generating a placeholder address-type partner in a sale order we
        need to decode message values to use within the placeholder and thus we don't want
        to use the message values verbatim. In this case, we'd set prioritize_defaults = True.
        """
        create_values = {}
        # if the given odoo class is "GraphQL aware", get the default values
        if hasattr(self, "get_graphql_placeholder_values"):
            default_values = self.with_context(
                transaction_id=transaction_id
            ).get_graphql_placeholder_values(
                message_field=field_name,
                message_values=values,
                transaction_id=transaction_id,
            )
        else:
            default_values = {}

        for _, odoo_field in self._fields.items():
            # regardless of source, we want to set the name to clearly show this is a placeholder
            if odoo_field.name == "name":
                # note that this doesn't "stick" for partners bc a name is formed from first + last names
                create_values[odoo_field.name] = (
                    f"[PENDING TI:{transaction_id}] {values.get(odoo_field.name, '')}"
                )
                continue

            # if we received a value from the incoming message we should set it
            if odoo_field.name in values:
                create_values[odoo_field.name] = values[odoo_field.name]

            # continue to reference the default values if either of these cases is true:
            # 1. the message does not have that field to reference or
            # 2. we have been told to prioritize the default values regardless of the message content
            if odoo_field.name in default_values and (
                not odoo_field.name in values or prioritize_defaults
            ):
                create_values[odoo_field.name] = default_values[odoo_field.name]

        # Create the placeholder record
        record = self.create(create_values)

        self.log_info_message(
            f"`{self},{field_name or log_field_name or ''}` | Placeholder created: `{record}` with"
            f" values: {create_values}",
            tid=transaction_id,
        )
        return record

    def find_related_odoo_record(self, odoo_object, field_name, value, tid):
        """
        Find the related Odoo record by the given field and value pair
        """
        related_record = odoo_object.search([(field_name, "=", value)])

        if len(related_record) >= 1:
            self.log_info_message(
                f"Found existing match(es) by {field_name}/{value} --> {related_record}",
                tid=tid,
            )
            if len(related_record) > 1:
                self.log_warning_message(
                    f"More than one exising record found for {field_name}/{value} -->"
                    f" {related_record} | Using first match: {related_record[0]}",
                    tid=tid,
                )
            return related_record[0]

        return False

    def get_record_dates_data(self):
        """
        Add the `graphql_update_date` to the dates data
        """
        res = super().get_record_dates_data()
        res.update({"graphql_update_date": self.graphql_update_date})
        return res
