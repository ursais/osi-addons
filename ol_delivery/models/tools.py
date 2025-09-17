# Import Odoo libs
from odoo.exceptions import ValidationError


def get_product_data_from_order_lines_data(env, company, order_lines_data):

    # Use the given company or fall back to the environment's company
    company = company or env.company

    total_weight = 0
    total_volume = 0
    total_price = 0
    total_cost = 0
    total_qty = 0
    total_shipping_buffer = 0
    extended_order_line_data = {}

    def calculate_volume(length, width, height, volume):
        if length and width and height:
            # If a component has all of its dimensions set
            # we calculate the volume from those
            final_volume = (length * width * height) / 1000000
        else:
            # Otherwise we use the volume set on the product
            final_volume = volume

        return final_volume or 0.0

    def get_product_data(company, product_uuids):
        # Get the basic data for the product via a direct query
        query = """
        SELECT
            pt.id,
            pt.default_code AS "sku",
            pt.uuid,
            pt.default_code,
            pt."weight_dummy" AS "weight",
            pt.height AS "height",
            pt.length AS "length",
            pt.width AS "width",
            pt.volume AS "volume",
            sb_ip.value_integer AS shipping_buffer,
            lp_ip.value_float AS "price",
            sp_ip.value_float AS "cost"
        FROM
            product_template pt
        LEFT JOIN product_product pp ON
            pp.product_tmpl_id = pt.id
            AND pt.has_configurable_attributes = FALSE
        LEFT JOIN ir_property sb_ip ON
            sb_ip.res_id = 'product.template,' || pt.id
            AND sb_ip."name" = 'shipping_buffer'
            AND sb_ip.company_id = %(company_id)s
        LEFT JOIN ir_property lp_ip ON
            lp_ip.res_id = 'product.template,' || pt.id
            AND lp_ip."name" = 'list_price'
            AND lp_ip.company_id = %(company_id)s
        LEFT JOIN ir_property sp_ip ON
            sp_ip.res_id = 'product.product,' || pp.id
            AND sp_ip."name" = 'standard_price'
            AND sp_ip.company_id = %(company_id)s
        WHERE
            pt."uuid" IN %(product_uuids)s
            """

        query_args = {"product_uuids": tuple(product_uuids), "company_id": company.id}
        env.cr.execute(query, query_args)
        return {str(r.get("uuid")): r for r in env.cr.dictfetchall()}

    def get_product_uuids():
        product_uuids = []
        for order_line_data in order_lines_data:
            product_uuids.append(order_line_data.get("product_id"))
            product_uuids += [
                x.get("product")
                for x in order_line_data.get("configuration", [])
                if x.get("product")
            ]
        return list(set(product_uuids))

    product_uuids = get_product_uuids()

    if not product_uuids:
        return {
            "total_qty": total_qty,
            "total_weight": round(total_weight, 4),
            "total_volume": total_volume,
            "total_price": total_price,
            "total_cost": total_cost,
            "total_shipping_buffer": total_shipping_buffer,
            "order_lines": extended_order_line_data,
        }

    products_data = get_product_data(company=company, product_uuids=product_uuids)

    """
    There are a few different cases this function needs to handle:

    1. Components: plain jane components. No special processing is needed since all of the fields we care about
       live on the product itself.

    2. Phantom Kits: Weight, cost, and price is compiled from the components onto the main phantom kit product.
       For shipping purposes we do not need to know about the BOM of the phantom kit since all the fields we
       care about are on the phantom kit product directly.

    3. Systems (w/ or w/o Phantom Kits): Systems have configurations which we dissect into component level detail.
       For our purposes we can treat any phantom kits into the configuration as components (see #2).
    """

    for order_line_data in order_lines_data:

        # Set the defaults
        product_uuid = order_line_data.get("product_id", False)
        product_data = products_data.get(product_uuid)
        if not product_data:
            raise ValidationError(f"Product with UUID {product_uuid} not found!")
        line_qty = order_line_data.get("qty") or 1
        line_price = (order_line_data.get("price") or 0) * line_qty

        line_data = {
            "id": product_data.get("id"),
            "uuid": product_uuid,
            "sku": product_data.get("sku"),
            "qty": line_qty,
            "price": line_price,
        }
        # ======== SYSTEMS ========
        if configuration := order_line_data.get("configuration"):
            # Iterate over the components
            line_weight = 0
            line_volume = 0
            line_shipping_buffer = 0
            line_cost = 0
            line_system_configuration = {}

            product_uuids = [
                c.get("product") for c in configuration if c.get("product")
            ]
            products_data = get_product_data(company, product_uuids)

            for configuration_line in configuration:

                # Get the UUID of the component
                component_uuid = configuration_line.get("product")

                if not component_uuid:
                    continue

                # Get the data for the component based on the UUID
                component_data = products_data.get(component_uuid)

                component_id = component_data.get("id")
                component_sku = component_data.get("sku") or "n/a"
                component_shipping_buffer = component_data.get("shipping_buffer") or 0
                component_length = component_data.get("length") or 0.0
                component_width = component_data.get("width") or 0.0
                component_height = component_data.get("height") or 0.0
                component_volume = component_data.get("volume") or 0.0
                component_weight = component_data.get("weight") or 0.0
                component_qty = configuration_line.get("qty") or 1
                component_price = configuration_line.get("price") or 0.0
                component_cost = component_data.get("cost") or 0.0
                product_attribute_uuid = configuration_line.get("option", False)

                # Line Volume calculation
                component_volume = calculate_volume(
                    length=component_length,
                    width=component_width,
                    height=component_height,
                    volume=component_volume,
                )

                if component_volume > line_volume:
                    # We only care about the biggest component
                    line_volume = component_volume

                # Line Shipping Buffer calculation
                if component_shipping_buffer > line_shipping_buffer:
                    # We only care about the biggest shipping buffer
                    line_shipping_buffer = component_shipping_buffer

                # Line Weight calculation
                line_weight += component_weight * component_qty
                line_cost += component_cost * component_qty

                line_system_configuration[component_uuid] = {
                    "id": component_id,
                    "sku": component_sku,
                    "uuid": product_uuid,
                    "product_attribute_uuid": product_attribute_uuid,
                    "qty": component_qty,
                    "weight": component_weight,
                    "length": component_length,
                    "width": component_width,
                    "height": component_height,
                    "volume": component_volume,
                    "price": component_price,
                    "cost": component_cost,
                    "shipping_buffer": component_shipping_buffer,
                }

            line_weight *= line_qty
            line_volume *= line_qty
            line_cost *= line_qty

            line_data.update(
                {
                    "weight": line_weight,
                    "length": None,
                    "width": None,
                    "height": None,
                    "volume": line_volume,
                    "cost": line_cost,
                    "shipping_buffer": line_shipping_buffer,
                    "configuration": line_system_configuration,
                }
            )
        # ======== COMPONENTS ========
        else:
            line_weight = product_data.get("weight") * line_qty
            line_volume = (
                calculate_volume(
                    length=product_data.get("length", 0.0),
                    width=product_data.get("width", 0.0),
                    height=product_data.get("height", 0.0),
                    volume=product_data.get("volume", 0.0),
                )
                * line_qty
            )
            line_shipping_buffer = product_data.get("shipping_buffer") or 0
            line_cost = (product_data.get("cost") or 0) * line_qty

            line_data.update(
                {
                    "weight": line_weight,
                    "length": product_data.get("length"),
                    "width": product_data.get("width"),
                    "height": product_data.get("height"),
                    "volume": line_volume,
                    "cost": line_cost,
                    "shipping_buffer": line_shipping_buffer,
                }
            )

        total_qty += line_qty
        total_weight += line_weight
        total_volume += line_volume
        total_price += line_price
        total_cost += line_cost
        if line_shipping_buffer > total_shipping_buffer:
            total_shipping_buffer = line_shipping_buffer

        extended_order_line_data[product_uuid] = line_data

    if company.use_delivery_uplift:
        # Uplift the total values if necessary
        total_weight = total_weight * ((company.delivery_weight_uplift / 100.0) + 1)
        total_volume = total_volume * ((company.delivery_dimension_uplift / 100.0) + 1)

    # We want to set a minimum volume
    total_volume = max((company.minimum_volume or 0.0), total_volume)

    result = {
        "total_qty": total_qty or 0,
        "total_weight": round(total_weight or 0.0, 4),
        "total_volume": total_volume or 0.0,
        "total_price": total_price or 0.0,
        "total_cost": total_cost or 0.0,
        "total_shipping_buffer": total_shipping_buffer or 0,
        "order_lines": extended_order_line_data,
    }

    return result
