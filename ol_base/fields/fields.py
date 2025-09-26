# Import Python libs

# Import Odoo libs
from odoo import fields, tools


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


class NullableInteger(fields.Integer):
    """
    Extend core Integer field

    Patch methods to preserve when a passed value is None, rather than converting it to 0.
    """

    type = "nullable_integer"

    def convert_to_column(self, value, record, values=None, validate=True):
        if value is False or value is None:
            return None
        return super().convert_to_column(value, record, values, validate)

    def convert_to_cache(self, value, record, validate=True):
        if value is False or value is None:
            return None
        return super().convert_to_cache(value, record, validate)

    def convert_to_record(self, value, record):
        if value is False or value is None:
            return None
        return super().convert_to_record(value, record)

    def convert_to_read(self, value, record, use_display_name=True):
        if value is False or value is None:
            return None
        return super().convert_to_read(value, record, use_display_name)


class NullableFloat(fields.Float):
    """
    Extend core Float field

    Patch methods to preserve when a passed value is None, rather than converting it to 0.
    """

    type = "nullable_float"

    def convert_to_column(self, value, record, values=None, validate=True):
        if value is False or value is None:
            return None
        return super().convert_to_column(value, record, values, validate)

    def convert_to_cache(self, value, record, validate=True):
        if value is False or value is None:
            return None
        return super().convert_to_cache(value, record, validate)

    def convert_to_record(self, value, record):
        if value is False or value is None:
            return None
        return super().convert_to_record(value, record)
