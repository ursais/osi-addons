# Import Python libs
import json
import logging
import base64
import datetime as dt
from io import StringIO
from datetime import timedelta
from dateutil.rrule import rrule, WEEKLY, MO, TU, WE, TH, FR

# Import Odoo libs
from odoo.exceptions import UserError, ValidationError
from odoo import fields, tools, models

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

_logger = logging.getLogger(__name__)


def odoo_binary_to_csv_data(odoo_binary, string_io=True, carriage_return_to_new_line=False):
    """
    Convert data received for `fields.Binary` to normal csv data than can be iterated via `readlines` etc.
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
            raise UserError(f"CSV File could not be decoded. Contact IT.\nError:\n{err}")

    if carriage_return_to_new_line:
        # clear out weird Windows line endings
        csv_data_str = csv_data_str.replace("\r", "\n")

    return StringIO(csv_data_str) if string_io else csv_data_str


def option_to_val(obj, field, option):  # pylint: disable=inconsistent-return-statements
    """
    Helper function to get a selection label from its database key
    """
    try:
        val = dict(obj.fields_get().get(field).get("selection")).get(option)
        return val
    except:
        return


def localize_date(record, date, output="date"):
    """
    Localize time from database
    """
    try:
        date_object = dt.datetime.strptime(
            date, tools.DEFAULT_SERVER_DATE_FORMAT + " " + tools.DEFAULT_SERVER_TIME_FORMAT
        )
        date_object = fields.Datetime.context_timestamp(record, date_object)
    except ValueError:
        date_object = dt.datetime.strptime(date, tools.DEFAULT_SERVER_DATE_FORMAT)

    if output == "string":
        return dt.datetime.strftime(date_object, tools.DEFAULT_SERVER_DATE_FORMAT)
    return date_object


def format_date(record, date, string=None):
    """
    Format time from database
    """
    if not string:
        string = "{dt.month}/{dt.day}/{dt.year}"

    date_object = localize_date(record, date)
    date_string = string.format(dt=date_object)

    return date_string


def string_list_to_list(string_value, value_type=int):
    """
    Convert a string representation of a list to a list.
    @param string_value: "[152,54]
    @param value_type: The type of the list values. ex. int, string etc.
    @return:
    """

    if not string_value:
        return False

    ids_str = string_value[1:-1]
    if ids_str:
        # Convert the "string" to a list of ids. (i.e. [2] instead of '[2]')
        list_value = [value_type(i) for i in ids_str.split(",")]
    else:
        # user_ids can be '[]' so convert to an actual list
        list_value = []

    return list_value


def filter_values_for_object(odoo_object, values, fields_to_remove=False):
    """
    Filter the values to only contain ones that the given odoo class accepts
    """
    filtered_values = {}
    for field_name, value in values.items():
        if not hasattr(odoo_object, field_name):
            # We only care about values for fields that also exists on the given Odoo class
            continue
        if fields_to_remove and field_name in fields_to_remove:
            # If this field was called out to be filtered skip it
            continue
        filtered_values[field_name] = value
    return filtered_values


def recompute_fields(records, field_names):
    """
    Recalculate the values of the given fields for the given records
    Idea from: https://stackoverflow.com/a/60152708
    """
    model = records.env[records._name]
    ids = [x.get("id") for x in model.search_read([("id", "in", records.ids)], ["id"])]
    for field_name in field_names:
        if model._fields.get(field_name, False):
            # If the field is defined on the odoo object
            records.env.all.tocompute[model._fields[field_name]].update(ids)
    model.recompute()


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
            id_string = "" if len(data.ids) == 0 else f"{','.join([str(x) for x in data.ids])}"
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


def chunk_recordset(records, chunk_size=False):
    """
    Create n-sized chunks from the recordset
    """
    chunked_records = []
    for i in range(0, len(records), chunk_size):
        chunked_records.append(records[i : i + chunk_size])
    return chunked_records


def is_string_valid_json(json_string, allow_empty=False):
    if allow_empty and (not json_string or json_string == ""):
        return True
    try:
        json.loads(json_string)
        return True
    except Exception:
        return False


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
            "<=": f"{field_name} >= '{value}'",
            "=": f"{field_name} = '{value}'",
            "!=": f"{field_name} != '{value}'",
        }
    return converter[operator]


def get_weekdays(start_date, end_date):
    """
    Return the number of weekdays between the given dates (inclusive)
    """
    # rrule generates dates based on a rule, in this case weekly dates with only workdays
    # between 2 dates.  The count of weekdays is the number of work days in the the given range

    if not start_date or not end_date:
        return False

    # Convert string dates if necessary
    if isinstance(start_date, str):
        start_date = fields.Date.from_string(start_date)

    if isinstance(end_date, str):
        end_date = fields.Date.from_string(end_date)

    rule = rrule(WEEKLY, byweekday=(MO, TU, WE, TH, FR), dtstart=start_date, until=end_date)
    return rule.count()


def is_weekday(date):
    """
    Check if the given date is a weekday
    :param date:
    :return:
    """

    if not date:
        return False

    # Convert string dates if necessary
    if isinstance(date, str):
        date = fields.Date.from_string(date)

    rule = rrule(WEEKLY, byweekday=(MO, TU, WE, TH, FR), dtstart=date, until=date)

    if rule.count() <= 0:
        return False

    return True


def is_workday(date):
    """
    Check if the given date is not a weekend or holiday
    """

    if not date:
        return False

    # Convert string dates if necessary
    if isinstance(date, str):
        date = fields.Date.from_string(date)

    if not is_weekday(date):
        return False

    return True


def get_closest_next_workday_by_delta(origin_date, delta):
    """
    Get next workday from N days from given from_date
    """

    # Make sure we received correct attributes
    assert isinstance(origin_date, dt.date)
    assert isinstance(delta, int)

    work_days_passed = 0
    new_date = origin_date

    # We move count up one day at a time from the given origin_date
    # and stop if enough workdays passed
    while work_days_passed < delta:
        new_date = new_date + timedelta(days=1)
        if is_weekday(new_date):
            work_days_passed += 1

    return new_date