# Import Python libs
from enum import Enum

# Import Odoo libs
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PutInPackStates(Enum):
    SERIAL_IN_PACK = "Serial Number In Pack"
    SERIAL_NOT_IN_PACK = "Serial Number Not In Pack"


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def remove_serial_from_package(self):
        """
        Removes a move line from a package (the same as removing a serial from a package)
        """
        self.result_package_id = False
        # Update the related packages in the wizard so that the UI reflects these changes
        if wizard_id := self._context.get("wizard_id"):
            self.env["put.in.pack.wizard"].browse(wizard_id).update_packages()


class PutInPackWizard(models.TransientModel):
    _name = "put.in.pack.wizard"
    _inherit = "barcodes.barcode_events_mixin"
    _description = "Put In Pack Wizard"
    _transient_max_hours = 1

    # COLUMNS #####
    name = fields.Char(default="Put In Pack Wizard")
    user_feedback = fields.Html()
    scanned_serial = fields.Many2one(string="Serial Number", comodel_name="stock.lot")
    serial_move_line = fields.Many2one(
        string="Serial Number Move Line", comodel_name="stock.move.line"
    )
    delivery = fields.Many2one(string="Delivery", comodel_name="stock.picking")
    packages = fields.Many2many(
        "stock.quant.package",
        "put_in_pack_packages_rel",
        "put_in_pack_id",
        "package_id",
    )
    move_lines = fields.Many2many(
        "stock.move.line",
        "put_in_pack_move_lines_rel",
        "put_in_pack_id",
        "move_line_id",
    )
    # STATES
    operating_object = fields.Selection(
        [
            ("serial", "Serial"),
            ("delivery", "Delivery Order"),
            ("package", "Package"),
            ("master_case", "Master Case Dimensions"),
        ]
    )
    state = fields.Char()

    """
    The design philosophy for this tool is to enable Ops with the fewest required interactions. This means that 
    we want to handle all the logic within the wizard without needing to have the user save the form or click 
    any unnecessary buttons. The barcode handler for odoo is built using onchange functions which create an in
    memory copy of the record to perform changes on. This is done to enable responsive UI features but presents
    a challenge for this tool where the write to the database is deferred.

    This tool is essentially a state machine and so requires context to operate correctly. This context is the
    current state of the record, so it is essential for the database, ORM, and UI to be in sync. There are a
    few things this tool does to enable these seamless updates across the system:
        1. Use a custom barcode widget which bypasses the asynchronous functionality of the original barcode
        widget and forces things to operate in sequence.
        2. Force save the record after the barcode onchange functionality has completed. This is the same as
        if the user had clicked the save button on the form.
        3. Ensure the fields are force saved through the form view (force_save="1")

    This is the best way I have found to achieve this functionality. This cannot be done using writes because
    of the nature of onchange described above. Even using self._origin, which points you to the "real" record
    is not enough because it cannot fetch updates to relational fields (think tree views). The write method
    would additionally require you to be sure that the "real" and "copy" record are in the same state which
    can get messy.

    To address concerns about forcing synchronous functionality, I have 3 points. First, there will be only
    be a handful of people using this app, so load should not be a problem. Second, in order for this app to
    function correctly, users would need to save the form anyway to get updated data. This is just taking that
    step out of their hands and requiring fewer clicks. Third, I think that the functionality gained is well
    worth any performance loss.
    """

    @api.model
    def default_get(self, fields):
        """
        Pre-load fields in the wizard with existing data
        """
        res = super().default_get(fields)
        return res

    def action_reset_wizard(self):
        """
        Reset the wizard view and clear all of the data
        """
        view_id = self.env.ref("ol_delivery.view_put_in_pack_wizard").id
        return {
            "name": "Test",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "put.in.pack.wizard",
            "view_id": view_id,
            "target": "main",
        }

    def action_set_selector(self):
        """
        This sets the object that we're using as a frame of reference for future operations.

        E.g. if the first scan is a serial number, then that will be saved as the operating object and future
        scans will be using that serial number as context for any operations.
        """
        self.operating_object = self.env.context.get("object_type")

    def on_barcode_scanned(self, barcode):
        """
        This function will execute for each barcode scan.
        In some cases we want to keep track of where we are in case we want to use the context of our previous
        actions to execute further functionality.
        """
        if self.operating_object == "serial":
            self.handle_serial_number(barcode)

    def add_serial_into_pack(self, pack):
        """
        Move a serial number into a specified package
        """
        # Check to make sure the scanned package is a valid package on the delivery order
        if pack in self.delivery.package_ids:
            self.serial_move_line.result_package_id = pack
            # Update packages since they may have changed
            self.update_packages()
        else:
            raise ValidationError(
                f"Package {pack.name} is not present on Delivery Order {self.delivery.name}"
            )

    def put_serial_in_new_pack(self, master_case):
        """
        Handle the logic for creating a new package, adding move_line(s) to it, and attaching it to
        the correct delivery order
        """
        package = self.env["stock.quant.package"].create({})
        package.package_type_id = master_case
        sml = self.serial_move_line
        default_dest_location = sml._get_default_dest_location()
        sml.location_dest_id = default_dest_location._get_putaway_strategy(
            product=sml.product_id,
            quantity=sml.quantity,
            package=package,
        )
        sml.write(
            {
                "result_package_id": package.id,
            }
        )
        self.env["stock.package_level"].create(
            {
                "package_id": package.id,
                "picking_id": self.delivery.id,
                "location_id": False,
                "location_dest_id": sml.location_dest_id.id,
                "move_line_ids": [(6, 0, sml.ids)],
                "company_id": self.delivery.company_id.id,
            }
        )
        self.update_packages()

    def get_move_line_containing_serial(self, move_lines, serial):
        """
        Filter down the move lines in a delivery order to find the one containig a serial number
        """
        return move_lines.filtered(lambda x: x.lot_id == serial)

    def update_packages(self):
        """
        Packages on the delivery order may change so we need to update them periodically
        """
        self.packages = self.delivery.package_ids

    def handle_serial_number(self, barcode):
        """
        Serial number state machine
        """
        if not self.state:
            if serial := self.env["stock.lot"].search([("name", "=", barcode)]):
                if len(serial) > 1:
                    raise ValidationError(
                        f"Too many serial numbers found! Serials: {serial}"
                    )
                delivery_order = (
                    self.env["stock.move.line"]
                    .search(
                        [
                            ("lot_id", "=", serial.id),
                            ("picking_code", "=", "outgoing"),
                            ("state", "!=", "done"),
                        ]
                    )
                    .picking_id
                )

                # If we did not find a delivery order with the given domain, give the user some feedback
                if not delivery_order:
                    self.user_feedback = """WARNING: Could not find any open delivery orders associated with the given serial number"""

                # Set some fields for user context
                self.scanned_serial = serial
                self.delivery = delivery_order
                self.packages = self.delivery.package_ids
                self.move_lines = self.delivery.move_line_ids
                self.serial_move_line = self.get_move_line_containing_serial(
                    delivery_order.move_line_ids, serial
                )
            else:
                raise ValidationError(f"Serial number {barcode} was not found!")

        # Update the state of the wizard depending on if the serial number is in a package or not
        self.state = (
            PutInPackStates.SERIAL_IN_PACK.value
            if self.serial_move_line.result_package_id
            else PutInPackStates.SERIAL_NOT_IN_PACK.value
        )

        # If the serial number is in a pack, the user scans a different pack, and that pack is in
        # the delivery order, then move the serial into that pack
        if self.state == PutInPackStates.SERIAL_IN_PACK.value:
            if pack := self.env["stock.quant.package"].search([("name", "=", barcode)]):
                self.add_serial_into_pack(pack)

        # If the serial number is not in a pack the user can either scan an existing pack to add it
        # or scan a master case to create a new pack
        elif self.state == PutInPackStates.SERIAL_NOT_IN_PACK.value:
            if pack := self.env["stock.quant.package"].search([("name", "=", barcode)]):
                self.add_serial_into_pack(pack)
            if master_case := self.env["stock.package.type"].search(
                [("barcode", "=", barcode)]
            ):
                self.put_serial_in_new_pack(master_case)
