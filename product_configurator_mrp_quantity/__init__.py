from . import models
from . import wizard


def uninstall_hook(env):
    """Archived product records that have a attribute quantity value set on the product variant."""
    attribute_value_qty_recs = env["product.product.attribute.value.qty"].search(
        [("product_id", "!=", False)]
    )
    product_tmpl_ids = attribute_value_qty_recs.mapped("product_id.product_tmpl_id")
    product_tmpl_ids.write({"active": False})
