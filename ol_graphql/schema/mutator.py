# Import Python Libs
import json
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.decoder import BaseDecoder
from odoo.addons.ol_graphql.schema.mutation_data import OdooMutationData
from odoo.addons.ol_graphql.schema.logger import AckableException
from odoo.addons.ol_base.models.tools import stringify_nested_odoo_objects
from odoo.exceptions import AccessDenied


class Mutator(BaseDecoder):
    def __init__(self, info, odoo_class, data, operation, uuid=False):
        self.info = info

        # Set the Odoo environment of the mutation
        # we change the user from Public to the given company user
        # IMPORTANT:    This could be a security risk if we would open Odoo GraphQL to an open network.
        #               Right now only validated services that are in our own secured shielded network can make calls to Odoo GraphQL
        env = info.context["env"]

        if not env.context.get(
            "graphql_api_client_signature_validated", False
        ) and not env.user.user_has_groups("ol_graphql.graphql_mutation"):
            _logger.warning(
                f"GraphQL Error: Access denied! User `{env.user.name} ({env.user})"
                " has no permission to run GraphQL Mutations!"
            )
            raise AccessDenied()

        self.env = env(user=env.company.company_user_id)

        # Update the Mutator context
        context = self.env.context.copy()
        context.update({"graphql_incoming_message": operation})
        self.env.context = context

        # IMPORTANT: While the incoming mutation is for one specific Odoo record
        # during the decoding of the message we potentionaly have to update / create / delete other Odoo records.

        # self.odoo_class - always refers to the main odoo_class the GraphQL Mutation was made for
        self.odoo_class = odoo_class

        # self.odoo_record - always refers to the main odoo record the GraphQL Mutation was made for
        self.odoo_record = self.env[self.odoo_class]

        # Get fields defined for the given odoo record
        self.valid_odoo_fields = list(self.odoo_record._fields.keys())

        # UUID for the specific record that we need to create, update or delete
        self.uuid = uuid or data.get("uuid", False)

        # self.data - always refers to the main data we received in GraphQL Mutation
        self.data = data

        # The operation of the main GQL Mutation
        self.operation = operation

        # The collection of decoded data, this represents the data in a format that odoo can understand
        # IMPORTANT: While the incoming mutation is for one specific Odoo record,
        # during the decoding of the message we potentionaly have to update / create / delete other Odoo records
        # these values will be also added to the `odoo_data` instance
        self.odoo_data = OdooMutationData(self.env, self.uuid)

        # Transaction ID of the incoming GQL Mutation, this is vital information we need to log
        # this allows us to do efficient and correct debugging
        self.transaction_id = data.get("transaction_id", False) if data else False

        # The original system that sent the message
        self.message_source = data.get("message_source", False) if data else False

        # The published time of the message according to Pub/Sub
        message_publish_time = data.get("message_publish_time", False)

        # Convert the published time to something Odoo can understand
        # https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.Timestamp
        self.publish_time = (
            datetime.fromtimestamp(int(message_publish_time) / 1e9)
            if message_publish_time
            else datetime.now()
        )

        # By default we always want to persist the decoded data
        self.persist_decoded_data = True

        # Keep track if we had to do an upsert or not
        self.upsert = False

        # Global setting that indicates whether we allow update actions to be performed from CREATE messages,
        # if the CREATE message references a record that already exists in Odoo
        # IMPORTANT: this action can still happen for PLACEHOLDER records, even if this global setting is False
        self.update_from_create = self.env["ir.config_parameter"].get_as_boolean(
            "ol_graphql.graphql_update_from_create", False
        )

        # Global setting that indicates whether we allow create actions to be performed from UPDATE messages,
        # if the UPDATE message references a record that does not already exist in Odoo
        self.create_from_update = self.env["ir.config_parameter"].get_as_boolean(
            "ol_graphql.graphql_create_from_update", False
        )

        self.log_received_message()

        # Dictionary containing parameters for _post_graphql_create_actions
        self.post_graphql_create_kwargs = {}
        # Dictionary containing parameters for _post_graphql_update_actions
        self.post_graphql_update_kwargs = {}

        self.fields_to_include = self.get_fields_to_include()
        self.fields_to_exclude = self.get_fields_to_exclude()

    def get_fields_to_include(self):
        """
        Specific field that we want to process from an incoming GraphQL message. If fields_to_include is defined only fields that are in this array are processed everything else is disregarded!
        """
        return []

    def get_fields_to_exclude(self):
        """
        These are fields that could exist in odoo, we could potentially get values for them in the message, but we don't want to set the values based on them. We don't necessarily need to add fields where the message key and Odoo field name are not matching but it's good practice and helps us understand which fields are used and which ones are excluded.
        ex.   Message has `net_terms` which corresponds with the Odoo `net_terms_active` field, as the two field names
               are not matching we don't need to specifically call out the field as send only. As the "decoder" is missing for the field,
               we are going to ignore it by default
        """
        return []

    def add_decoded_data(
        self, values, operation=False, odoo_record=None, company=False
    ):
        """
        Add the given decoded value to the odoo_data collection.
        IMPORTANT:  You should only use this function if you want to store data for the Main Odoo record that the received message is for!
                    In other cases (ex. related record updates/creates, running other functionality) use the `self.odoo_data.add_action()` directly

        Keyword arguments:
        @param values:      Dictionary - Ex. {"first_name": "Jon"}
                            The decoded values we should store, in a format that odoo's `write()` and `create()` methods can directly accept.
        @param operation:   String - Ex.: "update"
                            The operation we want to trigger for the given odoo record.
                            `update` will trigger an odoo `write`
                            `create` will trigger an odoo `create`
                            `delete` will trigger an odoo `unlink` or `action_archive`
        @param odoo_record: Inherited models.Model - Ex. res.partner() or res.partner(666)
                            The main odoo record the incoming message is for identified by a UUID
        @param company:     res.company() Ex.: res.company(1)
                            The `company` and related user `company.company_user_id`
                            that will be used to run the given action on the odoo_record
                            when we persist the decoded data
        """
        if not self.persist_decoded_data:
            # Allows us to skip setting these the decoded data
            return values

        try:
            # Fall back to the current default operation
            operation = operation or self.operation

            # Fall back to the record from the incoming message
            # IMPORTANT:    Notice that we use `None` as  the default value
            #               We do this as empty odoo recordsets (ex.: product.template())
            #               would be recognized as False, but in this case an empty recordset is usable information for us
            if odoo_record is None:
                odoo_record = self.odoo_record

            self.odoo_data.add_value_to_action(
                odoo_record=odoo_record,
                function=operation,
                values=values,
                uuid=self.uuid,
                company=company,
                # We can default to true as this function should always used for the main mutation record
                main_mutation_record_action=True,
            )

            return values
        except Exception as error:
            self.log_exception_message(
                f"S:2 | Error adding decoded data. Error: `{error}` | Odoo record: "
                f"{odoo_record} | Operation: {operation} | UUID: {self.uuid} | Values: {values}",
                company=company,
            )
            # Re-raise the exception
            raise error

    def get_decoded_data(
        self, operation=False, odoo_record=None, company=False, uuid=False
    ):
        """
        Get the already decoded values for a uuid/operation/company combination
        """
        try:
            # Handle defaults
            operation = operation or self.operation
            odoo_record = odoo_record or self.odoo_record
            company = company or self.env.company
            uuid = uuid or self.uuid

            action = self.odoo_data.get_action(
                odoo_record=odoo_record, uuid=uuid, function=operation, company=company
            )
            if not action:
                return None
            return action.function_kwargs
        except Exception as error:
            self.log_exception_message(
                f"S:2 | Could not get decoded data. Error: `{error}` | Odoo record: "
                f"{odoo_record} | Operation: {operation} | UUID: {uuid}",
                comapny=company,
            )
            # Re-raise the exception
            raise error

    def get_decoded_field_value(
        self, field_name, operation=False, odoo_record=None, company=False, uuid=False
    ):
        """
        Get the already decoded value for a field with the correct uuid/operation/company combination
        key: The decoded odoo field name
        """
        decoded_data = self.get_decoded_data(
            operation=operation, odoo_record=odoo_record, company=company, uuid=uuid
        )
        return decoded_data.get(field_name, None) if decoded_data else None

    def create(self):
        """
        Create the odoo record from the received mutation data
        """

        try:
            # Validate the data and update `self.odoo_record`
            # By default `self.odoo_record` is an empty recordset
            # but if `update_from_create` was enabled we would update the existing self.odoo_record
            self.validate_create()

            # If we have triggered an update from create, then self.operation was change to 'update'
            # and the message has already been processed. Let's not process it again
            if self.operation == "create":
                # Process the incoming data so it fits Odoo's data structure
                self.process_create_data()

                # Persist the change to Odoo
                self.apply_odoo_changes(
                    {"_post_graphql_create_actions": self.post_graphql_create_kwargs}
                )

        except AckableException as error:
            self.log_exception_message(
                f"S:2 | Create Ackable Exception: {error.message} | Odoo record: "
                f"{self.odoo_record} | UUID: {self.uuid} | Upsert: {self.upsert}",
                traceback=error.traceback,
            )
            return self.odoo_record.with_context(graphql_successful=True)
        except Exception as error:
            self.log_exception_message(
                f"S:2 | Error during create mutation: {error} | Odoo record: "
                f"{self.odoo_record} | UUID: {self.uuid} | Upsert: {self.upsert}"
            )
            # Re-raise the exception
            raise error
        else:
            return self.odoo_record.with_context(graphql_successful=True)

    def validate_create(self):
        """
        Do some basic validation before we try to create a record
        """
        try:
            if not self.uuid:
                # All new records created via GQL need to have a UUID
                self.raise_graphql_error(
                    f"Can't create {self.odoo_class}! `uuid` must be part of the creation data"
                )

            # Try to find the record based on the UUID
            # we want to include archived records in to the results
            # we use sudo() to bypass access rights checks so we can find records in all companies
            # SUDO is required here since we might find records in all companies and we need to read fields
            self.odoo_record = (
                self.odoo_record.sudo()
                .with_context(active_test=False)
                .get_by_uuid(self.uuid)
            )
            # We switch the found records environment to only active access records!
            self.odoo_record = self.odoo_record.with_context(active_test=True)

            if self.odoo_record.exists():
                if self.update_from_create or self.odoo_record.is_graphql_placeholder:
                    self.log_info_message(
                        f"Can't create {self.odoo_class} record with UUID: `{self.uuid}`! The"
                        " record already exists in Odoo. Updating record from create data"
                    )
                    # We need to switch the operation to update
                    self.switch_operation(new_operation="update")
                    return self.update()

                self.raise_ackable_exception(
                    f"Can't create {self.odoo_class}! {self.odoo_class} record with"
                    f" UUID: `{self.uuid}` already exists in the Odoo. This message will be acknowledged as"
                    " we don't wan't Pub/Sub to retry sending it!"
                )

            ongoing_create_mutations = self.get_ongoing_create_mutations()
        except Exception as error:
            self.log_exception_message(
                f"S:2 | Error during create validation. Error: `{error}` | Odoo "
                f"record: {self.odoo_record} | UUID: {self.uuid}"
            )
            # Re-raise the exception
            raise error

        if ongoing_create_mutations:
            self.raise_ackable_exception(
                f"Can't create {self.odoo_class} record with UUID: `{self.uuid}`! A"
                " creation is already underway. Existing create job:"
                f" `{ongoing_create_mutations.read(['name', 'method_name'])}` This message will be"
                " acknowledged as we don't wan't Pub/Sub to retry sending it!"
            )

        # We don't have to do anything else as `self.odoo_record` is already defined as an empty recordset

    def process_create_data(self):
        """
        Data processing related to record creation
        """

        # As a first step decode and switch to the correct odoo company
        self.set_correct_environment()

        self.process_data()

    def update(self):
        """
        Update the given Odoo records based on the received values
        """
        try:
            # Validate the data and try to get the partner
            # or handle any `upsert`
            if not self.odoo_record:
                self.validate_update()

            if self.upsert and self.odoo_record.env.context.get(
                "graphql_successful", False
            ):
                # If this was an `upsert` (create instead of update) and that was successful we can just return
                return self.odoo_record

            # Process the incoming data so it fits Odoo's data structure
            self.process_update_data()

            # If we receive an update mutation for a previously created Placeholder record
            # we want to ensure to remove that placeholder flag
            if self.odoo_record.is_graphql_placeholder:
                self.add_decoded_data(values={"is_graphql_placeholder": False})
            self.apply_odoo_changes(
                {"_post_graphql_update_actions": self.post_graphql_update_kwargs}
            )

        except AckableException as error:
            self.log_exception_message(
                f"S:2 | Update AckableException: {error} | Odoo record: "
                f"{self.odoo_record} | UUID: {self.uuid} | Upsert: {self.upsert}",
                traceback=error.traceback,
            )
            return self.odoo_record.with_context(graphql_successful=True)
        except Exception as error:
            self.log_exception_message(
                f"S:2 | Error during update mutation: {error} | Odoo record: "
                f"{self.odoo_record} | UUID: {self.uuid} | Upsert: {self.upsert}"
            )
            # Re-raise the exception
            raise error
        else:
            # Return the record with the additional context
            return self.odoo_record.with_context(graphql_successful=True)

    def process_update_data(self):
        """
        Data processing related to record update
        """

        # We don't want to change the `origin_system` from update mutations
        if "origin_system" in self.data:
            self.data.pop("origin_system")

        if "uuid" in self.data:
            # We should never overwrite the existing UUID
            # so we remove the UUID value from the data
            self.data.pop("uuid")

        # As a first step decode and switch to the correct odoo company
        self.set_correct_environment()

        self.process_data()

    def process_data(self):
        """
        Process the incoming GQL Mutation data.
        Data processing is made up from 2 steps:

        1. Find related decoding function
            For each incoming key/value pair this could end up in 4 scenarios:
                A. The incoming field is excluded (hard coded list) or not included in a hard coded list, so we simple skip it
                B. There is no decoding field or function defined for it,
                  if the message field name matches the odoo field name we use the key/value pair as is.
                  We should only use this solution if the incoming message value does not have to be changed.
                C. There is decoding field. This means we want to rename the incoming message key so it matches
                  and existing Odoo field name.
                  We should only use this solution if the incoming message value does not have to be changed.
                D. There is a decoding function, this might change both the key/value of the incoming data, and additionally
                  create/update/delete other Odoo records outside of the direct target of the GQL mutation.
        2. Run decoding
            For A. B. C. options from above, we update the `self.odoo_data` instance directly in this function
            for option D. we need to do that directly from the decode function.

        """

        # Loop through each key/value fair coming from the message
        for field, value in self.data.items():
            try:
                self.process_data_field(field, value)
            except AckableException as error:
                # Re-raise the exception
                raise error
            except Exception as error:
                self.log_exception_message(
                    f"S:2 | Decoding field `{field}` failed. Error: `{error}` | Field values: {value}"
                )
                # Re-raise the exception
                raise error

        return True

    def process_data_field(self, field, value):
        """
        Decode the field and its value
        """

        if self.fields_to_include and field not in self.fields_to_include:
            # Option A.
            # Filter out fields that we did not specifically called out to be processed
            return False

        if self.fields_to_exclude and field in self.fields_to_exclude:
            # Option B.
            # Filter out fields that we don't want to set in Odoo
            return False

        # Get the dynamic decode field/function name
        decoder_name = f"decode_{field}"

        if not hasattr(self, decoder_name):
            # No decode field or method found.
            # Use the key/value as it is in the message

            if field not in self.valid_odoo_fields:
                # Filter out anything that is not an Odoo field
                # This is important to keep the odoo create/write values clean
                return False

            # Option B.
            return self.add_decoded_data(values={field: value})

        # If there is a decode field function get it
        decoder = getattr(self, decoder_name)

        if isinstance(decoder, str):
            # Option C.
            # String decodes just rename the key, and keep the same value
            return self.add_decoded_data(values={decoder: value})

        if callable(decoder):
            # Option D.
            # Decoder is a function, so call it and include its results
            return decoder(field, value)

        return False

    def set_correct_environment(self):
        """
        Before decoding we need to make sure we use the correct user (res.users) and company (res.company)
        both on the odoo record the mutation is for, and also the mutator environment it self.

        This is important as this user/company is going to be used
        when we create the odoo_data actions.

        It also makes sure `company_dependent` decoding works correctly. See: `decode_company_dependent_field_value()`
        """

        current_user = self.env.company.company_user_id
        mutator_user = self.get_mutator_user()

        try:
            # Switch the odoo record environment to the correct user
            # this also remove the record's environment's `superuser` mode if it was set previously
            self.odoo_record = self.odoo_record.with_user(mutator_user)

            # Switch the Mutators Environment to match the correct user
            # We can't use `self = self.with_user(company.company_user_id)`
            # so we swap the environment
            self.env = self.env(user=mutator_user)
            self.odoo_data.env = self.env

            self.log_mutation_message(
                "S:2 | Switched to the correct environment by switching user "
                f"from '{current_user}' to {mutator_user} | Odoo "
                f"record: {self.odoo_record} | Operation: {self.operation} | UUID: {self.uuid}"
            )
        except Exception as error:
            self.log_exception_message(
                "S:2 | Could not switch to the correct environment. Switching user "
                f"from '{current_user}' to {mutator_user} | Error: `{error}` | Odoo "
                f"record: {self.odoo_record} | Operation: {self.operation} | UUID: {self.uuid}"
            )
            # Re-raise the exception
            raise error

    def get_mutator_user(self):
        """
        Get the odoo `res.users` we should use to process the incoming message.
        This user is used in the Mutator's Environment `self.env` and `self.odoo_data.env`
        and also the odoo records Environment `self.odoo_record.env`.
        The user is always returned from the related `res.company` record.

        The logic needs to differ based on the operation of the mutation (self.operation):

         :returns: - `res.users` record
        """
        try:
            # Get the company(s) from the message or fall back to the default admin company
            # As `message_companies` could be an empty record set we need to make sure we return the correct value
            # `message_companies` could also be an recordset of multiple companies, in this case we just choose the first one
            message_companies = self.get_message_companies()
            # `message_companies` could be a recordset of multiple companies, in this case we just choose the first one
            message_company = (
                message_companies[0] if message_companies else self.env["res.company"]
            )

            # Get the company from the odoo record
            odoo_record_company = self.odoo_record.get_related_res_company()
            match self.operation:
                case "create":
                    # As the odoo record does not exist we only care about the company that is set in the incoming message.
                    company = message_company
                case "update":
                    # We should use the company(s) that is set in the incoming message, This company is set on record in `persist_mutation_data()` before the rest of the values are written to the record.
                    # This solves the case when the incoming message will change the company that is currently set on the record.
                    # If the message does not contain company information fall back to the Odoo record's current company
                    company = message_company or odoo_record_company
                case _:
                    # We should use the company that is currently set on the odoo record. We need need to do that because Odoo's record rules would prevent us from CRUD command if we used a different company/user.
                    company = odoo_record_company
            # The fallback should be the admin company
            company = company or self.env.company

            # Return the related user
            return company.company_user_id

        except Exception as error:
            self.log_exception_message(
                f"S:2 | Error getting mutation user: {error} | Odoo "
                f"record: {self.odoo_record} | Operation: {self.operation} | UUID: {self.uuid}"
            )
            # Re-raise the exception
            raise error

    def get_message_companies(self):
        """
        Get the `res.company` value from the incoming message
        This could be extracted in different ways for each odoo record.
        This function covers the most generic situation of the values being present
        in the `onlogic_companies` and `onlogic_company` fields.
        Other odoo records might need to override this function to implement their own logic.
        """
        company_id = False
        for company_field in ["onlogic_companies", "onlogic_company"]:
            # We can do this as either one or the other field will be in the message
            if not company_id and company_field in self.data:
                # Get the decoded value but don't store it
                decoded_value = self.force_decode(company_field)
                # The decoded value is always a dictionary {odoo_field_name: value}
                # In the case of 'onlogic_companies', 'onlogic_company'
                company_id = (
                    decoded_value.get("company_id", False) if decoded_value else False
                )

        # If we got a company ID get the related Odoo company record
        # we use sudo() to bypass access rights checks so we can find records in all companies
        # Sort the companies by their ID's to get consistent results
        return (
            self.env["res.company"]
            .sudo()
            .browse(company_id)
            .exists()
            .sorted(key=lambda c: c.id)
        )

    def force_decode(self, field_name, persist=False, remove=False):
        """
        Force decode a field/value pair from the message.
        This allows us to decode certain fields before the loop in `process_data` would get to them.
        field_name: Name of the field in the incoming message
        """

        # Enabling or disabling storing decoded data
        # based on the `persist` attribute
        # If `persist` is False we only want to get the decoded field value
        # but not save it to the list of decoded fields
        self.persist_decoded_data = persist

        if field_name not in self.data:
            return None

        values = self.process_data_field(field_name, self.data[field_name])

        if remove:
            # Remove the decoded key/value pair from `data`
            del self.data[field_name]

        # Re-enable storing decoded data
        self.persist_decoded_data = True

        return values

    def validate_update(self):
        """
        Do some basic validation before we try to update a record
        """

        # Try to get the UUID from the GraphQL data
        data_uuid = self.data.get("uuid", False)

        if data_uuid and data_uuid != self.uuid:
            # The UUID used as an argument doesn't match the UUID passed in the data
            self.raise_graphql_error(
                f"Can't update {self.odoo_class}! "
                f"Argument UUID: `{self.uuid}` and data UUID: `{data_uuid}` are not matching. "
                "It is not allowed to update the UUID of an existing record!"
            )

        # Try to find the record based on the UUID
        # we want to include archived records in to the results
        # we use sudo() to bypass access rights checks so we can find records in all companies
        # SUDO is required here since we might find records in all companies and we need to read fields
        self.odoo_record = (
            self.odoo_record.sudo()
            .with_context(active_test=False)
            .get_by_uuid(self.uuid)
        )
        # We switch the found records environment to only active access records!
        self.odoo_record = self.odoo_record.with_context(active_test=True)

        # Find any ongoing create mutation for this exact record
        ongoing_create_mutations = self.get_ongoing_create_mutations()

        if self.odoo_record.exists():
            self.odoo_record.get_newer_graphql_queue_item(
                publish_time=self.publish_time,
                transaction_id=self.transaction_id,
                message_source=self.message_source,
                throw_exception=True,
            )
            return

        # Check if upserts are enabled for the specific system on the incoming message
        source_system = self.env["external.system"].search(
            [("message_source_string", "=", self.message_source)]
        )
        system_upsert = source_system.enable_upsert if source_system else True

        if not ongoing_create_mutations and self.create_from_update and system_upsert:
            # If the given Odoo record doesn't exists we should create it

            # Make sure we keep track that we switched to `upsert` from a normal `update`
            self.upsert = True

            # Add the `uuid` to the data as that is what we get during the normal create mutation
            self.log_mutation_message(
                f"S:2 | Can't update {self.odoo_class} record with UUID: `{self.uuid}`! "
                "The record does not exists in Odoo. Creating record from update data."
            )
            # We need to switch the operation to create
            self.switch_operation(new_operation="create")

            # Also make sure we are setting the correct UUID for the create values
            self.data["uuid"] = self.uuid
            self.odoo_record = self.create()
            return

        self.raise_graphql_error(
            f"S:2 | Can't update {self.odoo_class} record with UUID: `{self.uuid}`! "
            "The record does not exists in Odoo. Upsert not possible, create job already exists. Update "
            "should be retried later."
        )

    def switch_operation(self, new_operation):
        # Switch the operation to `new_operation`
        self.operation = new_operation

    def get_identity_key(self, odoo_class, uuid):
        """
        Create the queue identify key by hashing the odoo_class and uuid
        """

        data = {
            "odoo_class": odoo_class,
            "uuid": uuid,
        }
        return f"{self.env['api'].generate_hmac_signature(key=odoo_class, msg=data)}"

    def get_ongoing_create_mutations(self):
        """
        Find existing Jobs that are for the same record.
        IMPORTANT: We use `LIKE` to search for the base `identity_key`
        this is important as later when we create the related `queue.job` record, we extend this
        `identity_key` with the publish time and related company
        """

        identity_key = self.get_identity_key(odoo_class=self.odoo_class, uuid=self.uuid)
        return self.env["queue.job"].search(
            [
                ("model_name", "=", self.odoo_class),
                ("identity_key", "like", f"%-{self.operation}-{identity_key}"),
                ("state", "in", ["pending", "enqueued", "started"]),
                ("method_name", "=", "persist_mutation_data"),
            ],
            order="id desc",
        )

    def delete(self):
        # Validate the data and try to get the partner
        self.validate_delete_and_get_record()
        self.set_correct_environment()
        self.add_decoded_data(values={})
        self.apply_odoo_changes()
        return self.odoo_record.with_context(graphql_successful=True)

    def validate_delete_and_get_record(self):
        """
        Do some basic validation before we try to delete a record
        """
        self.odoo_record = self.odoo_record.with_context(active_test=False).get_by_uuid(
            self.uuid
        )
        # We switch the found records environment to only active access records!
        self.odoo_record = self.odoo_record.with_context(active_test=True)

        if not self.odoo_record.exists():
            self.raise_graphql_error(
                f"Can't delete {self.odoo_class} record with UUID: `{self.uuid}`! "
                "The record does not exists in Odoo."
            )

    def apply_odoo_changes(self, callback_functions=False):
        """
        Handle updating / creating / deleting Odoo records.
        IMPORTANT: While the incoming mutation is for one specific Odoo record
        during the decoding of the message we potentionaly have to update / create / delete other Odoo records.
        """

        try:
            # Add a graphql queue item, so later mutations can track what happened earlier
            graphql_queue = self.add_queue_item(values=self.odoo_data.actions)

            # Set the channel to the dedicated GraphQL one
            channel = self.odoo_record.get_graphql_queue_job_channel()

            priority = int(str(int(datetime.now().timestamp() * 1000))[4:])

            # Generate  `identity_key`
            identity_key = self.get_identity_key(
                odoo_class=self.odoo_record._name, uuid=self.uuid
            )

            context = self.env.context.copy()
            context.update(
                {
                    # We need to `company_id` in the context so the created `queue_job`
                    # also uses this company for its environment: oca/queue/queue_job/job.py line: 493 `if "company_id" in env.context:`
                    "company_id": self.env.company.id,
                    "transaction_id": self.transaction_id,
                    "graphql_queue_id": graphql_queue.id,
                }
            )

            odoo_data_actions = self.odoo_data.apply()
            if not odoo_data_actions:
                self.raise_graphql_error(
                    "S:3 | Something is not right, no mutation actions! | Odoo"
                    f" record: {self.odoo_record} | Operation: {self.operation} | UUID: {self.uuid} | Values:"
                    f" {self.odoo_data.actions}"
                )

            delayed = self.odoo_record.with_context(context).with_delay(
                priority=priority,
                eta=None,
                # Persisting the data can run into Odoo database concurrency issues so we want to try again
                max_retries=3,
                description=self.transaction_id,
                channel=channel,
                identity_key=f"{self.publish_time}-{self.operation}-{identity_key}",
            )

            return delayed.persist_mutation_data(
                main_record_uuid=self.uuid,
                mutation_operation=self.operation,
                actions=odoo_data_actions,
                callback_functions=callback_functions,
                publish_time=self.publish_time,
                transaction_id=self.transaction_id,
                message_source=self.message_source,
            )
        except Exception as error:
            self.log_exception_message(
                f"S:3 | Error during applying odoo changes. | Odoo record: {self.odoo_record} |"
                f" Operation: {self.operation} | Upsert: {self.upsert} | UUID: {self.uuid} | Values:"
                f" {self.odoo_data.actions} | Error: {error}"
            )
            # Re-raise the exception
            raise error

    def add_queue_item(self, values):
        """
        Keep track of the mutation queue
        """

        try:
            # Try to stringify the values so we can save them to the `Text` field of the graphql.queue
            stringified_values = json.dumps(stringify_nested_odoo_objects(values))
        except Exception as exception:
            # If stringify fails save log exception and save placeholder text.
            # We only use `graphql_queue.values` for debugging through the UI
            # so this shouldn't cause any issues.
            msg = "Could not stringify values for graphql.queue!"
            self.raise_graphql_error(
                f"S:3 | {msg} | Odoo record: {self.odoo_record} | Operation: {self.operation} | UUID:"
                f" {self.uuid} | Values: {values} | Error: {exception}"
            )
            stringified_values = msg

        return self.env["graphql.queue"].create(
            {
                "name": self.get_queue_item_name(),
                "operation": self.operation,
                "company_id": self.env.company.id,
                "odoo_class": self.odoo_class,
                "publish_time": self.publish_time,
                "record_uuid": self.uuid,
                "transaction_id": self.transaction_id,
                "message_source": self.message_source,
                "values": stringified_values,
            }
        )

    def get_queue_item_name(self):
        """
        Get the name from the values we want to set
        """
        default_name = f"{self.publish_time,} / {self.transaction_id}"
        return self.get_decoded_field_value(field_name="name") or default_name

    def add_post_graphql_create_parameter(self, field, value):
        """
        Adds key value pair to kwargs to be passed to _post_graphql_create_actions
        """
        self.post_graphql_create_kwargs[field] = value

    def add_post_graphql_update_parameter(self, field, value):
        """
        Adds key value pair to kwargs to be passed to _post_graphql_update_actions
        """
        self.post_graphql_update_kwargs[field] = value
