# Import Python Libs
import logging
from psycopg2 import OperationalError

_logger = logging.getLogger(__name__)


# Import Odoo libs
from odoo import models, fields, tools
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.tools.float_utils import float_compare


class SaleOrder(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "sale.order"
    _inherit = ["sale.order", "graphql.mixin"]

    # COLUMNS ###
    ecommerce_total = fields.Monetary(string="eCommerce Total", readonly=True)
    ecommerce_tax = fields.Monetary(string="eCommerce Taxes", readonly=True)
    # END ######

    def check_order_import_tax_difference(self):
        # We only want to enforce this exception for orders from the website
        if self.origin_system == "COMMERCETOOLS":
            return float_compare(self.ecommerce_tax, self.amount_tax, 2) == 0
        return False

    def check_order_import_shipping_error(self):
        # We only want to enforce this exception for orders from the website
        if self.origin_system == "COMMERCETOOLS":
            return not bool(self.order_line.filtered(lambda x: x.is_delivery))
        return False

    def _post_graphql_set_payment_methods(self, ecommerce_payment_method_details):
        """
        Finish the decoding and handling of payment methods, now that the sale order record has been created
        """
        pass

    def _post_graphql_process_order_lines(self, order_lines):
        """
        Process the incoming order lines using the product configurator wizard. We need the sale order to exist
        in order to run the wizard properly which is why this is a post graphql action.

            [
                {
                    "product": "PRODUCT UUID",
                    "option": "ATTRIBUTE UUID",
                    "qty": QTY
                },
                ...
            ]
        """
        for order_line in order_lines:
            # If one order line fails we don't want to scrap the whole thing, so log the error and move on
            try:
                self.process_order_line(order_line)
            except Exception as error:
                self.log_exception_message(
                    f"Unexpected error importing order line: {order_line} | Error: {error}"
                )

    def process_order_line(self, order_line):
        # Get the product template record for the system
        product_template = self.env["product.template"].get_by_uuid(order_line.get("product_id"))
        if not product_template:
            # TODO: handle this
            pass

        # Core order line values that always need to be written to the record
        order_line_data = {
            "uuid": order_line.get("uuid", 0),
            "product_uom_qty": order_line.get("qty", 0),
            "product_uom": (
                product_template.uom_id.id
                if product_template.uom_id
                else self.env.ref("uom.product_uom_unit").id
            ),
            "price_unit": order_line.get("price_unit", 0),
        }

        # If we have a configuration, then it's a system
        if configuration := order_line.get("configuration"):
            self.process_system_order_line(product_template, order_line_data, configuration)

        # If we don't have a configuration, then it's a component
        else:
            # Try to get the default product variant
            product_product = product_template.product_variant_id
            # If it doesn't exist then create one
            if not product_product:
                product_product = self.env["product.product"].create({"product_tmpl_id": product_template.id})
            order_line_data["product_id"] = product_product.id
            # Write the order line to the sale order
            self.write({"order_line": [(0, 0, order_line_data)]})

    def process_system_order_line(self, product_template, order_line_data, configuration):
        # TODO: This functionality will break if the user gives a component qty value that is not in the defined
        # range. We need to do something about this.
        # Get the attribute dict for the given configuration
        attribute_dict = self.build_attribute_dict(configuration)
        # Setup the product configuration wizard. This is essentially exactly what a user would do to configure
        # a system through the UI
        wizard_action = self.action_config_start()
        wizard_model = self.env[wizard_action["res_model"]]
        wizard_context = wizard_action.get("context", {})
        wizard = wizard_model.with_context(**wizard_context).create(
            {
                "product_tmpl_id": product_template.id,
            }
        )
        # When the wizard is created above it auto generates default product.config.session.value.qty (PVSVQ)
        # objects to represent the attributes that have a required quantity. This is a problem since we will add
        # all quantities with the attribute_dict that was created above and this will cause duplicate PCSVQ
        # records to be created. To remedy this problem, we will manually delete all PCSVQ objects from the
        # config session before we write our values.
        # See update_session_configuration_value in the product_configurator_mrp_quantity module for more info.
        wizard.config_session_id.session_value_quantity_ids.unlink()
        # Write the product configuration to the wizard
        wizard.write(attribute_dict)
        # Set the wizard as done which triggeres a whole bunch of logic behind the scenes.
        # We pass the order line data through the context so that we can make use of it in
        # _get_order_line_vals to set other values of the order line.
        wizard.with_context(graphql_order_line_data=order_line_data).action_config_done()

    def build_attribute_dict(self, configuration):
        """
        Builds an attribute dict with the given configuration to be used with the product configuration wizard.
        Will return a configuration dict that looks like...
            {
                "__attribute_10": 15,
                "__qty_10": 2,
                ...
            }
        ...where 10 is the id of a product.attribute record, 15 is the id of a product.attribute.value record
        and 2 is the quantity of the product specified in the __attribute_ line with the same id. Not all attributes
        will have a quantity specified, only those that are marked `is_qty_required`.
        """
        attribute_dict = {}
        for selection in configuration:
            product_attribute = self.env["product.attribute"].get_by_uuid(selection.get("option"))
            component = self.env["product.template"].get_by_uuid(selection.get("product"))
            pav = self.env["product.attribute.value"].search(
                [
                    ("attribute_id", "=", product_attribute.id),
                    ("product_id", "in", component.product_variant_ids.ids),
                ]
            )
            attribute_dict[f"__attribute_{product_attribute.id}"] = pav.id
            if qty := selection.get("qty", False):
                attribute_dict[f"__qty_{product_attribute.id}"] = qty
        return attribute_dict

    def has_import_tax_difference_holds(self):
        # Helper function to check if the tax import difference exception is active on the given sale order
        exception_id = self.env.ref("ol_graphql_sale.order_import_tax_difference")
        return exception_id in self.exception_ids

    def _post_graphql_create_actions(self, **kwargs):
        """
        We add some decoding-like functionality after the SO creation to handle
        things like taxes and holds. More might be added here in the future.
        """

        try:
            # Lang is set on the related partner of the sale order. If we recieve a malformed lang code then default to
            # "en_US". If we recieve a code that is different than what the partner currently has then change it.
            active_languages = self.env["res.lang"].get_installed()
            active_languages = [l[0] for l in active_languages]
            decoded_lang = kwargs.get("locale", False)
            if decoded_lang not in active_languages:
                decoded_lang = "en_US"
            if self.partner_id.lang != decoded_lang:
                self.partner_id.lang = decoded_lang
            # Make sure the taxes are recomputed and set properly
            # Make sure the sale order is in the correct state and all appropriate actions are called
            # Do checks and add exceptions (see odoo 13 version of this function for what we do today)
            # Finish stripe transactions if necessary

        except OperationalError as operational_error:
            # For typical transaction serialization errors we don't want to log the error
            # as these errors will be handled by the `queue.job`
            if operational_error.pgcode not in PG_CONCURRENCY_ERRORS_TO_RETRY:
                # Add special log entry
                self.log_exception_message(
                    "SO Post GraphQL Create Actions | Can't process action. Non standard operational "
                    f"error: {operational_error.pgcode}. Error: `{operational_error}`",
                    company=self.env.company.short_name.upper(),
                )
                raise

            self.log_warning_message(
                "SO Post GraphQL Create Actions | could not process action as a result of an Odoo"
                f" Concurrency error: {tools.ustr(operational_error.pgerror, errors='replace')} | Record: {self}",
                company=self.env.company.short_name.upper(),
            )

            raise RetryableJobError(
                "GraphQL Mutation Error | SO Post GraphQL Create Actions | Cant't process action. Odoo Concurrency error:"
                f" `{tools.ustr(operational_error.pgerror, errors='replace')}`. Error:"
                f" `{operational_error}` | Company: {self.env.company.short_name.upper()}",
                seconds=2,
            ) from operational_error
        except Exception as e:
            msg = (
                "An unexpected error ocurred during the Sale Order `Post GraphQL Create Actions`:"
                f"| Sale Order: {self.name}({self.id}) "
                f"| Payment Method: {self.payment_method_id.name} ({self.payment_method_id.id})"
                f"| Company: {self.env.company.short_name.upper()}"
                f"| Error: {e}"
            )
            self.env.ref("ls_graphql_sale.order_import_valid_check").create_hold(self, custom_msg=msg)

        return super()._post_graphql_create_actions()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def get_configuration(self):
        """
        Build a list of configuration tuples that contain product.template.attribute.value records matched with
        the associated product.product.attribute.value.qty record (if there is one)
        """

        ptav_ppavq_tuples = self.get_configuration_ptav_ppavq_tuples()
        configuration = []
        for ptav, ppavq in ptav_ppavq_tuples:
            configuration.append(
                {
                    "sku": ptav.product_attribute_value_id.product_id.default_code or None,
                    "product": ptav.product_attribute_value_id.product_id.uuid or None,
                    "option": ptav.attribute_id.uuid or None,
                    "qty": ppavq.qty or 1,
                }
            )
        return configuration

    def get_configuration_ptav_ppavq_tuples(self):
        """
        Get the `product.template.attribute.value` and `product.product.attribute.value.qty` tuples for the configuration
        """
        ptavs = self.product_id.product_template_variant_value_ids
        ppavqs = self.product_id.product_attribute_value_qty_ids
        configuration = []
        for ptav in ptavs:
            ppavq = ppavqs.filtered(lambda x: x.attr_value_id == ptav.product_attribute_value_id)
            configuration.append((ptav, ppavq))

        return [c for c in configuration]


class ProductConfiguratorSale(models.TransientModel):
    _inherit = "product.configurator.sale"

    def _get_order_line_vals(self, product_id):
        # Add additional values to order lines created with the product configurator wizard during graphql ingestion
        res = super(ProductConfiguratorSale, self)._get_order_line_vals(product_id)
        if order_line_data := self.env.context.get("graphql_order_line_data"):
            res.update(order_line_data)
        return res
