# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging
from datetime import datetime, timedelta

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class EdiSupportedDoc(models.Model):
    _name = "edi.supported.doc"
    _description = "EDI Supported Document"

    edi_provider_id = fields.Many2one("edi.provider", string="EDI Provider")
    name = fields.Char(string="Name")
    edi_model_id = fields.Many2one("ir.model", string="Model")
    edi_sup_doc_struct_ids = fields.One2many(
        "edi.supported.doc.structure", "edi_doc_id", string="EDI Document Structure"
    )
    code = fields.Selection(
        [
            ("810", "810"),
            ("850", "850"),
            ("856", "856"),
        ],
        string="Code",
    )

    active = fields.Boolean(default=True, help="Set active to false.")

    confirm_record = fields.Boolean(default=False, help="Auto Confirm Record.")

    @api.model
    def _parse_raw_message_lookup(self, field, struct_id, result):
        """
        Lookup a related record id
        - field: a string with the mapped field name
        - struct_id: the Document Structure Line being processed
        - result: a dict with the current parse result. Not modified.

        Returns the id for the related record.
        May raise a Validation error if an lookup id is required but was not found.
        """
        if not (struct_id.lookup_model and struct_id.lookup_domain):
            return

        domain = struct_id.lookup_domain % result
        model = self.env.get(struct_id.lookup_model.model)

        # Convert from string domain to list domain
        domain_list = ast.literal_eval(domain)
        lookup_id = model.search(domain_list, limit=1)
        #         lookup_id = model.search(domain, limit=1)
        if not lookup_id:
            if not struct_id.automatic_create:
                raise exceptions.ValidationError(
                    _("Lookup failed for element {}".format(struct_id.line_prefix))
                )
            else:
                # Automatically create related record
                # Example: result = {'partner_id.name': 'Acme', 'partner_id.ref': 'AM'}
                # -> create Partner using vals = {name': 'Acme', 'ref': 'AM'}
                vals = {k.split(".")[-1]: v for k, v in result.items()}
                lookup_id = model.create(vals)
        return lookup_id

    def get_parse_new_message_by_line(
        self,
        line,
        col_separator,
        result_line,
        edi_supported_doc_id,
        result,
        shipping_dict,
    ):
        cols = line.split(col_separator)
        prefix = cols[0] if not cols[1] else cols[0] + "*" + cols[1]
        # Get all Doc Structure definition that match the current line
        prefix = cols[0] + "*" + cols[1]
        matched_struct_ids = edi_supported_doc_id.edi_sup_doc_struct_ids.filtered(
            lambda s: s.line_prefix == prefix
        )
        # Support case where line is a child of a parent section
        if not matched_struct_ids:
            prefix = cols[0]
            matched_struct_ids = edi_supported_doc_id.edi_sup_doc_struct_ids.filtered(
                lambda s: s.line_prefix == prefix
            )

        for struct_id in matched_struct_ids:
            if struct_id.action == "newline":
                # Make buyer edi_code available in lines, to use in
                # domain expressions
                result_line = {
                    "partner_id.edi_code": result.get("partner_id.edi_code"),
                    "partner_id.id": result.get("partner_id.id"),
                }
                field = struct_id.mapped_field
                lines = result.setdefault(field, [])
                lines.append(result_line)
            else:
                # Update shipping values into separate dict
                if cols[0] + "*" + cols[1] == "N1*ST":
                    if struct_id.mapped_field not in shipping_dict:
                        shipping_dict.update(
                            {struct_id.mapped_field: cols[struct_id.column]}
                        )
                if cols[0] == "N3":
                    if struct_id.mapped_field not in shipping_dict:
                        shipping_dict.update(
                            {struct_id.mapped_field: cols[struct_id.column]}
                        )
                if cols[0] == "N4":
                    if struct_id.mapped_field not in shipping_dict:
                        shipping_dict.update(
                            {struct_id.mapped_field: cols[struct_id.column]}
                        )

                if struct_id.mapped_field not in shipping_dict:
                    field = struct_id.mapped_field
                    value = cols[struct_id.column]

                    # Make value as datetime format for date_order
                    # and commitment_date to fetch right datetime
                    if (
                        struct_id.mapped_field == "date_order"
                        or struct_id.mapped_field == "commitment_date"
                    ):
                        if value:
                            if len(value) == 6:
                                dt_str = value[:2] + "-" + value[2:4] + "-" + value[4:6]
                                dt = datetime.strptime(dt_str, "%y-%m-%d")
                            else:
                                dt_str = value[:4] + "-" + value[4:6] + "-" + value[6:8]
                                dt = datetime.strptime(dt_str, "%Y-%m-%d")
                            value = (dt + timedelta(hours=8)).strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                    # dt_str = value[:4]+'-'+value[4:6]+'-'+value[6:8]+' 08:00:00'
                    # value=datetime.strptime(dt_str, '%y-%m-%d %H:%M:%S')
                    target = result_line if struct_id.action == "line" else result
                    if field in target:
                        target[field] = value
                    else:
                        target.update({field: value})

                    # Check for lookup model and domain
                    if struct_id.lookup_model and struct_id.lookup_domain:
                        lookup_id = self._parse_raw_message_lookup(
                            field, struct_id, target
                        )
                        # Example: {'parent_id.ref': 'XX'} is used for the lookup,
                        # and the resulting id is written as {'parent_id.id': 999}
                        lookup_field_parent = field.split(".")[:-1]
                        lookup_field = ".".join(lookup_field_parent + ["id"])
                        target[lookup_field] = lookup_id

    @api.model
    def parse_raw_message(self, raw_message, edi_supported_doc_id):
        """
        Parses a text raw message into a dict,
        to later be converted into a proper "create" values dict.
        - raw_message: the EDI message text to parse.
        - edi_supported_doc_id:

        Returns a dict with the valies parsed from the message.
        May raise an exceptions, if the parsing ids not completed correctly.
        """
        # TODO: try .. except removed -> should be handled by the caller,
        # in the Message Queue Model.
        # TODO: replace the raw_message, edi_supported_doc_id arguments
        # with just one, "message_queue_id"
        # raw_message = .raw_message
        # edi_supported_doc_id= message_queue_id.edi_supported_doc_id
        if not (raw_message and edi_supported_doc_id):
            return

        line_separator = "\n"
        col_separator = "*"
        result = {}
        result_line = {}
        shipping_dict = {}

        # split raw message into lines
        lines = raw_message.split(line_separator)

        for line in lines:
            if line:
                self.get_parse_new_message_by_line(
                    line,
                    col_separator,
                    result_line,
                    edi_supported_doc_id,
                    result,
                    shipping_dict,
                )

        # Check if partner is drop to ship
        if "partner_id.id" in result:
            partner_ship = (
                result.get("partner_id.id")
                and result.get("partner_id.id").is_drop_third_party
            )
            if partner_ship:
                if "country_id.code" in shipping_dict:
                    country = self.env["res.country"].search(
                        [("code", "=", shipping_dict.get("country_id.code"))], limit=1
                    )
                    shipping_dict["country_id"] = country
                if "state_id.code" in shipping_dict:
                    state = self.env["res.country.state"].search(
                        [
                            ("code", "=", shipping_dict.get("state_id.code")),
                            ("country_id", "=", shipping_dict.get("country_id").name),
                        ],
                        limit=1,
                    )
                    # Update dict with state and country id
                    shipping_dict["state_id"] = state.id
                    shipping_dict["country_id"] = shipping_dict.get("country_id").id

                result.update(shipping_dict)

        return result

    def prepare_document(self, parsed_data):
        try:
            vals = {}
            for key, val in parsed_data.items():
                # key/value in the input dict, containing a list value
                if isinstance(val, list):
                    line_list = [(0, 0, self.prepare_document(x)) for x in val]
                    vals[key] = line_list
                # key/value in the input dict, where the key contains a dot
                elif "." in key:
                    # If only a single dot and ends with ".id"
                    if key.split(".")[1] == "id" and val:
                        vals[key[:-3]] = val.id
                    # else: ignored
                else:
                    vals[key] = val

        except Exception as e:
            _logger.error(
                "Exception while while prepare document: %s.\n Original Traceback:\n%s",
                e,
                Exception,
            )

        return vals

    def process_document(self, parsed_data):
        result = {}
        Model = self.env[self.edi_model_id.model]
        vals = Model.default_get(Model._fields.keys())
        # Get values for create method
        vals.update(self.prepare_document(parsed_data))
        # Based on vals create record
        result = Model.create(vals)
        # For model specific validations
        self.validate_document(result)

        return result

    def validate_document(self, record):
        if self.edi_model_id.model == "sale.order":
            # Update Fiscal Position
            record.fiscal_position_id = (
                record.partner_id.property_account_position_id
                and record.partner_id.property_account_position_id.id
                or False
            )
            # Update Warehouse
            if record.partner_id.warehouse_id:
                record.warehouse_id = record.partner_id.warehouse_id.id
            # update routes
            if record.partner_id.route_id:
                route_id = record.partner_id.route_id.id

                for line in record.order_line:
                    line.route_id = route_id
        return


class EdiSupportedDocStructure(models.Model):
    _name = "edi.supported.doc.structure"
    _description = "EDI Supported Document Structure"
    _order = "sequence"

    sequence = fields.Integer(string="Sequence", default=10)
    line_prefix = fields.Char(string="Line Prefix")
    action = fields.Selection(
        [
            ("head", "Header Field"),
            ("newline", "New Line"),
            ("line", "Line Field"),
            ("header-hl", "Header HL-S"),
            ("order-hl", "Order HL-O"),
            ("pack-hl", "Pack HL-P"),
            ("item-hl", "Item HL-1"),
        ],
        string="Action",
        default="head",
    )
    column = fields.Integer(string="Column")
    mapped_field = fields.Text(string="Mapped Field")
    lookup_model = fields.Many2one("ir.model", string="Lookup Model")
    lookup_domain = fields.Text(string="Lookup Domain")
    automatic_create = fields.Boolean(string="Automatically Create?")
    edi_doc_id = fields.Many2one("edi.supported.doc", string="EDI Supported Document")
