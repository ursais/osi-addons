# Import Python libs
import csv
from datetime import datetime

# Import Odoo libs
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

from odoo.addons.ol_base.models.tools import odoo_binary_to_csv_data

DATE_FORMAT = "%m/%d/%Y"

REQUIRED_ADDRESS_FIELDS = {
    "first_name": "First Name",
    "last_name": "Last Name",
    "address_line1": "Address line 1",
    "city": "City",
    "state": "State",
    "postcode": "Zip code",
    "country": "Country",
}


class CsvLoaderWizard(models.TransientModel):
    """Custom CSV Load Wizard"""

    _name = "wizard.csv.loader"
    _description = "Delivery Order CSV Import"

    # COLUMNS #####

    name = fields.Char(default="CSV Delivery Order Import")
    csv_file = fields.Binary(string="Import File")
    csv_filename = fields.Char(string="Filename")
    delivery_orders = fields.One2many(
        comodel_name="wizard.stock.picking",
        inverse_name="csv_id",
        readonly=True,
    )
    error_html = fields.Html(string="Lines with Errors", readonly=True)

    # END #########
    # METHODS #####

    @api.model
    def validate_row(self, row, has_partner=None):
        """
        Validates a row of input from the csv
        """
        country_obj = self.env["res.country"]
        state_obj = self.env["res.country.state"]

        errors = []
        if not row.get("qty"):
            errors.append("Product Qty is required")

        if not row.get("product_sku") and not row.get("tha"):
            errors.append("Product SKU is required")
        else:
            # validate product sku
            product_sku = row.get("product_sku") or row.get("tha")
            product_id = self.env["product.product"].search(
                [("default_code", "=", product_sku)]
            )
            if len(product_id) == 1:
                row["product_id"] = product_id.id
                row["product_name"] = product_id.display_name
            elif len(product_id) > 1:
                errors.append(f"Product SKU is not unique: {product_sku}")
            else:
                errors.append(f"Product SKU does not exist: {product_sku}")

        if not row["first_name"]:
            # assume a continuation of the previous line,
            # so no more validation necessary
            if not has_partner:
                errors.append("No previous partner to assign sku/qty to")
            return errors

        # check date
        if not row.get("ship_on"):
            errors.append("Ship date is required")
        else:
            try:
                date = datetime.strptime(row["ship_on"], DATE_FORMAT)
                # set the time to be midday so that any
                # timezone issues are accounted for
                date = date.replace(hour=12)
                row["min_date"] = datetime.strftime(
                    date, DEFAULT_SERVER_DATETIME_FORMAT
                )
            except Exception as err:
                errors.append(f'Error parsing date: {row["ship_on"]} ({err})')

        # check company_id
        if not row.get("origin_company"):
            errors.append("Origin Company is required")
        elif not row["origin_company"].isdigit():
            # can't have a string for company id!
            errors.append(f'Invalid company ID: {row["origin_company"]}')
        else:
            company_id = self.env["res.partner"].browse(int(row["origin_company"]))
            if not company_id.exists():
                errors.append(f'No such company ID: {row["origin_company"]}')

        # check carrier_id
        if not row.get("carrier"):
            errors.append("Carrier is required")
        elif not row["carrier"].isdigit():
            # can't have a string for company id!
            errors.append(f'Invalid carrier: {row["carrier"]}')
        else:
            # We need to support old carrier IDs
            carrier_id = self.get_carrier_id(int(row["carrier"]))
            if not carrier_id.exists():
                errors.append(f'No such carrier: {row["carrier"]}')
            else:
                # update the row with the new carrier id
                row["carrier"] = carrier_id.id

        # check delivery address stuff:
        for field, name in REQUIRED_ADDRESS_FIELDS.items():
            if not row.get(field):
                errors.append(f"{name} is required")

        # look up country and state
        if row.get("country"):
            country_id = country_obj.search([("code", "=", row["country"])])
            if country_id.exists():
                row["country_id"] = country_id.id
            else:
                errors.append(f'Country code not found: {row["country"]}')

        if row.get("state"):
            state_id = state_obj.search(
                [
                    ("code", "=", row["state"]),
                    ("country_id", "=", row.get("country_id")),
                ]
            )
            if state_id.exists():
                row["state_id"] = state_id.id
            else:
                errors.append(
                    f'State code {row["state"]} not found for country {row["country"]}'
                )

        # look up ship_from country and state
        ccode = row.get("ship_from_country")
        if ccode:
            country_id = country_obj.search([("code", "=", ccode)])
            if country_id.exists():
                row["ship_from_country_id"] = country_id.id
            else:
                errors.append(f"Country code not found: {ccode}")

        scode = row.get("ship_from_state")
        if scode:
            state_id = state_obj.search(
                [("code", "=", scode), ("country_id", "=", ccode)]
            )

            if state_id.exists():
                row["ship_from_state_id"] = state_id.id
            else:
                errors.append(f"State code {scode} not found for country {ccode}")

        return errors

    @api.model
    def get_carrier_id(self, delivery_carrier_id):
        """
        Translate v8 carrier ids to current carrier ids due to customer requirements
        """
        old_carrier = self.env["delivery.carrier"].browse(delivery_carrier_id)
        if old_carrier.exists() and old_carrier.v10_carrier_id.exists():
            # A mapping exists
            return old_carrier.v10_carrier_id

        if old_carrier.exists() and old_carrier.active:
            # No mapping, but it's an active carrier id, so it's fine
            return old_carrier

        # No mapping, not active. Return nothing.
        return self.env["delivery.carrier"]

    @api.model
    def soft_validate_row(self, row):
        """
        Validate row values that should throw warnings but do not halt import.
        """
        zcta = 5
        warnings = []
        postcode = row.get("postcode")
        ship_from = row.get("ship_from_postcode")

        # check if zipcode is valid in US
        if postcode and len(postcode) < zcta:
            warnings.append(f"Zipcode {postcode} has fewer than {zcta} characters")

        # check if ship_from zipcode is valid in US
        if ship_from and len(ship_from) < zcta:
            warnings.append(f"Zipcode {ship_from} has fewer than {zcta} characters")

        return warnings

    @api.model
    def get_partner(self, data, address_type="contact"):
        """
        Creates a res.partner object from the given data
        """
        name_parts = [
            x for x in [data["first_name"], data["last_name"]] if x is not None
        ]
        if not any(
            [data["first_name"], data["last_name"], data["destination_company"]]
        ):
            # Don't create a partner if we don't have any way of identifying them
            return None

        return self.env["res.partner"].create(
            {
                "parent_id": int(data["origin_company"]),
                "csv_company_name": data["destination_company"] if name_parts else None,
                "name": " ".join(name_parts) or data["destination_company"],
                "street": data["address_line1"],
                "street2": data["address_line2"] or None,
                "city": data["city"],
                "state_id": data.get("state_id"),
                "zip": data["postcode"],
                "country_id": data.get("country_id"),
                "phone": data["phone"],
                "email": data["notify_email"],
                "type": address_type,
                "active": False,
            }
        )

    @api.model
    def create_error_html(self, row_num, raw_line, errors, etype="error"):
        """
        Formats the given error array into a nice html string
        """
        errstyle = "padding-left: 1em;"
        if etype == "error":
            errstyle += "border-left: solid 3px red;"
        elif etype == "warning":
            errstyle += "border-left: solid 3px orange;"

        html = (
            f"<div style='{errstyle}'><span style='font-weight:bold;'>{etype.capitalize()}(s) on line "
            f"<span style='text-decoration:underline;'>{row_num}</span></span>: {raw_line}"
        )

        html += "<ul>"
        for error in errors:
            html += f"<li>{error}</li>"
        html += "</ul></div>"

        return html

    def process_csv(self):
        """
        Validates and parses the csv data into several wizard objects
        """
        self.ensure_one()

        csv_data_file = odoo_binary_to_csv_data(
            odoo_binary=self.csv_file, carriage_return_to_new_line=True
        )

        # Load the lines into a list, so we can point them out if there are errors
        content = csv_data_file.readlines()

        # Drop the first line (columns) and any blank lines
        content = [line.strip() for line in content[1:] if line.strip()]

        # Reset to the start of the file data so we can parse it
        csv_data_file.seek(0)

        reader = csv.DictReader(csv_data_file, strict=True)

        stock_loc_obj = self.env["stock.location"]
        picking_out = self.env["stock.picking.type"].search([("code", "=", "outgoing")])

        delivery_orders = self.env["wizard.stock.picking"]
        self.error_html = ""

        # check if this csv is already referenced
        matching_dos = self.env["stock.picking"].search(
            [("origin", "like", self.csv_filename)]
        )
        if matching_dos:
            errors = [
                f"Found {len(matching_dos)} delivery orders matching file: {self.csv_filename}"
            ]
            self.error_html += self.create_error_html(
                "CSV Name", self.csv_filename, errors, etype="warning"
            )

        cur_partner = None
        for row_num, row in enumerate(reader):
            # strip all whitespace from individual csv cells
            for key, val in row.items():
                if key and row[key]:
                    row[key] = val.strip()

            warns = self.soft_validate_row(row)
            if warns:
                # Generate soft warning messages that do not stop processing
                self.error_html += self.create_error_html(
                    row_num + 2, content[row_num], warns, etype="warning"
                )

            errors = self.validate_row(row, has_partner=cur_partner)
            if errors:
                # row_num + 2 is because we skip the header line and
                # start at 1 instead of 0
                self.error_html += self.create_error_html(
                    row_num + 2, content[row_num], errors
                )
                continue

            cur_move_vals = {
                "product_id": row["product_id"],
                "product_uom_qty": row["qty"],
                "product_uom": self.env.ref("uom.product_uom_categ_unit").id,
                "location_id": stock_loc_obj.search([("name", "=", "Warehouse")]).id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "name": row["product_name"],
            }

            cur_partner = self.get_partner(row, address_type="other")
            partner_shipping_id = cur_partner.copy(
                {
                    "type": "delivery",
                    "active": False,
                    "is_company": False,
                    "parent_id": cur_partner.id,
                }
            )
            cur_partner.write({"type": "contact"})
            ship_from = self.get_partner(
                {
                    "origin_company": row.get("ship_from_company")
                    and row["origin_company"],
                    "destination_company": row.get("ship_from_company"),
                    "first_name": row.get("ship_from_first_name"),
                    "last_name": row.get("ship_from_last_name"),
                    "address_line1": row.get("ship_from_address_line1"),
                    "address_line2": row.get("ship_from_address_line2"),
                    "city": row.get("ship_from_city"),
                    "state_id": row.get("ship_from_state_id"),
                    "postcode": row.get("ship_from_postcode"),
                    "country_id": row.get("ship_from_country_id"),
                    "phone": row.get("ship_from_phone"),
                    "notify_email": None,
                },
                address_type="other",
            )

            # Check if the row is set to blind ship
            if (
                ship_from
                or row.get("blind", "NO").upper() == "YES"
                or row.get("blind_drop_ship", "NO").upper() == "YES"
            ):
                set_blind_drop_ship = True
            else:
                set_blind_drop_ship = False

            if cur_partner:
                # we created a new partner, so also create a new wizard DO
                delivery_order_values = {
                    "name": "OUT/Consigned",
                    "picking_type_id": picking_out.id,
                    "min_date": row["min_date"],
                    "carrier_id": row["carrier"],
                    "origin": "{}{}".format(
                        self.csv_filename,
                        row["source"] and ":{}".format(row["source"]) or "",
                    ),
                    "custom_shipping_account": row["account_number"],
                    "partner_id": cur_partner.id,
                    "partner_shipping_id": partner_shipping_id.id,
                    "additional_notes": row["notes"],
                    "note": row["notes"],
                    "move_lines": [
                        (0, 0, cur_move_vals)
                    ],  # create current move and append
                    "blind_ship_from": ship_from
                    and ship_from.id,  # add blind_ship_from partner if it exists
                    "blind_drop_ship_csv": set_blind_drop_ship,
                    "customer_po": row.get("po_number"),
                    "location_id": stock_loc_obj.search(
                        [("name", "=", "Warehouse")]
                    ).id,
                    "location_dest_id": self.env.ref(
                        "stock.stock_location_customers"
                    ).id,
                }

                # create and append to recordset
                delivery_orders |= self.env["wizard.stock.picking"].create(
                    delivery_order_values
                )

        return delivery_orders

    def import_csv(self):
        """
        Called by button on the wizard view.  Starts the import process
        """

        if not self.csv_file:
            raise UserError(_("You must specify the csv file to import!"))

        if self.delivery_orders:
            self.delivery_orders.unlink()
            self.delivery_orders = None

        self.delivery_orders = self.process_csv().mapped("id")

        # pass on to the next view
        return {
            "name": "Orders to Create on Import",
            "view_mode": "form",
            "view_type": "form",
            "view_id": self.env.ref("ol_stock_loadcsv.view_orders_to_import").id,
            "res_model": "wizard.csv.loader",
            "res_id": self.id,
            "type": "ir.actions.act_window",
            "target": "new",
            "context": self.env.context,
        }

    def import_confirm(self):
        """
        Creates the real delivery orders and stock moves from the wizard
        versions once the user has had a chance to verify.
        """
        self.ensure_one()

        if not self.delivery_orders:
            # nothing to import is like a cancel
            return self.import_cancel()

        # create attachment
        attach_partner = self.delivery_orders[0].partner_id.parent_id
        vals = {
            "name": self.csv_filename,
            "res_model": attach_partner._name,
            "res_id": attach_partner.id,
            "company_id": attach_partner.company_id.id,
            "type": "binary",
            "datas": self.csv_file,
        }
        attachment = self.env["ir.attachment"].create(vals)

        # create the real delivery orders
        delivery_orders = self.delivery_orders.create_stock_pickings(attachment)

        # mark as ready to go
        delivery_orders.action_confirm()
        res = {
            "name": "Imported Delivery Orders",
            "view_mode": "tree,form",
            "view_type": "form",
            "res_model": "stock.picking",
            "domain": "[('id', 'in', ["
            + ",".join(map(str, delivery_orders.mapped("id")))
            + "])]",
            "type": "ir.actions.act_window",
            "target": "current",
        }
        return res

    def import_cancel(self):
        """
        Do some cleanup before closing the wizard popup
        """
        self.ensure_one()
        for delivery_order in self.delivery_orders:
            # these were not transient objects, so they should be cleaned up
            delivery_order.partner_id.unlink()

        # clean up anything else left over
        self.unlink()

        return {"type": "ir.actions.act_window_close"}

    # END #########


