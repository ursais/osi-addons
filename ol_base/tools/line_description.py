# Method to be used across several objects to generate the line description
# based on the attribute visibility settings.


def get_product_description(product):
    """
    Generate the description based on product's attribute values
    and their corresponding attribute lines.
    """
    description = product.name

    # Check if the product has template attribute values
    if product.product_template_attribute_value_ids:
        for attribute_value in product.product_template_attribute_value_ids:
            # Retrieve the attribute line for the current attribute value
            attribute_line = product.product_tmpl_id.attribute_line_ids.filtered(
                lambda line: line.attribute_id == attribute_value.attribute_id
            )

            # If 'used_in_sale_description' is True, add attribute to description
            if attribute_line and attribute_line.used_in_sale_description:
                description += "\n  " + attribute_value.display_name

    return description
