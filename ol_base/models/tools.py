# Import Python libs
import base64
from io import StringIO
from odoo.exceptions import UserError
import logging
import datetime as dt

# Import Odoo libs
from odoo import fields, tools, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


def odoo_binary_to_csv_data(
    odoo_binary,
    string_io=True,
    carriage_return_to_new_line=False,
):
    """
    Convert data received for `fields.Binary` to
    normal csv data than can be iterated via `readlines` etc.
    """
    # Decode the base-64 encoded byte file
    csv_data_decoded = base64.b64decode(odoo_binary)

    # Attempt to convert resulting byte-object to a string
    try:
        csv_data_str = csv_data_decoded.decode()  # utf-8 encoding is default
    except UnicodeDecodeError:
        try:
            # It's possible the file is encoded in latin-1 (found in testing)
            csv_data_str = csv_data_decoded.decode("latin-1")
        except UnicodeDecodeError as err:
            raise UserError(
                f"CSV File could not be decoded. Contact IT.\nError:\n{err}"
            )

    if carriage_return_to_new_line:
        # clear out weird Windows line endings
        csv_data_str = csv_data_str.replace("\r", "\n")

    return StringIO(csv_data_str) if string_io else csv_data_str


def stringify_nested_odoo_objects(data):
    """
    Recursively iterates over all values of an iterable variable and replaces any instances of
    Odoo13 records with a string (the name of the class and IDs of the record).
    """

    try:
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = stringify_nested_odoo_objects(value)
        elif isinstance(data, list):
            data = [stringify_nested_odoo_objects(item) for item in data]
        elif isinstance(data, set):
            data = {stringify_nested_odoo_objects(item) for item in data}
        elif isinstance(data, dt.date):
            data = data.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif isinstance(data, dt.datetime):
            data = data.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        elif is_named_tuple_instance(data):
            # This is a `namedtuple`, convert it to a dictionary and try again
            data = stringify_nested_odoo_objects(dict(data._asdict()))
        elif isinstance(data, tuple):
            data = tuple(stringify_nested_odoo_objects(item) for item in data)
        elif isinstance(data, models.Model):
            # We want to represent the odoo recordset as a string
            id_string = (
                "" if len(data.ids) == 0 else f"{','.join([str(x) for x in data.ids])}"
            )
            data = f"{data._name}({id_string})"
    except Exception as error:
        _logger.exception(
            f'Error stringifying nested Odoo object. | Type: {type(data)} | Data: {data} | Error: {error}"'
        )
    return data


def is_named_tuple_instance(value):
    """
    Checks if the given variable is an instance of a named tuple

    Source:
    https://stackoverflow.com/a/2166841
    Calling the function collections.namedtuple gives you a new type
    that's a subclass of tuple (and no other classes)
    with a member named _fields that's a tuple
    whose items are all strings.
    """
    value_type = type(value)
    value_type_bases = value_type.__bases__
    if len(value_type_bases) != 1 or value_type_bases[0] != tuple:
        return False
    fields_attribute = getattr(value_type, "_fields", None)
    if not isinstance(fields_attribute, tuple):
        return False
    return all(isinstance(n, str) for n in fields_attribute)


def install_uuid_postgres_extension(env):
    # Check if the UUID extension is installed or not
    query = """SELECT extname FROM pg_extension;"""
    env.cr.execute(query)
    available_extensions = [x[0] for x in env.cr.fetchall()]
    _logger.info(f"Available PostgreSQL extensions: {available_extensions}")
    if "uuid-ossp" not in available_extensions:
        # Enable the UUID extension if it's not available on the database
        query = """CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""
        env.cr.execute(query)


def operator_value_to_raw_sql(field_name, operator, value):
    """
    Helper for computed field's search functionality.
    Returns a raw SQL partial that can be used in a WHERE statement
    """

    if value is False:
        converter = {
            "=": f"{field_name} IS NULL",
            "!=": f"{field_name} IS NOT NULL",
        }
    else:
        converter = {
            ">": f"{field_name} > '{value}'",
            ">=": f"{field_name} >= '{value}'",
            "<": f"{field_name} < '{value}'",
            "<=": f"{field_name} <= '{value}'",
            "=": f"{field_name} = '{value}'",
            "!=": f"{field_name} != '{value}'",
        }
    return converter[operator]


def chunk_recordset(records, chunk_size=False):
    """
    Create n-sized chunks from the recordset
    """
    chunked_records = []
    for i in range(0, len(records), chunk_size):
        chunked_records.append(records[i : i + chunk_size])
    return chunked_records
