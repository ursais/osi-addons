# Import Python Libs

# Import Odoo Libs
from odoo.addons.ol_graphql.schema.decoder import BaseDecoder


class ProductTemplateDecoder(BaseDecoder):

    def decode_image(self, _, message_value):
        """
        - Decode the image
        - Add a follow up function to update related Tier 1/2 system images if necessary
        """

        if (
            self.odoo_record
            and self.odoo_record.has_configurable_attributes
            and self.odoo_record.system_tier != "normal"
        ):
            # This is a Tier 1 or Tier 2 system that has a parent portfolio system
            # there is no need to set the image as we always use the related parent portfolio system's image
            # check `ol_graphql_product/models/fields.py new_read()`
            return

        values = {"image_1920": message_value}
        self.add_decoded_data(values=values)
