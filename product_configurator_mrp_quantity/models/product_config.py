from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    session_value_quantity_ids = fields.One2many(
        "product.config.session.value.qty", "session_id", string="Quantities"
    )
    # Helper Field for Fetch Values while Default Values set on Qty Attribute
    default_qty_ids = fields.Many2many(
        "product.attribute.value",
        string="",
        help="It a hidden Field which help to fatch value when we set default_val in PTAL",
    )

    @api.model
    def search_variant(self, value_ids=None, product_tmpl_id=None):
        products = super().search_variant(
            value_ids=value_ids, product_tmpl_id=product_tmpl_id
        )
        session_attrs_qtys = self.session_value_quantity_ids
        duplicate_product = self.env["product.product"]
        for product in products:
            attribute_value_qty_ids = session_attrs_qtys.mapped(
                "attribute_value_qty_id"
            )
            if not attribute_value_qty_ids:
                duplicate_product = product
            else:
                for value_qty in attribute_value_qty_ids:
                    if product.product_attribute_value_qty_ids.filtered(
                        lambda x: x.attribute_value_qty_id.id == value_qty.id
                    ):
                        duplicate_product = product
                    elif (
                        not duplicate_product
                        and value_qty.id
                        not in product.product_attribute_value_qty_ids.mapped(
                            "attribute_value_qty_id"
                        ).ids
                    ):
                        duplicate_product = self.env["product.product"]
        return duplicate_product

    def create_get_variant(self, value_ids=None, custom_vals=None):
        result = super().create_get_variant(
            value_ids=value_ids, custom_vals=custom_vals
        )
        if self.session_value_quantity_ids and result.id != self.product_id.id:
            # result.product_attribute_value_qty_ids.unlink()
            self.env.cr.execute(
                "delete from product_product_attribute_value_qty where product_id=%s",
                (result.id,),
            )
            qty_attr_obj = self.env["product.product.attribute.value.qty"]
            qty_list = []
            for qty_value in self.session_value_quantity_ids:
                qty_attr_dict = {
                    "product_id": result.id,
                    "attr_value_id": qty_value.attr_value_id.id,
                    "qty": qty_value.qty,
                    "attribute_value_qty_id": qty_value.attribute_value_qty_id.id,
                }
                qty_list.append(qty_attr_dict)
            qty_attr_obj.create(qty_list)
        return result

    @api.model
    def get_variant_vals(self, value_ids=None, custom_vals=None, **kwargs):
        values = super().get_variant_vals(value_ids=value_ids, custom_vals=custom_vals)
        attrs_value_qty_list = []
        for attr_qty in self.session_value_quantity_ids:
            attrs_value_qty_list.append(
                (
                    0,
                    0,
                    {
                        "attr_value_id": attr_qty.attr_value_id.id,
                        "qty": int(attr_qty.qty),
                    },
                )
            )
        values.update({"product_attribute_value_qty_ids": attrs_value_qty_list})
        return values

    @api.model_create_multi
    def create(self, vals_list):
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        attribute_value_qty_obj2 = self.env["product.template.attribute.value"]
        for val in vals_list:
            product_tmpl = (
                self.env["product.template"].browse(val.get("product_tmpl_id")).exists()
            )
            session_qty_list = []
            if product_tmpl:
                default_val_ids = product_tmpl.attribute_line_ids.filtered(
                    lambda line: line.default_val and line.is_qty_required
                )
                default_qty_ids = default_val_ids.default_val
                for line in default_val_ids:
                    template_attribute_value2 = attribute_value_qty_obj2.search(
                        [
                            ("product_tmpl_id", "=", product_tmpl.id),
                            ("attribute_id", "=", line.attribute_id.id),
                            ("product_attribute_value_id", "=", line.default_val.id),
                        ]
                    )

                    template_attribute_value = attribute_value_qty_obj.search(
                        [
                            ("product_tmpl_id", "=", product_tmpl.id),
                            ("product_attribute_id", "=", line.attribute_id.id),
                            ("product_attribute_value_id", "=", line.default_val.id),
                            ("qty", "=", int(template_attribute_value2.default_qty)),
                        ],
                        order="qty",
                        limit=1,
                    )
                    session_qty_list.append(
                        (
                            0,
                            0,
                            {
                                "product_attribute_id": template_attribute_value.product_attribute_id.id,
                                "attr_value_id": template_attribute_value.product_attribute_value_id.id,
                                "attribute_value_qty_id": template_attribute_value.id,
                                "qty": template_attribute_value.qty,
                            },
                        )
                    )

            # Added Context quantity_val_create which use to bypass Core Vals Creation over Custom vals.
            if not self._context.get("quantity_val_create"):
                val.update(
                    {
                        "session_value_quantity_ids": session_qty_list,
                        "default_qty_ids": [(6, 0, default_qty_ids.ids)],
                    }
                )
        return super().create(vals_list)

    # ============================
    # OVERRIDE Methods
    # ============================

    def update_session_configuration_value(self, vals, product_tmpl_id=None):
        """Update value of configuration and quantities in the session,
        safely handling default values.

        :param: vals: Dictionary of fields(of configution wizard) and values
        :param: product_tmpl_id: record set of preoduct template
        :return: True/False
        """
        self.ensure_one()
        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id

        product_configurator_obj = self.env["product.configurator"]
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        field_prefix = product_configurator_obj._prefixes.get("field_prefix")
        custom_field_prefix = product_configurator_obj._prefixes.get(
            "custom_field_prefix"
        )
        qty_field_prefix = product_configurator_obj._prefixes.get("qty_field")
        custom_val = self.get_custom_value_id()

        attr_val_dict = {}  # line_id → value(s)
        custom_val_dict = {}  # line_id → custom val
        qty_val_list = []  # list of qty dicts

        for attr_line in product_tmpl_id.attribute_line_ids:
            attr_id = attr_line.attribute_id.id
            line_id = attr_line.id

            field_name = f"{field_prefix}{line_id}_{attr_id}"
            custom_field_name = f"{custom_field_prefix}{attr_id}"
            qty_field_name = f"{qty_field_prefix}{line_id}_{attr_id}"

            if (
                field_name not in vals
                and custom_field_name not in vals
                and qty_field_name not in vals
            ):
                continue

            # STANDARD ATTRIBUTE VALUE
            if vals.get(field_name, custom_val.id) != custom_val.id:
                if attr_line.multi and isinstance(vals[field_name], list):
                    if not vals[field_name]:
                        field_val = None
                    else:
                        field_val = []
                        for field_vals in vals[field_name]:
                            if field_vals[0] == 6:
                                field_val += field_vals[2] or []
                            elif field_vals[0] == 4:
                                field_val.append(field_vals[1])
                elif not attr_line.multi and isinstance(vals[field_name], int):
                    field_val = vals[field_name]
                else:
                    raise UserError(
                        _("An error occurred while parsing value for attribute %s")
                        % attr_line.attribute_id.name
                    )

                attr_val_dict[line_id] = field_val

                # REMOVE EXISTING SESSION QTY RECORDS (INCLUDING DEFAULTS)
                if attr_line.is_qty_required:
                    if vals.get(qty_field_name):
                        attribute_value_qty_rec = attribute_value_qty_obj.browse(
                            int(vals[qty_field_name])
                        )

                        # Remove old session records for this attribute line that are not the new value
                        existing_session_attrs = (
                            self.session_value_quantity_ids.filtered(
                                lambda sv: sv.product_attribute_id.id
                                == attr_line.attribute_id.id
                                and sv.attr_value_id.id != field_val
                            )
                        )
                        existing_session_attrs.unlink()

                        # Add the new qty
                        qty_val_list.append(
                            {
                                "product_attribute_id": attr_line.attribute_id.id,
                                "attr_value_id": field_val,
                                "attribute_value_qty_id": attribute_value_qty_rec.id,
                                "qty": attribute_value_qty_rec.qty,
                            }
                        )

                # Clear custom value if switching to standard
                if attr_line.custom:
                    custom_val_dict[line_id] = False

            # CUSTOM ATTRIBUTE VALUE
            elif attr_line.custom:
                val = vals.get(custom_field_name, False)
                if attr_line.attribute_id.custom_type == "binary":
                    val = [{"name": "custom", "datas": vals[custom_field_name]}]
                custom_val_dict[line_id] = val
                attr_val_dict[line_id] = False

            # PURE QTY CHANGE (without changing attribute value)
            elif vals.get(qty_field_name) and attr_line.is_qty_required:
                attribute_value_qty_rec = attribute_value_qty_obj.browse(
                    int(vals[qty_field_name])
                )
                existing_session_attrs = self.session_value_quantity_ids.filtered(
                    lambda sv: sv.product_attribute_id.id == attr_line.attribute_id.id
                    and sv.attr_value_id.id
                    == attribute_value_qty_rec.product_attribute_value_id.id
                    and sv.attribute_value_qty_id.id != attribute_value_qty_rec.id
                )
                existing_session_attrs.write(
                    {
                        "qty": attribute_value_qty_rec.qty,
                        "attribute_value_qty_id": attribute_value_qty_rec.id,
                    }
                )

        # FINALLY UPDATE THE SESSION
        self.update_config(attr_val_dict, custom_val_dict, qty_val_list)

    def update_config(
        self, attr_val_dict=None, custom_val_dict=None, qty_val_dict=None
    ):
        """Update the session object with the given value_ids and custom values.

        Use this method instead of write in order to prevent incompatible
        configurations as this removed duplicate values for the same attribute.

        :param attr_val_dict: Dictionary of the form {
            int (attribute_id): attribute_value_id OR [attribute_value_ids]
        }

        :custom_val_dict: Dictionary of the form {
            int (attribute_id): {
                'value': 'custom val',
                OR
                'attachment_ids': {
                    [{
                        'name': 'attachment name',
                        'datas': base64_encoded_string
                    }]
                }
            }
        }


        """
        if attr_val_dict is None:
            attr_val_dict = {}
        if custom_val_dict is None:
            custom_val_dict = {}
        if qty_val_dict is None:
            qty_val_dict = []

        update_vals = {}
        value_ids = self.value_ids.ids

        # Standard values
        for line_id, vals in attr_val_dict.items():
            line = self.env["product.template.attribute.line"].browse(line_id)
            if not line:
                continue

            # Remove only values that belong to this line
            attr_val_ids = self.value_ids.filtered(
                lambda v: v.id in line.value_ids.ids
            ).ids
            value_ids = list(set(value_ids) - set(attr_val_ids))

            if not vals:
                continue
            if isinstance(vals, list):
                value_ids += vals
            elif isinstance(vals, int):
                value_ids.append(vals)

        if value_ids != self.value_ids.ids:
            update_vals["value_ids"] = [(6, 0, value_ids)]

        # Session qty updates
        if qty_val_dict:
            session_qty_list = []
            for qty_val in qty_val_dict:
                existing_session_ids = self.session_value_quantity_ids.filtered(
                    lambda sv: sv.product_attribute_id.id
                    == qty_val["product_attribute_id"]
                    and sv.attr_value_id.id == qty_val["attr_value_id"]
                    and sv.attribute_value_qty_id.id
                    != qty_val["attribute_value_qty_id"]
                )
                existing_session_ids.unlink()
                session_qty_list.append((0, 0, qty_val))
            update_vals["session_value_quantity_ids"] = session_qty_list

        # Remove existing custom values for these lines
        line_attr_ids = [
            self.env["product.template.attribute.line"].browse(line_id).attribute_id.id
            for line_id in custom_val_dict.keys()
        ]
        self.custom_value_ids.filtered(
            lambda cv: cv.attribute_id.id in line_attr_ids
        ).unlink()

        # Custom values
        if custom_val_dict:
            binary_field_ids = (
                self.env["product.attribute"]
                .search([("id", "in", line_attr_ids), ("custom_type", "=", "binary")])
                .ids
            )
        else:
            binary_field_ids = []

        for line_id, vals in custom_val_dict.items():
            line = self.env["product.template.attribute.line"].browse(line_id)
            attr_id = line.attribute_id.id
            if not vals:
                continue

            if "custom_value_ids" not in update_vals:
                update_vals["custom_value_ids"] = []

            custom_vals = {"attribute_id": attr_id}

            if attr_id in binary_field_ids:
                attachments = [
                    (0, 0, {"name": val.get("name"), "datas": val.get("datas")})
                    for val in vals
                ]
                custom_vals["attachment_ids"] = attachments
            else:
                custom_vals["value"] = vals

            update_vals["custom_value_ids"].append((0, 0, custom_vals))
        self.write(update_vals)

    @api.model
    def get_onchange_specifications(self, model):
        """return onchange specification
        - same functionality by _onchange_spec
        - needed this method because odoo don't add specification for fields
        one2many or many2many there is view-reference(using : tree_view_ref)
        intead of view in that field"""
        model_obj = self.env[model]
        specs = model_obj._onchange_spec()
        for name, field in model_obj._fields.items():
            if field.type not in ["one2many", "many2many"]:
                continue
        return specs

    def _get_bom_line(self, variant, product_tmpl_id):
        """Return bom line values, applying qty multipliers only when there is an explicit session qty match."""
        bom_line_vals = super()._get_bom_line(variant, product_tmpl_id)
        session_qtys = self.session_value_quantity_ids
        parent_bom = self._get_parent_bom(product_tmpl_id)
        attr_values = variant.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id"
        )

        # Case: no parent bom and explicit product in context
        if not parent_bom and self._context.get("product_id"):
            product = self._context.get("product_id")
            sv = session_qtys.filtered(
                lambda s: s.attr_value_id.product_id
                and s.attr_value_id.product_id.id == product.id
            )
            if sv:
                bom_line_vals = {
                    "product_id": product.id,
                    "product_qty": sv[0].qty or 1,
                }
            return bom_line_vals

        # Case: when we have a parent bom and are evaluating a parent bom line
        if parent_bom and self._context.get("parent_bom_line"):
            parent_bom_line = self._context.get("parent_bom_line")

            # If parent bom line has a config_set (configurable set)
            if parent_bom_line.config_set_id:
                for config in parent_bom_line.config_set_id.configuration_ids:
                    # Only consider this config if its values are applicable to the variant
                    if set(config.value_ids.ids).issubset(set(attr_values.ids)):
                        # 1) Try to find a session qty where the attribute value maps to the same product as the parent line
                        local_match = session_qtys.filtered(
                            lambda s: s.attr_value_id.product_id
                            and s.attr_value_id.product_id.id
                            == parent_bom_line.product_id.id
                            and s.attr_value_id.id in config.value_ids.ids
                        )
                        if local_match:
                            qty = local_match[0].qty or 1
                            bom_line_vals = {
                                "product_id": parent_bom_line.product_id.id,
                                "product_qty": parent_bom_line.product_qty * qty,
                            }
                            break  # found definitive match, stop checking configs

                        # 2) Otherwise try to find a non-product (attribute-level) session qty that belongs
                        #    to one of the attributes used by this config and to a value in this config.
                        config_attr_ids = config.value_ids.mapped("attribute_id").ids
                        nonlocal_match = session_qtys.filtered(
                            lambda s: (not s.attr_value_id.product_id)
                            and s.attr_value_id.attribute_id.id in config_attr_ids
                            and s.attr_value_id.id in config.value_ids.ids
                        )
                        if nonlocal_match:
                            qty = nonlocal_match[0].qty or 1
                            bom_line_vals = {
                                "product_id": parent_bom_line.product_id.id,
                                "product_qty": parent_bom_line.product_qty * qty,
                            }
                            break  # found match, stop checking configs

                # if no local_match or nonlocal_match found, leave bom_line_vals unchanged

            else:
                # parent_bom_line has no config_set – check for a direct product match only
                direct_sv = session_qtys.filtered(
                    lambda s: s.attr_value_id.product_id
                    and s.attr_value_id.product_id.id == parent_bom_line.product_id.id
                )
                if direct_sv:
                    qty = direct_sv[0].qty or 1
                    bom_line_vals = {
                        "product_id": parent_bom_line.product_id.id,
                        "product_qty": parent_bom_line.product_qty * qty,
                    }

        return bom_line_vals


class ProductConfigSessionValueQty(models.Model):
    _name = "product.config.session.value.qty"
    _description = """Helper object to store
    the user's choice for any value that has an associated quantity."""

    session_id = fields.Many2one("product.config.session", ondelete="cascade")
    attr_value_id = fields.Many2one("product.attribute.value")
    product_attribute_id = fields.Many2one("product.attribute")
    qty = fields.Integer(string="Quantity")
    attribute_value_qty_id = fields.Many2one("attribute.value.qty", ondelete="cascade")
    template_attri_value_id = fields.Many2one(
        "product.template.attribute.value",
        related="attribute_value_qty_id.template_attri_value_id",
        store=True,
    )
