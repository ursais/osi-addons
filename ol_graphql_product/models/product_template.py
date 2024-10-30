# Import Python libs
import logging
from datetime import datetime
from collections import namedtuple, defaultdict, OrderedDict

# Import Odoo libs
from odoo import models, fields, api

_logger = logging.getLogger(__name__)
ConfigLineTuple = namedtuple(
    "ConfigLine", ["system_id", "attribute_id", "component_id", "company_id"]
)


class ProductTemplate(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "product.template"
    _inherit = ["product.template", "graphql.mixin"]

    # COLUMNS #####
    lifecycle_launch_date = fields.Date(string="Lifecycle Launch Date")
    lifecycle_status = fields.Selection(
        string="Lifecycle Status",
        selection=[
            ("in_development", "In Development"),
            ("coming_soon", "Coming Soon"),
            ("preorder", "Pre-Order"),
            ("available", "Available"),
            ("discontinued", "Discontinued"),
            ("end_of_life", "End of Life"),
            ("canceled", "Canceled"),
        ],
        company_dependent=True,
    )
    public_destination = fields.Char(
        string="Public Destination",
        selection=[
            ("not_public", "Not Public"),
            ("b2b", "B2B"),
            ("b2c", "B2C"),
            ("b2b_b2c", "B2B + B2C"),
        ],
    )
    # END #########

    def get_related_res_company(self):
        """
        Get the `res.company` value for this product
        """
        # As `company_ids` could be an empty record set we need to make sure we return the correct value
        # `company_ids` could also be an recordset of multiple companies, in this case we just choose the first one
        companies = self.company_ids.exists().sorted(key=lambda c: c.id)
        return companies[0] if companies else self.env["res.company"]

    def get_graphql_placeholder_values(
        self, message_field=False, message_values=False, transaction_id=False
    ):
        base_values = super().get_graphql_placeholder_values(
            message_field=message_field
        )
        # Merge the super and customer specific values
        base_values.update(
            {
                "company_id": False,
                "default_code": f'PENDING-{self.env.context.get("transaction_id", datetime.now())}',
            }
        )
        return base_values

    def get_encoded_options(self):
        """
        Encode the configurable systems options
        """
        # TODO: This needs to be reworked with the new product strucutre
        return
        options = []
        for line in self.attribute_line_ids:
            # Add all of the options and their selections
            selection_dict = defaultdict(dict)
            for value in line.product_template_value_ids:
                component = value.product_attribute_value_id.product_id
                selection_dict[component.uuid]["uuid"] = component.uuid
                if self.env.context.get("encode_full_product_configuration"):
                    selection_dict[component.uuid].update(
                        {
                            "default_qty": value.default_qty,
                            "max_qty": value.maximum_qty,
                            "visible_to_user": value.product_attribute_value_id.visible_to_user,
                        }
                    )
                    if selection_dict[component.uuid].get("is_default"):
                        selection_dict[component.uuid]["is_default"].append(
                            {
                                "onlogic_company": value.company_id.short_name,
                                "value": value.is_default,
                            },
                        )
                    else:
                        selection_dict[component.uuid]["is_default"] = [
                            {
                                "onlogic_company": value.company_id.short_name,
                                "value": value.is_default,
                            }
                        ]

                    if selection_dict[component.uuid].get("enabled"):
                        selection_dict[component.uuid]["enabled"].append(
                            {
                                "onlogic_company": value.company_id.short_name,
                                "value": value.ptav_active,
                            },
                        )
                    else:
                        selection_dict[component.uuid]["enabled"] = [
                            {
                                "onlogic_company": value.company_id.short_name,
                                "value": value.ptav_active,
                            }
                        ]
            selections = []
            onlogic_companies = self.env["res.company"].get_all()
            # Turn the dictionary back into a list
            # also add any possible missing company dependent data information
            # This could happen if the PTAV doesn't exist in a given company
            for selection in selection_dict.values():
                for field_name in ["is_default", "enabled"]:
                    field_values = selection.get(field_name, [])
                    for onlogic_company in onlogic_companies:
                        company_field_value = [
                            x
                            for x in field_values
                            if x.get("onlogic_company", False)
                            == onlogic_company.short_name.lower()
                        ]
                        if not company_field_value:
                            field_values.append(
                                {
                                    "onlogic_company": onlogic_company.short_name.lower(),
                                    "value": None,
                                }
                            )
                selections.append(selection)
            options.append(
                {
                    "uuid": line.attribute_id.uuid,
                    "classification": line.attribute_id.classification_id.uuid,
                    "name": line.attribute_id.name,
                    "selections": selections,
                    "required": line.required,
                    "position": line.sequence,
                }
            )
        return options

    def get_public_attachment(self, field_name, datas=False):
        """
        Ensure that Tier 1/2 Systems use their parent portfolio system images
        """
        if (
            self.has_configurable_attributes
            and self.system_tier != "normal"
            and self.pim_parent_portfolio_system
        ):
            # This is a Tier 1 or Tier 2 system that has a parent portfolio system
            # use `self.pim_parent_portfolio_system` instead of self
            return super(
                ProductTemplate, self.pim_parent_portfolio_system
            ).get_public_attachment(field_name=field_name, datas=datas)
        # Return Super
        return super().get_public_attachment(field_name=field_name, datas=datas)

    def get_public_image_src(self, field_name):
        """
        Ensure that Tier 1/2 Systems use their parent portfolio system images
        """
        if (
            self.has_configurable_attributes
            and self.system_tier != "normal"
            and self.pim_parent_portfolio_system
        ):
            # This is a Tier 1 or Tier 2 system that has a parent portfolio system
            # use `self.pim_parent_portfolio_system` instead of self
            return super(
                ProductTemplate, self.pim_parent_portfolio_system
            ).get_public_image_src(field_name=field_name)
        # Return Super
        return super().get_public_image_src(field_name=field_name)
