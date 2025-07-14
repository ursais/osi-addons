from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductConfigSession(models.Model):
    _inherit = "product.config.session"

    session_value_quantity_ids = fields.One2many(
        "product.config.session.value.qty", "session_id", string="Quantities"
    )
    #Helper Field for Fetch Values while Default Values set on Qty Attribute
    default_qty_ids = fields.Many2many("product.attribute.value",string="",help="It a hidden Field which help to fatch value when we set default_val in PTAL")

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
            self.env.cr.execute("delete from product_product_attribute_value_qty where product_id=%s", (result.id,))
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
                val.update({"session_value_quantity_ids": session_qty_list,"default_qty_ids":[(6,0,default_qty_ids.ids)]})
        return super().create(vals_list)

    # ============================
    # OVERRIDE Methods
    # ============================

    def update_session_configuration_value(self, vals, product_tmpl_id=None):
        """Update value of configuration in current session

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

        attr_val_dict = {}
        custom_val_dict = {}
        qty_val_dict = {}
        qty_val_list = []
        for attr_line in product_tmpl_id.attribute_line_ids:
            attr_id = attr_line.attribute_id.id
            field_name = field_prefix + str(attr_id)
            custom_field_name = custom_field_prefix + str(attr_id)
            qty_field_name = qty_field_prefix + str(attr_id)

            if (
                field_name not in vals
                and custom_field_name not in vals
                and qty_field_name not in vals
            ):
                continue

            # Add attribute values from the client except custom attribute
            # If a custom value is being written, but field name is not in
            #   the write dictionary, then it must be a custom value!
            # existing_session_attrs_qtys = self.session_value_quantity_ids.filtered(lambda l:l.attr_value_id.attribute_id.id == attr_id and l.qty == int(vals.get(qty_field_name)))
            existing_session_attrs_nonqtys = False
            if vals.get(qty_field_name):
                existing_session_attrs_nonqtys = self.session_value_quantity_ids.filtered(
                    lambda session_value_id: session_value_id.attr_value_id.attribute_id.id
                    == attr_id
                    and session_value_id.qty != int(vals.get(qty_field_name))
                )
            if vals.get(field_name, custom_val.id) != custom_val.id:
                if attr_line.multi and isinstance(vals[field_name], list):
                    if not vals[field_name]:
                        field_val = None
                    else:
                        field_val = []
                        qty_field_val = []
                        for field_vals in vals[field_name]:
                            if field_vals[0] == 6:
                                field_val += field_vals[2] or []
                            elif field_vals[0] == 4:
                                field_val.append(field_vals[1])
                        # field_val = [
                        #     i[1] for i in vals[field_name] if vals[field_name][0]
                        # ] or vals[field_name][0][1]
                elif not attr_line.multi and isinstance(vals[field_name], int):
                    field_val = vals[field_name]

                    if attr_line.is_qty_required and vals.get(qty_field_name):
                        qty_field_val = vals[qty_field_name]
                    if self.session_value_quantity_ids:
                        update_session_ids = self.session_value_quantity_ids.filtered(
                            lambda local_session: local_session.attr_value_id.attribute_id.id
                            == attr_id
                        )
                        for sess in update_session_ids:
                            sess.attr_value_id = field_val
                else:
                    raise UserError(
                        _("An error occurred while parsing value for attribute %s")
                        % attr_line.attribute_id.name
                    )
                attr_val_dict.update({attr_id: field_val})
                if attr_line.is_qty_required and vals.get(qty_field_name):
                    attribute_value_qty_rec = attribute_value_qty_obj.browse(
                        qty_field_val
                    )
                    qty_val_list.append(
                        {
                            "product_attribute_id": attribute_value_qty_rec.product_attribute_id.id,
                            "attr_value_id": attribute_value_qty_rec.product_attribute_value_id.id,
                            "attribute_value_qty_id": attribute_value_qty_rec.id,
                            "qty": attribute_value_qty_rec.qty,
                        }
                    )

                # Ensure there is no custom value stored if we have switched
                # from custom value to selected attribute value.
                if attr_line.custom:
                    custom_val_dict.update({attr_id: False})
            elif attr_line.custom:
                val = vals.get(custom_field_name, False)
                if attr_line.attribute_id.custom_type == "binary":
                    # TODO: Add widget that enables multiple file uploads
                    val = [{"name": "custom", "datas": vals[custom_field_name]}]
                custom_val_dict.update({attr_id: val})
                # Ensure there is no standard value stored if we have switched
                # from selected value to custom value.
                attr_val_dict.update({attr_id: False})

            elif (
                vals.get(qty_field_name)
                and not qty_val_dict
                and attr_line.is_qty_required
            ):
                attribute_value_qty_rec = attribute_value_qty_obj.browse(
                    int(vals.get(qty_field_name))
                )
                existing_session_attrs_nonqtys.write(
                    {
                        "qty": attribute_value_qty_rec.qty,
                        "attribute_value_qty_id": attribute_value_qty_rec.id,
                    }
                )
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
            qty_val_dict = {}
        update_vals = {}

        value_ids = self.value_ids.ids
        for attr_id, vals in attr_val_dict.items():
            attr_val_ids = self.value_ids.filtered(
                lambda value_id: value_id.attribute_id.id == int(attr_id)
            ).ids
            # Remove all values for this attribute and add vals from dict
            value_ids = list(set(value_ids) - set(attr_val_ids))
            if not vals:
                continue
            if isinstance(vals, list):
                value_ids += vals
            elif isinstance(vals, int):
                value_ids.append(vals)

        if value_ids != self.value_ids.ids:
            update_vals.update({"value_ids": [(6, 0, value_ids)]})
        if qty_val_dict:
            session_qty_list = []
            dict_qty = {}
            for qty_val in qty_val_dict:
                existing_session_ids = self.session_value_quantity_ids.filtered(
                    lambda l: l.product_attribute_id.id
                    == qty_val.get("product_attribute_id")
                    and l.attr_value_id.id == qty_val.get("attr_value_id")
                    and l.attribute_value_qty_id.id
                    != qty_val.get("attribute_value_qty_id")
                )
                existing_session_ids.unlink()
                session_qty_list.append((0, 0, qty_val))

            update_vals.update({"session_value_quantity_ids": session_qty_list})
        # Remove all custom values included in the custom_vals dict
        self.custom_value_ids.filtered(
            lambda custom_value_id: custom_value_id.attribute_id.id
            in custom_val_dict.keys()
        ).unlink()

        if custom_val_dict:
            binary_field_ids = (
                self.env["product.attribute"]
                .search(
                    [
                        ("id", "in", list(custom_val_dict.keys())),
                        ("custom_type", "=", "binary"),
                    ]
                )
                .ids
            )
        else:
            binary_field_ids = []

        for attr_id, vals in custom_val_dict.items():
            if not vals:
                continue

            if "custom_value_ids" not in update_vals:
                update_vals["custom_value_ids"] = []

            custom_vals = {"attribute_id": attr_id}

            if attr_id in binary_field_ids:
                attachments = [
                    (
                        0,
                        0,
                        {"name": val.get("name"), "datas": val.get("datas")},
                    )
                    for val in vals
                ]
                custom_vals.update({"attachment_ids": attachments})
            else:
                custom_vals.update({"value": vals})

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
            # ch_specs = self.get_child_specification(
            #     model=field.comodel_name, parent=name
            # )
            # specs.update(ch_specs)
        return specs

    def _get_bom_line(self, variant, product_tmpl_id):
        bom_line_vals = super()._get_bom_line(variant, product_tmpl_id)
        session_attr_qty_values = self.session_value_quantity_ids
        parent_bom = self._get_parent_bom(product_tmpl_id)
        attr_values = variant.product_template_attribute_value_ids.mapped(
            "product_attribute_value_id"
        )
        if not parent_bom and self._context.get("product_id"):
            product = self._context.get("product_id")
            local_session_attr_qty_value = session_attr_qty_values.filtered(
                lambda local_session: local_session.attr_value_id.product_id.id
                == product.id
            )
            bom_line_vals = {
                    "product_id": product.id,
                    "product_qty": local_session_attr_qty_value.qty > 0
                    and local_session_attr_qty_value.qty
                    or 1,
                }
        elif parent_bom and self._context.get("parent_bom_line"):
            parent_bom_line = self._context.get("parent_bom_line")
            if parent_bom_line.config_set_id:
                for config in parent_bom_line.config_set_id.configuration_ids:
                    if set(config.value_ids.ids).issubset(set(attr_values.ids)):
                        local_session_attr_qty_values = session_attr_qty_values.filtered(
                            lambda local_session: local_session.attr_value_id.product_id
                            and local_session.attr_value_id.attribute_id.id
                            in config.value_ids.mapped("attribute_id").ids
                        )
                        non_local_session_attr_qty_values = session_attr_qty_values.filtered(
                            lambda local_session: not local_session.attr_value_id.product_id
                            and local_session.attr_value_id.attribute_id.id
                            in config.value_ids.mapped("attribute_id").ids
                        )
                        session_attr_qty_values = (
                            session_attr_qty_values - local_session_attr_qty_values
                        )
                        if local_session_attr_qty_values:
                            bom_line_vals = {
                                "product_id": parent_bom_line.product_id.id,
                                "product_qty": (
                                    parent_bom_line.product_qty
                                    * local_session_attr_qty_values.qty
                                ),
                            }
                        elif non_local_session_attr_qty_values:
                            bom_line_vals = {
                                "product_id": parent_bom_line.product_id.id,
                                "product_qty": (
                                    parent_bom_line.product_qty
                                    * non_local_session_attr_qty_values.qty
                                ),
                            }
                    else:
                        parent_bom_product = parent_bom_line.product_id
                        local_session_attr_qty_value = session_attr_qty_values.filtered(
                            lambda local_session: local_session.attr_value_id.product_id.id
                            == parent_bom_product.id and local_session.attr_value_id.attribute_id.id
                            in config.value_ids.mapped("attribute_id").ids
                        )
                        if local_session_attr_qty_value:
                            bom_line_vals = {
                                "product_id": parent_bom_product.id,
                                "product_qty": local_session_attr_qty_value.qty > 0
                                and local_session_attr_qty_value.qty
                                * parent_bom_line.product_qty
                                or parent_bom_line.product_qty,
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
