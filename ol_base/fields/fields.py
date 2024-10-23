# Import Python libs

# Import Odoo libs
from odoo import fields


class Uuid(fields.Field):
    """
    A field for UUID data
    """

    # Odoo UI will show this as text
    type = "text"
    # postgres column type: uuid
    column_type = ("uuid", "uuid")


class JsonField(fields.Field):
    """
    A field for JSON data
    """

    # Odoo UI will show this with a custom JSON widget
    type = "json"
    # postgres column type: json
    column_type = ("json", "json")


class Timestamp(fields.Field):
    """
    A field for Timestamp data
    """

    # Odoo UI will show this as text
    type = "text"
    # postgres column type: timestamp
    column_type = ("timestamp", "timestamp")
