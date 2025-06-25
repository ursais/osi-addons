# Import Python Libs

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.logger import GraphQLLogger


class BaseDecoder(GraphQLLogger):

    def decode_onlogic_company(self, message_field, message_value):
        """
        Interface to decode one company using the decode_onlogic_companies logic
        """
        # Messages can come in without an onlogic company set, in which case message_value will be None
        message_value = [message_value] if message_value else message_value
        return self.decode_onlogic_companies(message_field, message_value)

    def decode_onlogic_companies(self, message_field, message_value):
        """
        Find the matching company and return it
        """

        if not message_value:
            values = {"company_id": False}
            return self.add_decoded_data(values=values)

        if not isinstance(message_value, list):
            self.raise_graphql_error(
                f"Invalid value for field: `{message_field}`. Should be a list!"
            )

        # Get the ENUM value that matches the `res.company` short_name
        short_names = [company_enum.value for company_enum in message_value]

        # try to find the related companies
        company_ids = self.env["res.company"].search(
            [("short_name", "in", short_names)]
        )

        if len(company_ids) > 1:
            self.log_exception_message(
                f"MultiCompany not implemented yet. Received: {message_value}"
            )
            # Set the company to be false
            values = {"company_id": False}
            return self.add_decoded_data(values=values)

        if not company_ids:
            values = {"company_id": False}
            return self.add_decoded_data(values=values)

        company_id = company_ids
        values = {"company_id": company_id.id}
        return self.add_decoded_data(values=values)

    def decode_company_dependent_field_value(
        self,
        message_field,
        message_value,
        odoo_field_name=False,
        additional_decode_functions=False,
    ):
        """
        Decode a company dependent Odoo field.

        Args:
            message_field (string): Name of the field we received via the incoming GQL message
            message_value (any): Value of the field we received via the incoming GQL message
            odoo_record (odoo model): The Odoo record this message was for
            additional_decode_functions (string[], optional): List of functions that should be will be triggered in order to further decode / process the incoming field. Defaults to False.

        Returns:
            Dictionary: Decoded values for the given company. In reality the returned values are not as important as the save_value
        """

        if not message_value:
            # If we didn't receive any value, create one from scratch that mimics a message with False `values`
            onlogic_companies = self.env["res.company"].get_all()
            message_value = [
                {"onlogic_company": c.short_name.upper(), "value": False}
                for c in onlogic_companies
            ]

        # Extract the OnLogic Companies (stores) that are set for the given field
        field_companies = [
            company_value["onlogic_company"].lower() for company_value in message_value
        ]

        # Get the company/companies that are allowed for the record based on the incoming message
        record_companies = self.get_message_companies()

        if record_companies:
            # If the record it self is only enabled in certain companies, filter the field companies
            # We have to do this as it is theoretically possible that while a record is only enabled in one company
            # the field it self as marked as to have values in multiple companies.
            # Example: PIM which has no concept of Odoo's company/region rules.
            field_companies = [
                c for c in field_companies if c in record_companies.mapped("short_name")
            ]

        # Find the related OnLogic Companies (stores)
        onlogic_companies = self.env["res.company"].search(
            [("short_name", "in", field_companies)]
        )

        for company in onlogic_companies:
            # Extract the values for each OnLogic Company

            # Find the company related value
            company_related_value = [
                company_value.get("value", False)
                for company_value in message_value
                if company_value.get("onlogic_company") == company.short_name.upper()
            ]
            # If there is one use it or default to False
            value = (
                company_related_value[0] or False if company_related_value else False
            )

            # We should allow further decoding of the value if necessary
            if additional_decode_functions:
                for additional_decode_function in additional_decode_functions:
                    if hasattr(self, additional_decode_function):
                        value = getattr(self, additional_decode_function)(
                            message_field, value
                        )

            # Store the calculated company_dependent_data
            values = {odoo_field_name or message_field: value}

            # If the values we want to create/update are for a different company
            # than the one we use for the main message mutation, we need to make sure we handle that
            if company != self.env.company:
                # If this is a `create` mutation but the companies don't match we need to add these
                #   company dependent values to the `update` block
                # If this is an `update` mutation but the companies don't match we still need to add the
                # company dependent values to the `update` block
                self.add_decoded_data(
                    operation="update", values=values, company=company
                )
            else:
                # if the companies are matching we can omit the specific `operation` and use the mutations default
                self.add_decoded_data(values=values, company=company)
