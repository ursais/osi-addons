# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging
import os
import shutil
from datetime import datetime, timedelta

from pyparsing import commaSeparatedList
from unidecode import unidecode

from odoo import api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class EdiMessageQueue(models.Model):
    _name = "edi.message.queue"
    _description = "EDI Message Item"

    direction = fields.Selection(
        [
            ("in", "Inbound"),
            ("out", "Outbound"),
        ],
        string="Direction",
    )
    raw_message = fields.Text()
    parsed_data = fields.Text()
    edi_provider_id = fields.Many2one("edi.provider", string="EDI Provider")
    edi_supported_doc_id = fields.Many2one(
        "edi.supported.doc", string="EDI Document Type"
    )
    edi_model_id = fields.Many2one(
        related="edi_supported_doc_id.edi_model_id", string="Model"
    )
    partner_id = fields.Many2one("res.partner", string="Related Partner")
    state = fields.Selection(
        [
            ("new", "New"),
            ("parsed", "Parsed"),
            ("processed", "Processed"),
            ("done", "Done"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        tracking=True,
    )
    rec_created = fields.Integer("Record Created")
    file_name = fields.Char("File Name")
    received_date = fields.Datetime("EDI Received Date")
    log_message = fields.Text()

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == "tracking" or super()._valid_field_parameter(field, name)

    def checkin_inbound_message(self):
        # Get company and check EDI Providers used
        company_id = self.env.user.company_id

        if company_id and company_id.edi_provider_id:
            # Verify path for inbound and Archive
            in_path = archive_path = ""

            if company_id.edi_provider_id.new_inbound_messages:
                in_path = company_id.edi_provider_id.new_inbound_messages
                # Check path if not valid
                if in_path:
                    if not os.path.exists(in_path):
                        # Invalid path
                        _logger.debug(
                            "Invalid Path for New Inbound Message: %s", in_path
                        )
                else:
                    _logger.debug(
                        "Path not defined for New Inbound Message for provider %s",
                        company_id.edi_provider_id.name,
                    )

            if company_id.edi_provider_id.archived_inbound_messages:
                archive_path = company_id.edi_provider_id.archived_inbound_messages
                # Check path if not valid
                if archive_path:
                    if not os.path.exists(archive_path):
                        # Invalid path
                        _logger.debug(
                            "Invalid Path for Archived Inbound Message: %s",
                            archive_path,
                        )
                else:
                    _logger.debug(
                        "Path not defined for Archived Inbound Message for provider %s",
                        company_id.edi_provider_id.name,
                    )

            # Get all files from Inbound Location
            inbound_files = os.listdir(in_path)
            if inbound_files:
                partner_obj = self.env["res.partner"]
                for file in inbound_files:
                    try:
                        # Copy file data in raw message
                        src_file_path = os.path.join(in_path, file)
                        str_msg = open(src_file_path, "r").read()

                        # Get Type of Document from raw_message
                        # split raw message into lines
                        lines = str_msg.split("\n")
                        document_code = partner_code = ""
                        doc_id = False
                        rec_dt = False

                        for line in lines:
                            cols = line.split("*")
                            if line and cols[0] == "ST":
                                document_code = cols[1]
                            if line and cols[0] == "GS" and cols[1] == "PO":
                                partner_code = cols[2]
                                dt = cols[4] + cols[5]
                                # Get datetime format from raw_message file
                                dt_str = (
                                    dt[:4]
                                    + "-"
                                    + dt[4:6]
                                    + "-"
                                    + dt[6:8]
                                    + " "
                                    + dt[8:10]
                                    + ":"
                                    + dt[10:12]
                                    + ":00"
                                )
                                rec_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

                        if document_code and partner_code:
                            # Get document type from partner
                            partner_rec = partner_obj.search(
                                [("edi_code", "=", partner_code)]
                            )
                            if partner_rec:
                                for rec in partner_rec:
                                    for doc in rec.edi_partner_document_ids:
                                        if doc.code == document_code:
                                            doc_id = doc.edi_supported_doc_id.id

                        vals = {
                            "direction": "in",
                            "edi_provider_id": company_id.edi_provider_id.id,
                            "raw_message": str_msg,
                            "edi_supported_doc_id": doc_id or False,
                            "state": "new",
                            "received_date": rec_dt,
                            "file_name": file,
                        }
                        # Create new queue for each file
                        self.create(vals)

                        # Move current file to Archived directory
                        if company_id.edi_provider_id.archive_local:
                            archive_file_path = os.path.join(archive_path, file)
                            shutil.move(src_file_path, archive_file_path)
                        else:
                            _logger.error("Local Archive not setup !!!")

                    except Exception as e:
                        _logger.error(
                            "Exception while while executing Inbound Message File: %s.\n Original Traceback:\n%s",
                            e,
                            Exception,
                        )
        return

    def _preparse_raw_message(self):
        """Initial raw message parse, to find the Document Structure to use
        Uses the self recordset.
        Sets the Partner and Document Structure in the queue items,
        or raises an exception if errors are found.
        """
        Partner = self.env["res.partner"]
        for item in self:
            # Find ST and BEG header section in the raw message
            line_grid = [
                [col for col in line.split("*")]
                for line in item.raw_message.split("\n")
            ]
            ST_lines = [line for line in line_grid if line[0] == "ST"]
            BEG_lines = [line for line in line_grid if line[0] == "BEG"]
            # list to get edi_code
            PO_lines = [
                line for line in line_grid if line[0] == "GS" and line[1] == "PO"
            ]
            if not ST_lines or not BEG_lines:
                raise exceptions.UserError(
                    "Incorrect file format. BEG and ST sections must be present."
                )
            # Find the buyer Partner record
            #             buyer_code = BEG_lines[0][3]
            buyer_code = PO_lines[0][2]
            buyer = Partner.search([("edi_code", "=", buyer_code)])
            if not buyer:
                raise exceptions.UserError(
                    "Partner for buyer code %s could not be found. "
                    "Configure the EDI Code field in the appropriate Partner."
                    % (buyer_code,)
                )
            if len(buyer) > 1:
                raise exceptions.UserError(
                    'Found too many Partners for buyer code "%s". '
                    "Ensure that there is only one Partner with this EDI Code."
                    % (buyer_code,)
                )
            self.partner_id = buyer
            # Find the Buyers Document Structure to use
            doc_code = ST_lines[0][1]
            doc_struct = buyer.edi_partner_document_ids.filtered(
                lambda s: s.code == doc_code
            )
            if not doc_struct:
                raise exceptions.UserError(
                    'Partner %s has no Document Structure defined for code "%s". '
                    "Configure the EDI Documents for this Partner."
                    % (buyer_code, doc_code)
                )
            if len(doc_struct) > 1:
                raise exceptions.UserError(
                    'Partner %s has too many Document Structures for code "%s". '
                    "Ensure that the Partner has only one Document Structure with this EDI Code."
                    % (buyer_code, doc_code)
                )
            self.edi_supported_doc_id = doc_struct.edi_supported_doc_id
        return True

    def _parse_raw_message(self):
        """
        Parse the raw message and create the corresponding Odoo document
        Uses the self recordset of queue items.
        If successful, updated the queue item with the created record id.
        If not successful raises an error.
        """
        for inbound in self:
            # if inbound.state in ['processed', 'done', 'cancelled']:
            #    raise exceptions.UserError(
            #        "Can't reprocess items in Done or Cancelled states."
            #    )
            inbound._preparse_raw_message()
            new_parse = inbound.edi_supported_doc_id.parse_raw_message(
                inbound.raw_message, inbound.edi_supported_doc_id
            )
            inbound.parsed_data = new_parse
            # Call method from EDI Document Type
            rec = inbound.edi_supported_doc_id.process_document(new_parse)
            inbound.rec_created = rec
            inbound.log_message = False
            inbound.state = "processed"
        return True

    def parse_raw_message(self):
        """
        Parse the raw message and create the corresponding Odoo document
        Uses the self recordset of queue items.
        If successful, updates the queue item with the created record id.
        If not successful, updates the state and error log accordingly.
        """
        for inbound in self:
            # if inbound.state in ['processed', 'done', 'cancelled']:
            #    raise exceptions.UserError(
            #        "Can't reprocess items in Processed, Done or Cancelled states."
            #    )
            try:
                inbound._preparse_raw_message()
                inbound._parse_raw_message()
            except Exception as e:
                inbound.state = "error"
                inbound.log_message = str(Exception) + str(e)
                _logger.error(
                    "Exception while while executing parsing raw message: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )
        return True

    def checkin_csv_inbound_message(self):
        # Get company and check EDI Providers used
        company_id = self.env.user.company_id

        if company_id and company_id.edi_provider_id:
            # Verify path for inbound and Archive
            in_path = archive_path = ""

            if company_id.edi_provider_id.new_inbound_messages:
                in_path = company_id.edi_provider_id.new_inbound_messages
                # Check path if not valid
                if in_path:
                    if not os.path.exists(in_path):
                        # Invalid path
                        _logger.debug(
                            "Invalid Path for New Inbound Message: %s", in_path
                        )
                else:
                    _logger.debug(
                        "Path not defined for New Inbound Message for provider %s",
                        company_id.edi_provider_id.name,
                    )

            if company_id.edi_provider_id.archived_inbound_messages:
                archive_path = company_id.edi_provider_id.archived_inbound_messages
                # Check path if not valid
                if archive_path:
                    if not os.path.exists(archive_path):
                        # Invalid path
                        _logger.debug(
                            "Invalid Path for Archived Inbound Message: %s",
                            archive_path,
                        )
                else:
                    _logger.debug(
                        "Path not defined for Archived Inbound Message for provider %s",
                        company_id.edi_provider_id.name,
                    )

            # Get all files from Inbound Location
            inbound_files = os.listdir(in_path)
            if inbound_files:
                partner_obj = self.env["res.partner"]
                for file in inbound_files:
                    try:
                        # Copy file data in raw message
                        src_file_path = os.path.join(in_path, file)
                        str_msg = open(src_file_path, "r").read()

                        # Get Type of Document from raw_message
                        # split raw message into lines
                        lines = str_msg.split("\n")
                        document_code = partner_code = ""
                        doc_id = False
                        rec_dt = fields.Date.today()

                        linecount = 0

                        for line in lines:

                            linecount += 1
                            cols = commaSeparatedList.parseString(
                                unidecode(line)
                            ).asList()

                            # Header Line, skip
                            if cols[0] == "TRANSACTION ID":
                                continue

                            # 2 - n lines contain header and detail
                            # read header fields from line 2, skip for the rest
                            if linecount == 2:
                                document_code = cols[0]
                                partner_code = cols[1]
                                break

                        if document_code and partner_code:
                            # Get document type from partner
                            partner_rec = partner_obj.search(
                                [("edi_code", "=", partner_code)]
                            )
                            if partner_rec:
                                for rec in partner_rec:
                                    for doc in rec.edi_partner_document_ids:
                                        if doc.code == document_code:
                                            doc_id = doc.edi_supported_doc_id.id

                        vals = {
                            "direction": "in",
                            "edi_provider_id": company_id.edi_provider_id.id,
                            "raw_message": str_msg,
                            "edi_supported_doc_id": doc_id or False,
                            "state": "new",
                            "received_date": rec_dt,
                            "file_name": file,
                            "partner_id": partner_rec.id,
                        }
                        # Create new queue for each file
                        self.create(vals)

                        # Move current file to Archived directory
                        if company_id.edi_provider_id.archive_local:
                            archive_file_path = os.path.join(archive_path, file)
                            shutil.move(src_file_path, archive_file_path)
                        else:
                            _logger.error("Local Archive not setup !!!")

                    except Exception as e:
                        _logger.error(
                            "Exception while while executing Inbound Message File: %s.\n Original Traceback:\n%s",
                            e,
                            Exception,
                        )
        return

    def create_850(self):
        """Initial raw message parse, to find the Document Structure to use
        Uses the self recordset.
        Sets the Partner and Document Structure in the queue items,
        or raises an exception if errors are found.
        """

        try:

            raw_dict = {}

            for item in self.edi_supported_doc_id.edi_sup_doc_struct_ids:
                raw_dict[item.line_prefix] = (
                    item.column,
                    item.mapped_field,
                    item.action,
                    item.lookup_model,
                    item.lookup_domain,
                    item.line_prefix,
                )

            for record in self:

                line_count = 0
                lines_list = []
                header_dict = {}
                order_dict = {}

                for line in record.raw_message.split("\n"):

                    if not line:
                        continue
                    line_dict = {}
                    line_count += 1
                    cols = commaSeparatedList.parseString(unidecode(line)).asList()

                    # column header line
                    if line_count == 1:
                        header_cols = cols
                        for idx, name in enumerate(header_cols):
                            if raw_dict.get(name, False):
                                header_dict[idx] = raw_dict[name]

                    # reading data lines
                    elif line_count == 2:

                        for idx, col in enumerate(cols):
                            item = header_dict.get(idx, False)

                            # if it is a header field
                            if item and item[2] == "head":
                                order_dict[header_dict[idx][1]] = col or False

                                # lookup
                                if item[3] and item[4]:
                                    lookup_id = self._parse_raw_csv_lookup(
                                        item[1], item[3], item[4], order_dict
                                    )
                                    order_dict[header_dict[idx][1]] = (
                                        lookup_id and lookup_id.id or False
                                    )

                            elif item and item[2] == "line":
                                line_dict[header_dict[idx][1]] = col or False

                                # lookup
                                if item[3] and item[4]:
                                    lookup_id = self._parse_raw_csv_lookup(
                                        item[1], item[3], item[4], line_dict
                                    )
                                    if lookup_id:
                                        line_dict[header_dict[idx][1]] = (
                                            lookup_id and lookup_id.id or False
                                        )

                        if line_dict:
                            if order_dict.get("partner_id", False):
                                line_dict["partner_id"] = order_dict.get("partner_id")
                            model = self.env["ir.model"].search(
                                [("model", "=", "product.product")]
                            )
                            product_id = line_dict.get("product_id", False)
                            edi_product_code = line_dict.get("edi_product_code", False)
                            barcode = line_dict.get("barcode", False)
                            partner_id = line_dict.get("partner_id", False)
                            if not partner_id:
                                raise Exception(
                                    "Partner ID is not resolved in Line Dict"
                                )
                            if not edi_product_code:
                                line_dict["edi_product_code"] = product_id
                            if not barcode:
                                line_dict["barcode"] = product_id
                            domain = "['|', '|', ('default_code', 'ilike', '%(product_id)s'), ('product_tmpl_id.barcode', '=', '%(barcode)s'), '&', ('product_tmpl_id.product_customer_code_ids.partner_id.id', '=', '%(partner_id)d'), ('product_tmpl_id.product_customer_code_ids.product_code', '=', '%(edi_product_code)s')]"
                            lookup_id = self._parse_raw_csv_lookup(
                                "product_id", model, domain, line_dict
                            )
                            line_dict["product_id"] = lookup_id.id
                            name = line_dict.get("name", False)
                            line_dict["name"] = not name and lookup_id.name or name
                            line_dict.pop("barcode")
                            line_dict.pop("partner_id")
                            line_dict.pop("product_uom")

                            if line_dict.get("product_id") is False:
                                self.log_message = "Product ID could not be found!"
                                raise Exception("Product ID could not be found!")

                            lines_list.append((0, 0, line_dict))

                    # only detail lines, skip header columns
                    else:
                        for idx, col in enumerate(cols):
                            item = header_dict.get(idx, False)

                            # if it is a header field
                            if item and item[2] == "head":
                                continue

                            elif item and item[2] == "line":
                                line_dict[header_dict[idx][1]] = col or False

                                # lookup
                                if item[3] and item[4]:
                                    lookup_id = self._parse_raw_csv_lookup(
                                        item[1], item[3], item[4], line_dict
                                    )
                                    if lookup_id:
                                        line_dict[header_dict[idx][1]] = (
                                            lookup_id and lookup_id.id
                                        )

                        if line_dict:
                            if order_dict.get("partner_id", False):
                                line_dict["partner_id"] = order_dict.get("partner_id")
                            model = self.env["ir.model"].search(
                                [("model", "=", "product.product")]
                            )
                            product_id = line_dict.get("product_id", False)
                            edi_product_code = line_dict.get("edi_product_code", False)
                            barcode = line_dict.get("barcode", False)
                            partner_id = line_dict.get("partner_id", False)
                            if not partner_id:
                                raise Exception(
                                    "Partner ID is not resolved in Line Dict"
                                )
                            if not edi_product_code:
                                line_dict["edi_product_code"] = product_id
                            if not barcode:
                                line_dict["barcode"] = product_id
                            domain = "['|', '|', ('default_code', 'ilike', '%(product_id)s'), ('product_tmpl_id.barcode', '=', '%(barcode)s'), '&', ('product_tmpl_id.product_customer_code_ids.partner_id.id', '=', '%(partner_id)d'), ('product_tmpl_id.product_customer_code_ids.product_code', '=', '%(edi_product_code)s')]"
                            lookup_id = self._parse_raw_csv_lookup(
                                "product_id", model, domain, line_dict
                            )
                            line_dict["product_id"] = lookup_id.id
                            name = line_dict.get("name", False)
                            line_dict["name"] = not name and lookup_id.name or name
                            line_dict.pop("barcode")
                            line_dict.pop("partner_id")
                            line_dict.pop("product_uom")

                            if line_dict.get("product_id") is False:
                                self.log_message = "Product ID could not be found!"
                                raise Exception("Product ID could not be found!")

                            lines_list.append((0, 0, line_dict))

                # add the lines list to the order_dict
                order_dict["order_line"] = lines_list

                self.pre_validate(order_dict)

                self.rec_created = self.env[self.edi_model_id.model].create(order_dict)

                # For model specific validations
                self.validate_document(self.env["sale.order"].browse(self.rec_created))

                # Update state
                self.state = "processed"

                # Clear logs
                self.log_message = False

        except Exception as e:
            self.state = "error"
            self.log_message = str(Exception) + str(e)
            _logger.error(
                "Exception while while executing parsing raw message: %s.\n Original Traceback:\n%s",
                e,
                Exception,
            )

        return True

    @api.model
    def pre_validate(self, order_dict):

        try:
            if order_dict:

                # Check for Partner
                if not order_dict.get("partner_id", False):
                    raise Exception("Trading Partner required for processing!")

                Partner = self.env["res.partner"]
                partner_rec = Partner.browse(order_dict.get("partner_id"))

                # Check for PO
                if not order_dict.get("client_order_ref", False):
                    raise Exception("PO # required for processing")

                # check for duplicate PO'sale
                dup_ids = (
                    self.env["sale.order"].search(
                        [
                            ("partner_id", "=", partner_rec.id),
                            (
                                "client_order_ref",
                                "=",
                                order_dict.get("client_order_ref"),
                            ),
                        ]
                    )
                    or False
                )

                if dup_ids:
                    raise Exception("Duplicate PO for the Customer. Cannot Continue!")

                # validate deivery method
                if partner_rec.property_delivery_carrier_id:
                    order_dict[
                        "carrier_id"
                    ] = partner_rec.property_delivery_carrier_id.id

                else:
                    raise Exception(
                        "Trading Partner does not have a default delivery method set!"
                    )

                # Payment terms for partner
                if partner_rec.property_payment_term_id:
                    order_dict[
                        "payment_term_id"
                    ] = partner_rec.property_payment_term_id.id

                else:
                    raise Exception("Payment Terms not set on Customer")

                # Check if partner is drop ship
                if order_dict.get("partner_id", False):
                    partner_ship = partner_rec.is_drop_third_party

                    # validate shipping address
                    if partner_ship:
                        order_dict["third_party_exists"] = True
                        if not order_dict["country_id"]:
                            order_dict["country_id"] = partner_rec.country_id.code
                        if "country_id" in order_dict:
                            country = self.env["res.country"].search(
                                [("code", "=", order_dict.get("country_id"))], limit=1
                            )
                            order_dict["country_id"] = country.id
                        if "state_id" in order_dict:
                            state = self.env["res.country.state"].search(
                                [
                                    ("code", "=", order_dict.get("state_id")),
                                    ("country_id", "=", order_dict.get("country_id")),
                                ],
                                limit=1,
                            )
                            order_dict["state_id"] = state.id
                    else:

                        model = self.env["ir.model"].search(
                            [("model", "=", "res.partner")]
                        )
                        # find shipping partner from the shipping address
                        if order_dict.get("attn", False):
                            partner_shipping_id = self._parse_raw_csv_lookup(
                                "name",
                                model,
                                "[('name', 'ilike', '%(attn)s')]",
                                {"attn": order_dict.get("attn", False)},
                            )

                        if order_dict.get("store_number", False):
                            partner_shipping_id = self._parse_raw_csv_lookup(
                                "name",
                                model,
                                "[('store_number', 'ilike', '%(store_number)s')]",
                                {"store_number": order_dict.get("store_number", False)},
                            )

                        if not partner_shipping_id:
                            partner_shipping_id = partner_rec

                        order_dict["partner_shipping_id"] = partner_shipping_id.id

                        # clear third party fields
                        order_dict.pop("attn")
                        order_dict.pop("street1")
                        order_dict.pop("street2")
                        order_dict.pop("city")
                        order_dict.pop("state_id")
                        order_dict.pop("country_id")
                        order_dict.pop("zip")
                        order_dict.pop("phone")

                    order_dict["partner_invoice_id"] = partner_rec.id

                # ship method resolution
                ship_method = order_dict.get("ship_method_id", False)
                warehouse = order_dict.get("ship_from_code", False)
                if (ship_method and not warehouse) or (not ship_method and warehouse):
                    raise Exception(
                        "Ship Method and Ship From both needs to be set for processing."
                    )

                if not warehouse:
                    warehouse_id = partner_rec.warehouse_id.id or False
                    carrier_id = False
                    route_id = False

                    result = self.env["partner.shipping.method"].get_warehouse_details(
                        partner_id=partner_rec.id, rule="fixed", mode="edi"
                    )

                    if not result[0]:
                        result = self.env[
                            "partner.shipping.method"
                        ].get_warehouse_details(
                            partner_id=partner_rec.id,
                            rule="address",
                            zipcode=order_dict["third_party_exists"]
                            and order_dict["zip"]
                            or partner_rec.zip,
                            mode="edi",
                        )

                    if result[0]:
                        order_dict["warehouse_id"] = result[1]
                        order_dict["route_id"] = result[2]
                        order_dict["carrier_id"] = result[3]
                        if result[4]:
                            order_dict["ups_carrier_account"] = result[4][0]
                            order_dict["fedex_bill_my_account"] = result[4][1]
                            order_dict["fedex_carrier_account_retail"] = result[4][2]
                            order_dict["fedex_carrier_account_dropship"] = result[4][3]

                if ship_method and warehouse:
                    warehouse_id = self.env["stock.warehouse"].search(
                        [("ship_from_code", "=", warehouse)]
                    )
                    model = self.env["ir.model"].search(
                        [("model", "=", "partner.shipping.method")]
                    )
                    result = self.env["partner.shipping.method"].get_warehouse_details(
                        partner_id=partner_rec.id,
                        warehouse=warehouse_id.id,
                        rule="edi",
                        code=ship_method,
                    )
                    order_dict["ship_method_id"] = result[0]
                    order_dict["warehouse_id"] = result[1]
                    order_dict["route_id"] = result[2]
                    order_dict["carrier_id"] = result[3]

                    # validate for billing account on the delivery method
                    if partner_rec.fedex_bill_my_account:
                        if result[4][1]:
                            order_dict[
                                "fedex_bill_my_account"
                            ] = partner_rec.fedex_bill_my_account
                            order_dict["fedex_carrier_account_retail"] = result[4][2]
                            order_dict["fedex_carrier_account_dropship"] = result[4][3]
                        else:
                            raise Exception(
                                "FedEx Carrier Account needed to bill to Customer for shipping!"
                            )
                    else:
                        if result[4][0]:
                            order_dict["ups_carrier_account"] = result[4][0]

                        else:
                            raise Exception(
                                "UPS Carrier Account needed to bill to Customer for shipping!"
                            )

                # Make value as datetime format for date_order
                # and commitment_date to fetch right datetime
                if order_dict.get("date_order", False):
                    value = order_dict.get("date_order")
                    dt = datetime.strptime(value, "%m/%d/%Y")
                    order_dict["date_order"] = (dt + timedelta(hours=8)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                if order_dict.get("commitment_date", False):
                    value = order_dict.get("commitment_date")
                    dt = datetime.strptime(value, "%m/%d/%Y")
                    order_dict["commitment_date"] = (dt + timedelta(hours=8)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

        except Exception as e:
            self.state = "error"
            self.log_message = str(Exception) + str(e)
            _logger.error(
                "Exception while while executing parsing raw message: %s.\n Original Traceback:\n%s",
                e,
                Exception,
            )
            raise e
        return order_dict

    def validate_document(self, record):

        if self.edi_model_id.model == "sale.order":
            # Update Fiscal Position
            record.fiscal_position_id = (
                record.partner_id.property_account_position_id
                and record.partner_id.property_account_position_id.id
                or False
            )

            if not record.ship_from_code:
                warehouse_id = record.partner_id.warehouse_id.id or False
                carrier_id = False
                route_id = False

                result = self.env["partner.shipping.method"].get_warehouse_details(
                    partner_id=record.partner_id.id,
                    rule="address",
                    zipcode=record.third_party_exists
                    and record.zip
                    or record.partner_shipping_id.zip
                    or record.partner_id.zip,
                    mode="edi",
                )

                if not result[0]:
                    result = self.env["partner.shipping.method"].get_warehouse_details(
                        partner_id=record.partner_id.id, rule="fixed", mode="edi"
                    )

                if result[0]:
                    record.warehouse_id = result[1]
                    record.route_id = result[2]
                    record.carrier_id = result[3]
                    record.ups_carrier_account = result[4][0]
                    record.fedex_bill_my_account = result[4][1]
                    record.fedex_carrier_account_retail = result[4][2]
                    record.fedex_carrier_account_dropship = result[4][3]

            if record.route_id:
                for line in record.order_line:
                    line.route_id = record.route_id

            if record.edi_shipping_cost:
                record._create_delivery_line(
                    record.carrier_id, record.edi_shipping_cost
                )

            if self.edi_supported_doc_id.confirm_record:
                record.action_confirm()

        return

    def _parse_raw_csv_lookup(self, field, model, raw_domain, result):
        """
        Lookup a related record id
        - field: a string with the mapped field name
        - struct_id: the Document Structure Line being processed
        - result: a dict with the current parse result. Not modified.

        Returns the id for the related record.
        May raise a Validation error if an lookup id is required but was not found.
        """

        domain = raw_domain % result
        model = self.env.get(model.model)

        # Convert from string domain to list domain
        domain_list = ast.literal_eval(domain)
        lookup_id = model.search(domain_list, limit=1)
        return lookup_id

    def parse_csv_message(self):
        """
        Parse the raw message and create the corresponding Odoo document
        Uses the self recordset of queue items.
        If successful, updates the queue item with the created record id.
        If not successful, updates the state and error log accordingly.
        """
        for inbound in self:

            try:
                if inbound.state in ["new", "error"]:
                    inbound.create_850()
                    if inbound.state != "error":
                        inbound.state = "done"
                else:
                    continue
            except Exception as e:
                inbound.state = "error"
                inbound.log_message = str(Exception) + str(e)
                _logger.error(
                    "Exception while while executing parsing raw message: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )
        return True

    @api.model
    def cron_inbound(self):
        """
        Perform all inbound operations.
        To be used in a cron job.
        - Checkin inbound messages
        - Parse all messages in New state
        """
        self.checkin_inbound_message()
        new_inbounds = self.search(
            [("direction", "=", "in"), ("state", "in", ("new", "error"))]
        )
        for inbound in new_inbounds:
            try:
                inbound.parse_raw_message()
                inbound.error = ""
            except Exception as e:
                inbound.state = "error"
                inbound.log_message = str(Exception) + str(e)
                _logger.error(
                    "Exception while while executing parsing raw message: %s.\n Original Traceback:\n%s",
                    e,
                    Exception,
                )
        return True

    @api.model
    def cron_csv_inbound(self):
        """
        Perform all inbound operations.
        To be used in a cron job.
        - Checkin inbound CSV messages
        - Parse all messages in New state
        """
        self.checkin_csv_inbound_message()

        new_inbounds = self.search(
            [("direction", "=", "in"), ("state", "in", ("new", "error"))]
        )
        for inbound in new_inbounds:
            try:
                inbound.parse_csv_message()
                if inbound.state != "error":
                    inbound.state = "done"
                inbound.error = ""
            except Exception as e:
                inbound.state = "error"
                inbound.log_message = str(Exception) + str(e)

        return True

    def checkout_inbound_message(self):
        if self:
            processed_inbounds = self.search(
                [("direction", "=", "in"), ("state", "=", "processed")]
            )

            for processed in processed_inbounds:
                try:
                    # Check if related doc in final state
                    processed.state = "done"

                except Exception as e:
                    _logger.error(
                        "Exception while while executing Checkout Inbound Message File: %s.\n Original Traceback:\n%s",
                        e,
                        Exception,
                    )

        return

    def get_record(self):
        """
        Returns the newly created record in wizard
        """
        self.ensure_one()
        # Get Model
        if self.rec_created and self.edi_supported_doc_id.edi_model_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": self.edi_supported_doc_id.edi_model_id.model,
                "res_id": self.rec_created,
                "view_mode": "form",
                "target": "current",
            }
