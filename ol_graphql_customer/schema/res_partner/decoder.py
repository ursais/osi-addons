# Import Python Libs

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.decoder import BaseDecoder


class CustomerDecoder(BaseDecoder):

    def decode_type(self, message_field, message_value):
        """
        Make sure we received a valid type
        """
        customer_type = message_value.lower()
        valid_types = list(
            dict(
                self.odoo_record.fields_get().get(message_field).get("selection")
            ).keys()
        )
        if customer_type not in valid_types:
            self.raise_graphql_error(
                "Rejecting message for customer as the `type` in the message is invalid. | Message `type`"
                f" value: `{customer_type}` | Valid types: {', '.join(valid_types)}"
            )

        values = {message_field: customer_type}
        return self.add_decoded_data(values=values)