class CsvStockPicking(models.TransientModel):
    _name = "wizard.stock.picking"
    _description = "Temporary stock picking for validation"

    # COLUMNS #####
    csv_id = fields.Many2one(comodel_name="wizard.csv.loader", string="Wizard CSV!")
    name = fields.Char(string="Reference", default="OUT/Temporary")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    partner_shipping_id = fields.Many2one(
        comodel_name="res.partner", string="Delivery Address", readonly=True
    )
    picking_type_id = fields.Many2one(comodel_name="stock.picking.type")
    min_date = fields.Datetime(string="Scheduled Date")
    carrier_id = fields.Many2one(comodel_name="delivery.carrier")
    custom_shipping_account = fields.Char(string="Shipping Account")
    origin = fields.Char(string="Source Document")
    note = fields.Text(string="Internal note")
    additional_notes = fields.Text()
    move_lines = fields.One2many(
        comodel_name="wizard.stock.move",
        inverse_name="csv_picking_id",
        string="Product",
    )
    blind_ship_from = fields.Many2one(comodel_name="res.partner", string="Ship From")
    blind_drop_ship = fields.Boolean()
    blind_drop_ship_csv = fields.Boolean(
        string="Blind Drop Ship Imported",
        help="""The imported value of "Blind Drop Ship".
        This overrides the calculated blind_drop_ship field.""",
    )
    customer_po = fields.Char(string="Customer PO")
    location_id = fields.Many2one(
        comodel_name="stock.location", string="Source Location"
    )
    location_dest_id = fields.Many2one(
        comodel_name="stock.location", string="Destination Location"
    )

    # END #########
    # METHODS #########

    def create_stock_pickings(self, attachment=None):
        """
        Creates and returns real stock pickings from this object's data
        """
        delivery_orders = self.env["stock.picking"]
        location_id = self.env.ref("stock.stock_location_stock")
        location_dest_id = self.env.ref("stock.stock_location_customers")

        for record in self:
            # get the values for the stock moves in the form
            # [(0,0, {vals1...}), (0,0, {vals2...}), etc]
            move_lines = record.move_lines.get_stock_move_vals()
            delivery_order_values = {
                "partner_id": record.partner_id.id,
                "picking_type_id": record.picking_type_id.id,
                "scheduled_date": record.min_date,
                "carrier_id": record.carrier_id.id,
                "origin": record.origin,
                "note": record.note,
                "move_line_ids": move_lines,
                "blind_ship_from": record.blind_ship_from.id,
                "location_id": record.location_id.id or location_id.id or False,
                "location_dest_id": record.location_dest_id.id
                or location_dest_id.id
                or False,
                "csv_import": True,
                "csv_partner_shipping_id": record.partner_shipping_id.id,
                "csv_customer_po": record.customer_po,
                "blind_drop_ship_csv": record.blind_drop_ship,
            }

            delivery_order = self.env["stock.picking"].create(delivery_order_values)

            # Add attachment
            delivery_order.message_post(
                body=_("Created from imported csv file"), attachment_ids=[attachment.id]
            )
            delivery_order.partner_id.message_post(
                body=_("Created from imported csv file"), attachment_ids=[attachment.id]
            )
            delivery_orders |= delivery_order

        return delivery_orders

    # END #########


