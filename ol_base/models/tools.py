# Import Python libs
import base64
from io import StringIO
from odoo.exceptions import UserError

# Import Odoo libs
from odoo import fields, tools, models


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
