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
        company_ids = (
            self.env["res.company"].sudo().search([("short_name", "in", short_names)])
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