class CsvStockMove(models.TransientModel):
    _name = "wizard.stock.move"
    _description = "Temporary stock move for validation"

    # COLUMNS #####

    csv_picking_id = fields.Many2one(
        comodel_name="wizard.stock.picking", string="Wizard Picking!"
    )
    name = fields.Char(string="Description")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    product_uom_qty = fields.Float(string="Quantity")
    product_uom = fields.Many2one(comodel_name="uom.uom", string="UOM")
    location_id = fields.Many2one(
        comodel_name="stock.location", string="Source Location"
    )
    location_dest_id = fields.Many2one(
        comodel_name="stock.location", string="Destination Location"
    )

    # END #########
    # METHODS #####

    def get_stock_move_vals(self):
        """
        Returns a list of stock move values to be used by a stock.picking.create call
        """
        stock_move_vals = []
        location_id = self.env.ref("stock.stock_location_stock")
        location_dest_id = self.env.ref("stock.stock_location_customers")

        for record in self:
            vals = {
                "product_id": record.product_id.id,
                "quantity": record.product_uom_qty,
                "product_uom_id": record.product_uom.id,
                "location_id": record.location_id.id or location_id.id or False,
                "location_dest_id": record.location_dest_id.id
                or location_dest_id.id
                or False,
            }
            stock_move_vals.append((0, 0, vals))
        # returning a recordset here
        return stock_move_vals

    # END #########
