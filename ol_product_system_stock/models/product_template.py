# Import Python libs
import logging
from datetime import datetime

# Import Odoo libs
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Additions and overrides to templates to support product configuration
    """

    _inherit = "product.template"

    # COLUMNS #####
    system_stock_state = fields.Selection(
        string="System Stock State",
        selection=[
            ("has_default_config_in_stock", "Has Default In Stock"),
            ("has_any_config_in_stock", "Has Any Config In Stock"),
            ("out_of_stock", "Out Of Stock"),
        ],
        company_dependent=True,
        help=(
            "Programmatically set field that is mostly used outside of Odoo to carry high level system stock"
            " information."
        ),
    )
    website_system_stock_state = fields.Selection(
        string="Website System Stock State",
        selection=[
            ("has_default_config_in_stock", "Has Default In Stock"),
            ("has_any_config_in_stock", "Has Any Config In Stock"),
            ("out_of_stock", "Out Of Stock"),
        ],
        company_dependent=True,
        help=(
            "Calculated based on components that have `Public Destination` set to `b2c` Programmatically set field that is mostly used outside of Odoo to carry high level system stock"
            " information."
        ),
    )
    # END #########

    def product_stock_queue_trigger(self):
        """
        Method to handle events that need to add a new item to the product.stock.queue
        """
        self.env["product.stock.queue"].add_new(self.mapped("product_variant_id"))

    def stock_quantity_changed(self):
        """
        Add System Stock Queue items for Components where the stock changed
        """

    def system_stock_quantity_changed(self):
        """
        This function is intended to be overridden in later modules
        """

    def manual_update_system_stock_state(self):
        """
        Manually refresh the system stock for this product and show a view with the results
        """
        html_data = ""
        onlogic_companies = self.env["res.company"].get_all().sorted(key=lambda c: c.id)
        for company in onlogic_companies:
            if not self.company_ids_display or company in self.company_ids_display:
                env = api.Environment(self.env.cr, company.company_user_id.id, {})
                _, data = (
                    env["product.template"]
                    .browse(self.id)
                    .with_context(manual_update_system_stock_state=True)
                    .update_system_stock_state()
                )
                html_data += f"{data}<hr/>"
        self.system_stock_quantity_changed()

        return {
            "type": "ir.actions.act_window",
            "name": "System Stock Status Results",
            "res_model": "system.stock.status.result.wizard",
            "view_type": "form",
            "view_mode": "form",
            "view_id": [
                self.env.ref(
                    "ol_product_system_stock.view_system_stock_status_result_wizard"
                ).id
            ],
            "context": {"system_stock_status_results": html_data},
            "target": "new",
        }

    def update_system_stock_state(self):
        generic_updated_portfolios, generic_data = self.set_system_stock_state(
            for_website_facing_products=False
        )
        public_updated_portfolios, public_data = self.set_system_stock_state(
            for_website_facing_products=True
        )
        updated_portfolios = generic_updated_portfolios | public_updated_portfolios
        data = f"{generic_data}<br/><hr/><br/>{public_data}"
        return updated_portfolios, data

    def set_system_stock_state(self, for_website_facing_products=False):
        """
        Update the given systems `system_stock_state` field
        """

        def valid_website_facing_component(component, is_default, pav):
            """
            Check if the component is valid based on it's Public Destination field
            """
            if not for_website_facing_products:
                # No need to check or return any information
                # if we are not calculating for customer facing
                return True, ""

            if component.public_destination not in ["b2c", "b2b_b2c"]:
                # For website related products we need to make sure the Public Destination is correct
                return False, f"No, Not Public ({component.public_destination})"

            """
            If a component is a default selection we don't care if it is visible or not
                It is still needed to determine if we can build the system
            If a component is NOT a default selection we DO care if it is visible or not.
                If it is visible it can still be selected to build the system, if not it can't
            """
            if is_default:
                return True, "Yes, Public + Default"

            if not pav.visible_to_user:
                return False, "No, Not Visible"

            return True, "Yes, Public + Visible"

        self.env.invalidate_all()

        updated_systems = self.env["product.template"]

        # Do bulk reads to make load values into cache
        # this dramatically speeds up the function speed
        all_pavs = self.mapped(
            "attribute_line_ids.product_template_value_ids.product_attribute_value_id"
        )
        all_pavs.read(["company_ids", "product_id"])
        all_components = all_pavs.mapped("product_id")
        all_components.with_company(self.env.company.id).read(
            ["qty_available", "has_configurable_attributes", "type"]
        )

        data = ""
        for system in self:
            system_header = f"<h2><strong>{'WEBSITE | ' if for_website_facing_products else ''}[{self.env.company.short_name.upper()}] {system.default_code}</strong></h2><br/>"
            system_data = ""
            try:
                has_default_config_in_stock = True
                has_any_config_in_stock = True

                for ptal in system.attribute_line_ids:
                    system_data += f"<h5>{ptal.attribute_id.name}</h5>"

                    if not ptal.required:
                        # We only care about required options\
                        system_data += "<ul><li>Not Required Option</ul></li>"
                        continue

                    option_selection_stock_states = []
                    system_data += f' <table class="table table-bordered"> <thead> <tr> <th>SKU</th> <th>Is Default</th> <th>In Stock</th> {"<th>Valid for Website</th>" if for_website_facing_products else ""} </tr> </thead> <tbody> '
                    has_default_ptav = False
                    for ptav in ptal.product_template_value_ids:
                        # These are each a product.template.attribute.value a.k.a Selections or SKUs in relations
                        if (
                            ptav.company_ids
                            and self.env.company not in ptav.company_ids
                        ):
                            # Skip PTAV's for different companies
                            continue

                        if not ptav.ptav_active:
                            continue

                        component = ptav.product_attribute_value_id.product_id
                        if not component:
                            # Skip PTAV's that don't have a product.product
                            # These are usually the remainder `None` values
                            continue

                        is_default = ptav.product_attribute_value_id == ptal.default_val

                        # Check if the Component is valid for this System Stock calculation
                        # this is mainly used for `website_system_stock_state`
                        (
                            is_valid_website_facing_component,
                            website_facing_validation_info,
                        ) = valid_website_facing_component(
                            component, is_default, ptav.product_attribute_value_id
                        )

                        if not component.is_stockable():
                            # Product should not have stock values, so for simplicity we mark it as in stock
                            component_in_stock = True
                            system_data += (
                                f"<tr>"
                                f"<td>{component.default_code:<30}</td>"
                                f"<td>{is_default}</td>"
                                f"<td>Not Stockable</td>"
                                f"{f'<td>{website_facing_validation_info}</td>' if for_website_facing_products else ''}"
                                "</tr> "
                            )
                        else:
                            component_in_stock = component.qty_available > 0
                            system_data += (
                                f"<tr>"
                                f"<td>{component.default_code:<30}</td>"
                                f"<td>{is_default}</td>"
                                f"<td>{component_in_stock}</td>"
                                f"{f'<td>{website_facing_validation_info}</td>' if for_website_facing_products else ''}"
                                "</tr> "
                            )

                        eligible_component_stock = (
                            is_valid_website_facing_component and component_in_stock
                        )
                        if (
                            has_default_config_in_stock
                            and is_default
                            and not eligible_component_stock
                        ):
                            # All other options until now had their default selection in stock and
                            # This is a default selection that is out of stock
                            has_default_config_in_stock = False

                        option_selection_stock_states.append(eligible_component_stock)
                        if is_default and is_valid_website_facing_component:
                            has_default_ptav = True

                    system_data += "</tbody></table>"

                    if not has_default_ptav:
                        # If an Option has no default Selection set
                        # we should not mark the System has `has_default_config_in_stock`
                        has_default_config_in_stock = False

                    if has_any_config_in_stock and not any(
                        option_selection_stock_states
                    ):
                        # All other options until now had at least one selection in stock and
                        # This option has none of its selections in stock
                        has_any_config_in_stock = False

                    if (
                        not self.env.context.get(
                            "manual_update_system_stock_state", False
                        )
                        and not has_default_config_in_stock
                        and not has_any_config_in_stock
                    ):
                        # If this is not a manual update (for manual updates we don't want to early return so we have all the `data` to display in the UI)
                        # If we know that neither the default or any other config is in stock,
                        # we can stop looping through the rest of the options
                        break
                if has_default_config_in_stock:
                    system_stock_state = "has_default_config_in_stock"
                elif has_any_config_in_stock:
                    system_stock_state = "has_any_config_in_stock"
                else:
                    system_stock_state = "out_of_stock"

                if for_website_facing_products:
                    system_stock_state_field_name = "website_system_stock_state"
                else:
                    system_stock_state_field_name = "system_stock_state"

                current_system_stock_state = getattr(
                    system.with_company(self.env.company.id),
                    system_stock_state_field_name,
                )

                if current_system_stock_state != system_stock_state:
                    system_data += f"<h3><strong>{'Website ' if for_website_facing_products else ''}System Stock State</strong></h3><ul><li>Changed from `{current_system_stock_state}` to `{system_stock_state}`</ul></li>"
                    system.write({system_stock_state_field_name: system_stock_state})
                    updated_systems |= system
                else:
                    system_data += f"<h3><strong>{'Website ' if for_website_facing_products else ''}System Stock State</strong></h3><ul><li>Unchanged: `{system_stock_state}`</ul></li>"
                system_data += "<br/>"
            except Exception as error:
                _logger.exception(
                    f"Could not update {system.default_code} {'Website ' if for_website_facing_products else ''}System Stock State! | Error: {error}"
                )
                system_data = f"<h3><strong>[{self.env.company.short_name.upper()}] Error updating {system.default_code}'s {'Website ' if for_website_facing_products else ''}System Stock State</strong></h3><br/>Error: {error}<br/>"
            data += system_header + system_data

        return updated_systems, data
