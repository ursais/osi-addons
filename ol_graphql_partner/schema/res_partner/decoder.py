# Import Python Libs

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.decoder import BaseDecoder


class PartnerDecoder(BaseDecoder):

    def decode_type(self, message_field, message_value):
        """
        Make sure we received a valid type
        """
        partner_type = message_value.lower()
        valid_types = list(
            dict(
                self.odoo_record.fields_get().get(message_field).get("selection")
            ).keys()
        )
        if partner_type not in valid_types:
            self.raise_graphql_error(
                "Rejecting message for partner as the `type` in the message is invalid. | Message `type`"
                f" value: `{partner_type}` | Valid types: {', '.join(valid_types)}"
            )

        values = {message_field: partner_type}
        return self.add_decoded_data(values=values)
