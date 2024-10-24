from odoo import fields

OLD_CONVERT_TO_READ = fields.Many2one.convert_to_read


def new_convert_to_read(self, value, record, use_name_get=True):
    """
    @ol_upgrade:    Full override of the core function, to include the UUID to the basic read response for Many2one fields.
                    This will help with GraphQL data extracts, debugging, and development.
                    As the UUID field is indexed this should not add a huge overhead in loading times.

    Example: Until now if you did sale_order.read(["partner_id"]) you got the following result:
    [{  'id': 288387,
        'partner_id': (1943647,
                        'IDS,, Brandon Holguin'),
        'uuid': '4fc1f0ed-82ed-4801-9b0b-665a1957f59c'}]
    Now you will get:
    [{  'id': 288387,
        'partner_id': (1943647,
                        'IDS,, Brandon Holguin',
                        '024519f4-8248-4e40-a978-51b5c676dcc7'),
        'uuid': '4fc1f0ed-82ed-4801-9b0b-665a1957f59c'}]

    Notice the new '024519f4-8248-4e40-a978-51b5c676dcc7' part in the `partner_id` field.
    This new 3rd element in the tuple will be the UUID.
    """
    if use_name_get and value:
        # evaluate name_get() as superuser, because the visibility of a
        # many2one field value (id and name) depends on the current record's
        # access rights, and not the value's access rights.
        try:
            # performance: value.sudo() prefetches the same records as value
            if hasattr(value, "_uses_uuid_mixin") and value._uses_uuid_mixin:
                # @ol_upgrade: If the record uses the UUID mixin, we should always add the uuid field to the results
                return (value.id, value.sudo().display_name, value.sudo().uuid)
            return (value.id, value.sudo().display_name)
        except MissingError:
            # Should not happen, unless the foreign key is missing.
            return False
    else:
        return value.id


# Monkey patch the convert_to_read method of the Many2one class
fields.Many2one.convert_to_read = new_convert_to_read

# Imported here to avoid dependency cycle issues
from odoo.exceptions import MissingError
