# Import Python libs
import logging
from datetime import datetime
from collections import namedtuple, defaultdict, OrderedDict

# Import Odoo libs
from odoo import models, fields, api
from odoo.addons.ol_graphql.tools import get_translated_field_values
from odoo.addons.ol_base.fields.fields import JsonField

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """
    Add GraphQL compatibility
    """

    _name = "product.template"
    _inherit = ["product.template", "graphql.mixin"]

    pim_latest_message = JsonField(string="Latest PIM Message", readonly=True, copy=False)
    pricing_latest_message = JsonField(string="Latest Pricing Message", readonly=True, copy=False)


    def get_encoded_options(self):
        """
        Encode the configurable systems options
        """
        options = []
        onlogic_companies = self.env["res.company"].get_all()
        for line in self.attribute_line_ids:
            # Add all of the options and their selections
            selection_dict = defaultdict(dict)
            # Within each product template attribute line, iterate over each ptav
            for value in line.product_template_value_ids:
                component = value.product_attribute_value_id.product_id
                selection_dict[component.uuid]["uuid"] = component.uuid
                if self.env.context.get("encode_full_product_configuration"):
                    selection_dict[component.uuid].update(
                        {
                            "default_qty": value.default_qty,
                            "max_qty": value.maximum_qty,
                            "visible_to_user": value.visible_to_user,
                            "is_user_defined_qty": value.attribute_line_id.is_qty_required,
                            "sequence": value.product_attribute_value_id.sequence,
                            "is_default": False,
                        }
                    )
                    for company in onlogic_companies:
                        enabled = company in value.company_ids
                        selection_dict[component.uuid].setdefault("enabled", []).append(
                            {
                                "onlogic_company": company.short_name.lower(),
                                "value": enabled,
                            }
                        )

            if self.env.context.get("encode_full_product_configuration"):
                if line.default_val and line.default_val.product_id:
                    default_uuid = line.default_val.product_id.uuid
                    selection_dict[default_uuid]["is_default"] = True

            # Turn the dictionary back into a list
            selections = [selection for selection in selection_dict.values()]

            options.append(
                {
                    "uuid": line.attribute_id.uuid,
                    "classification": line.attribute_id.classification_id.uuid or None,
                    "name": get_translated_field_values(
                        odoo_record=line.attribute_id,
                        field="name",
                    ),
                    "classification_name": get_translated_field_values(
                        odoo_record=line.attribute_id.classification_id,
                        field="name",
                    ),
                    "selections": selections,
                    "required": line.required,
                    "sequence": line.sequence,
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
