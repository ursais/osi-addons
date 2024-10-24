# Import Python Libs
import json
import logging
from psycopg2 import OperationalError

_logger = logging.getLogger(__name__)


# Import Odoo libs
from odoo import models, fields
from odoo.tools.float_utils import float_compare


class SaleOrder(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "sale.order"
    _inherit = ["sale.order", "graphql.mixin"]

    # COLUMNS ###
    ecommerce_state = fields.Char(
        string="eCommerce State",
        readonly=True,
        help="a SO state field populated by website",
    )
    ecommerce_total = fields.Monetary(string="eCommerce Total", readonly=True)
    ecommerce_tax = fields.Monetary(
        string="eCommerce Taxes",
        readonly=True,
    )
    # END ######

    def _post_graphql_set_payment_methods(self, ecommerce_payment_method_details):
        """
        Finish the decoding and handling of payment methods,
        now that the sale order record has been created
        """
        try:
            payment_data = json.loads(ecommerce_payment_method_details)
            payment_method = self.env["sale.order.payment.method.base"].search(
                [("id", "=", payment_data.get("method_id"))]
            )
            payment_sub_method = self.env["sale.order.payment.method.base"].search(
                [("id", "=", payment_data.get("sub_method_id"))]
            )

            # start building the create values with common fields
            create_vals = {
                "order_id": self.id,
                "method_id": payment_method.parent_method_id.id or payment_method.id,
                "sub_method_id": payment_sub_method.id,
            }

            # add Stripe details, if we have them
            if payment_data.get("stripe_card_id"):
                stripe_field_names = ["stripe_charge_ids", "stripe_card_id"]
                for name in stripe_field_names:
                    create_vals[name] = payment_data.get(name)

                # stripe_customer is a computed field, so we need to set it via stored_stripe_customer
                # which is the first location that is checked when computing stripe_customer
                if payment_data.get("stripe_customer", None):
                    create_vals["stored_stripe_customer"] = payment_data.get(
                        "stripe_customer"
                    )

            new_sale_order_payment_method = self.env[
                "sale.order.payment.method"
            ].create(create_vals)
            write_vals = {"payment_method_id": new_sale_order_payment_method}

            # add PayPal details, if we have them (this requires the payment method record to already exist)
            if payment_data.get("paypal_data"):
                paypal_verify_ids = self._post_graphql_decode_paypal_payment(
                    payment_data.get("paypal_data"), new_sale_order_payment_method
                )
                # we need to update the sale.order.payment.method record with this information, but it only takes the record, not list
                new_sale_order_payment_method.write(
                    {"paypal_verify_ids": paypal_verify_ids[0]}
                )
                # and then include it in the write values for updating the sale.order itself
                write_vals.update({"paypal_verify_ids": paypal_verify_ids})
                self.write(write_vals)
        except Exception as error:
            msg = (
                "Error during Website Sale Order payment handling.\nEcommerce Payment"
                f" Details:{ecommerce_payment_method_details}\nError: {error}"
            )
            self.env.ref("ls_graphql_sale.order_stripe_import_error").create_hold(
                order=self, custom_msg=msg
            )

    def do_taxes_match(self):
        """Check if taxes match between the systems"""
        return float_compare(self.ecommerce_tax, self.amount_tax, 2) == 0

    def does_total_match(self):
        """Check if totals match between the systems"""
        return float_compare(self.ecommerce_total, self.amount_total, 2) == 0

    def has_zero_value_lines(self):
        """Check if all non shipping lines have non zero total value"""

        for order_line in self.order_line:
            if order_line.is_delivery:
                continue
            if order_line.price_total == 0:
                return True
        return False

    def has_import_tax_difference_holds(self):
        # Manually encode totals, we use these for verification but also
        # to set Commercetools in case of edits. Don't override if we're currently
        # reviewing disparity.
        tax_check_id = self.env.ref("ls_graphql_sale.order_import_tax_difference").id
        active_tax_holds = self.hold_ids.filtered(
            lambda x: (x.check_id.id == tax_check_id and not x.resolve_user_id)
        )
        return bool(active_tax_holds)

    # def _post_graphql_create_actions(self, **kwargs):
    #     """
    #     We add some decoding-like functionality after the SO creation to handle
    #     things like taxes and holds. More might be added here in the future.
    #     """

    #     try:
    #         self._post_graphql_set_taxes()

    #         # The state field is not decoded traditionally, instead we are passing it through the **kwargs parameter to check for cancelled orders.
    #         # To determine which action to take, check if the incoming state is cancelled and the current order state is in draft.
    #         # If these are true then cancel the order, otherwise validate and push the order forward.
    #         if (
    #             kwargs.get("state", False) in CANCELLED_STATES
    #             and self.state not in CANCELLED_STATES
    #             and self.detailed_state in SALE_DRAFT_STATES
    #         ):
    #             self.action_cancel()
    #         else:
    #             self.action_validate(skip_user_validation=True)

    #         # Add a hold if the ecommerce taxes (from message) don't match the computed taxes (from Avatax)
    #         if not self.do_taxes_match():
    #             msg = "Ecommerce Tax: {:.2f} <br/>Odoo Tax: {:.2f}".format(
    #                 self.ecommerce_tax, self.amount_tax
    #             )
    #             self.env.ref("ls_graphql_sale.order_import_tax_difference").create_hold(
    #                 self, custom_msg=msg
    #             )

    #         # Add a hold if the ecommerce total amount doesn't match the computed total
    #         if not self.does_total_match():
    #             msg = "Ecommerce Total: {:.2f} <br/>Odoo Total: {:.2f}".format(
    #                 self.ecommerce_total, self.amount_total
    #             )
    #             self.env.ref(
    #                 "ls_graphql_sale.order_import_amount_total_difference"
    #             ).create_hold(self, custom_msg=msg)

    #         # Add a hold if the sale order has sale order lines that have 0 price total set
    #         if self.has_zero_value_lines():
    #             msg = "One or multiple order lines have 0 as total value"
    #             self.env.ref(
    #                 "ls_graphql_sale.order_import_zero_value_lines"
    #             ).create_hold(self, custom_msg=msg)

    #         # If we get this far and still don't have holds, create one because something has gone wrong
    #         if self.state == "draft" and not self.has_active_holds():
    #             msg = "No Holds Created, but something went wrong on import, call IT."
    #             self.env.ref("ls_graphql_sale.generic_import_error_check").create_hold(
    #                 self, custom_msg=msg
    #             )

    #         # force the order into Review if we are still in Draft
    #         if self.state == "draft":
    #             self.state = self.detailed_state = "review"

    #         # finish Stripe transactions, where applicable
    #         for transaction in self.transaction_ids.filtered(
    #             lambda t: t.state != "done"
    #         ):
    #             if transaction.state == "error":
    #                 # Handle transactions with errors
    #                 msg = (
    #                     "The following error occurred during Stripe Transaction handling:"
    #                     f" {transaction.state_message} | Reference: {transaction.reference} | Transaction:"
    #                     f" {transaction}"
    #                 )
    #                 self.env.ref(
    #                     "ls_graphql_sale.order_import_transaction_check"
    #                 ).create_hold(self, custom_msg=msg)
    #                 continue

    #             # make sure the transaction amount matches its charge
    #             transaction.amount = transaction.stripe_charge_id.initial_amount
    #             # mark the transaction as finished
    #             transaction._set_transaction_done()
    #             # trigger all the post-done functionality (such as payment creation))
    #             transaction._post_process_after_done()
    #     except OperationalError as operational_error:
    #         # For typical transaction serialization errors we don't want to log the error
    #         # as these errors will be handled by the `queue.job`
    #         if operational_error.pgcode not in PG_CONCURRENCY_ERRORS_TO_RETRY:
    #             # Add special log entry
    #             self.log_exception_message(
    #                 "SO Post GraphQL Create Actions | Can't process action. Non standard operational "
    #                 f"error: {operational_error.pgcode}. Error: `{operational_error}`",
    #                 company=self.env.company.short_name.upper(),
    #             )
    #             raise

    #         self.log_warning_message(
    #             "SO Post GraphQL Create Actions | could not process action as a result of an Odoo"
    #             f" Concurrency error: {tools.ustr(operational_error.pgerror, errors='replace')} | Record: {self}",
    #             company=self.env.company.short_name.upper(),
    #         )

    #         raise RetryableJobError(
    #             "GraphQL Mutation Error | SO Post GraphQL Create Actions | Cant't process action. Odoo Concurrency error:"
    #             f" `{tools.ustr(operational_error.pgerror, errors='replace')}`. Error:"
    #             f" `{operational_error}` | Company: {self.env.company.short_name.upper()}",
    #             seconds=2,
    #         ) from operational_error
    #     except Exception as e:
    #         msg = (
    #             "An unexpected error ocurred during the Sale Order `Post GraphQL Create Actions`:"
    #             f"| Sale Order: {self.name}({self.id}) "
    #             f"| Payment Method: {self.payment_method_id.name} ({self.payment_method_id.id})"
    #             f"| Company: {self.env.company.short_name.upper()}"
    #             f"| Error: {e}"
    #         )
    #         self.env.ref("ls_graphql_sale.order_import_valid_check").create_hold(
    #             self, custom_msg=msg
    #         )

    #     return super()._post_graphql_create_actions()

    def _post_graphql_set_taxes(self):
        try:
            # call onchanges to set the fiscal position
            self.onchange_partner_shipping_id()
            self.onchange_exemption()
            # and force the recomputation of tax IDs on product lines
            self.action_refresh()
        except OperationalError as operational_error:
            raise operational_error
        except Exception as e:
            msg = (
                f"An error occurred during the `Post GraphQL Set Taxes` functionality"
                f"| Sale Order: {self.name}({self.id}) "
                f"| Payment Method: {self.payment_method_id.name} ({self.payment_method_id.id})"
                f"| Company: {self.env.company.short_name.upper()}"
                f"| Error: {e}"
            )
            self.message_post(subject="Integration Error", body=msg)
            _logger.exception(msg)

    def _post_graphql_decode_paypal_payment(self, paypal_data, payment_method_record):
        """
        Take the data provided in the paypal_data and make a new paypal verification
        record that we're going to link to the payment method and, from there, to
        the newly-created sale order

        Note that paypal_verify_ids is a One2many field on both a sale.order.payment.method
        and a sale.order that relates a payment record for a SO to (potentially) many PayPal
        verifications. However, it looks like we so far have never had more than one
        verification for a single SO.
        """
        paypal_transactions = []
        for transaction in paypal_data:
            vals = {
                "seller_protection_status": transaction.get(
                    "seller_protection_status", False
                ),
                "payment_method_id": payment_method_record.id,
            }
            res = self.env["paypal.verification"].create(vals)
            paypal_transactions.append(res)

        return paypal_transactions

    def process_graphql_sale_order_holds(self, **kwargs):
        """
        Add any requested Sale Order Holds
        kwargs example:
        {
            'Sale Order Line Import Error':
                {
                    'custom_msg': '',
                    'ref': 'ls_graphql_sale.order_line_import_error_check'
                },
            'Something else is wrong':
                {
                    'custom_msg': '',
                    'ref': 'ls_graphql_sale.order_line_import_error_check'
                }
        }
        """
        for hold_reason, hold_data in kwargs.items():
            check = self.env.ref(hold_data.get("ref", False))
            if check:
                msg = hold_data.get("custom_msg", "")
                _logger.info(
                    f"GraphQL Mutation | S:3 | Add new Sale Order Hold | Reason: {hold_reason}"
                    f" | Sale Order: {self} | Check: {check} | Hold Message; {msg}"
                    f"  TI: {self.env.context.get('transaction_id', 'N/A')}"
                )
                check.create_hold(order=self, custom_msg=msg)
