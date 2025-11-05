from odoo.addons.helpdesk.tests.common import HelpdeskCommon
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form
from odoo import fields
from datetime import date, datetime


class HelpdeskRepairBatch(HelpdeskCommon):
    """
        Test case for managing repair batches in the helpdesk module.
    """
    @classmethod
    def setUpClass(cls):
        super(HelpdeskRepairBatch, cls).setUpClass()
        cls.team_customer_rma = cls.env.ref("ol_helpdesk_repair_batch.helpdesk_team_customer_rma")
        cls.sale_order_obj = cls.env['sale.order']
        cls.payment_method_id = cls.env["payment.method"].search([], limit=1)
        cls.helpdesk_ticket_obj = cls.env['helpdesk.ticket']
        cls.product = cls.env['product.product'].create([
            {
                'name': 'Onlogic Product',
            }
        ])
        # Create a Sale Order
        cls.sale_order = cls.sale_order_obj.create({
            'partner_id': cls.partner.id,
            'commitment_date': fields.Datetime.to_string(datetime.now()),
            "sale_payment_method_id": cls.payment_method_id.id,
        })
        if "override_saleable_exception" in cls.sale_order_obj.fields_get():
            cls.sale_order.write({'override_saleable_exception': True})

        # Create a Sale Order Line
        cls.sale_order_line = cls.env['sale.order.line'].create({
            'product_id': cls.product.id,
            'price_unit': 10,
            'product_uom_qty': 1,
            'order_id': cls.sale_order.id,
        })

    def test01_create_repair_batch(self):
        # Confirm Sale Order and validate delivery
        sale_order = self.sale_order
        sale_order_line = self.sale_order_line
        sale_order.action_confirm()

        delivery = sale_order.picking_ids
        delivery.move_ids.quantity = 1
        
        delivery.move_ids.picked = True
        delivery.button_validate()

        # Create Helpdesk Ticket
        ticket = self.helpdesk_ticket_obj.create({
            'name': 'test',
            'partner_id': self.partner.id,
            'team_id': self.team_customer_rma.id,
            'sale_order_id': sale_order.id,
        })

        # Create Repair Batch
        repair_batch = self.env['repair.batch'].create({
            'partner_id': self.partner.id,
            'ticket_id': ticket.id,
            'product_id': self.product.id,
            'sale_id': sale_order.id,
            'sale_line_id': sale_order_line.id,
        })
        self.assertEqual(repair_batch.state, "draft")
        repair_batch.action_generate_repairs()
        self.assertTrue(repair_batch.repair_ids)

        # Verify Repair Order state
        repair_order = repair_batch.repair_ids
        self.assertEqual(repair_order.state, "draft")

        # Cancel Repair Batch and verify state changes
        repair_batch.action_repair_cancel()
        self.assertEqual(repair_order.state, "cancel")
        self.assertEqual(repair_batch.state, "cancel")

        # Set Repair Batch to draft and verify state changes
        repair_batch.action_repair_cancel_draft()
        self.assertEqual(repair_order.state, "draft")
        self.assertEqual(repair_batch.state, "draft")

        # Confirm Repair Batch and verify state changes
        repair_order._action_repair_confirm()
        self.assertEqual(repair_order.state, "confirmed")
        self.assertEqual(repair_batch.state, "confirmed")
        if delivery.location_id:
            self.assertEqual(repair_order.location_id.id, delivery.location_id.id)

        # Start Repair Batch and verify state changes
        repair_batch.action_repair_start()
        self.assertEqual(repair_order.state, "under_repair")
        self.assertEqual(repair_batch.state, "under_repair")

        # End Repair Batch and verify state changes
        repair_batch.action_repair_end()
        self.assertEqual(repair_order.state, "done")
        self.assertEqual(repair_batch.state, "done")

        # Attempt to cancel Repair Order and verify exceptions
        with self.assertRaises(UserError):
            repair_order.action_repair_cancel()

        with self.assertRaises(UserError):
            repair_order.action_repair_cancel_draft()

    def test02_create_repair_so(self):
        # Confirm the Sale Order
        sale_order = self.sale_order
        sale_order.action_confirm()

        # Create a Helpdesk Ticket
        ticket = self.helpdesk_ticket_obj.create({
            'name': 'test',
            'partner_id': self.partner.id,
            'team_id': self.team_customer_rma.id,
        })

        # Import the Sale Order into the Helpdesk Ticket
        import_sale_form = Form(self.env['helpdesk.ticket.import.sale'].with_context(default_ticket_id=ticket.id, default_sale_order_id=sale_order.id))
        import_sale = import_sale_form.save()
        import_sale._onchange_sale_order() # Trigger onchange to update fields based on the sale order
        import_sale.action_confirm() # Confirm the import action

        # Verify that the ticket has associated repair batches
        self.assertTrue(ticket.repair_batch_ids)

        # Generate repairs from the ticket
        ticket.action_generate_repairs()
        self.assertTrue(ticket.repair_ids)

        # Create a receipt for the ticket
        ticket.action_create_receipt()
        transfers = self.env["stock.picking"].search(
            [
                ("ticket_id", "=", ticket.id),
                ("picking_type_code", "=", "incoming"),
            ]
        )
        transfers.move_ids.picked = True
        transfers.button_validate()

        # Retrieve the Repair Batch and Repair Order
        repair_batch = ticket.repair_batch_ids
        repair_order = ticket.repair_ids

        # Validate the Repair Batch and ensure its state matches the Repair Order's state
        repair_batch.action_validate()
        self.assertEqual(repair_batch.state, repair_order.state)

        # Attempt to cancel the Repair Batch and ensure it raises an exception
        with self.assertRaises(UserError):
            repair_batch.action_repair_cancel()
            ticket.action_generate_repairs()
