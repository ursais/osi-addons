import ast
import json

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductConfigurator(models.TransientModel):
    _inherit = "product.configurator"

    dyn_qty_field_value = fields.Char()
    domain_qty_ids = fields.Many2many(
        "attribute.value.qty",
        string="Domain",
    )
    domains_dict = fields.Text("Domains")
    value_qty_dict = fields.Text("Value Qty")
    values_dict = fields.Text("Values")

    @property
    def _prefixes(self):
        """Oerride this method to add all extra prefixes"""
        return {
            "field_prefix": "__attribute_",
            "custom_field_prefix": "__custom_",
            "qty_field": "__qty_",
            "domain_field_prefix": "__domain_",
        }

    @api.model
    def fields_get(self, allfields=None, write_access=True, attributes=None):
        qty_field_prefix = self._prefixes.get("qty_field")
        res = super().fields_get(allfields=allfields, attributes=attributes)

        wizard_id = self._find_wizard_context()
        # If wizard_id is not defined in the context then the wizard was just
        # launched and is not stored in the database yet
        if not wizard_id:
            return res

        # Get the wizard object from the database
        wiz = self.browse(wizard_id)
        active_step_id = wiz.state

        # If the product template is not set it is still at the 1st step
        if not wiz.product_tmpl_id:
            return res
        # Default field attributes
        default_attrs = self.get_field_default_attrs()

        attribute_lines = wiz.product_tmpl_id.attribute_line_ids
        attribute_value_obj = self.env["product.template.attribute.value"]
        for line in attribute_lines:
            attribute = line.attribute_id
            value_ids = line.value_ids.ids
            if line.is_qty_required:
                field_name = qty_field_prefix + str(line.id)+"_"+str(attribute.id)
                res[field_name] = dict(
                    default_attrs,
                    type="many2one",
                    domain=[("product_tmpl_id", "=", wiz.product_tmpl_id.id)],
                    string="Qty",
                    relation="attribute.value.qty",
                    widget="selection",
                )
        return res

    @api.model_create_multi
    def create(self, vals_list):
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        qty_prefix = self._prefixes.get("qty_field")
        for vals in vals_list:
            if "product_id" in vals:
                product = self.env["product.product"].browse(vals["product_id"])
                product_attr_qty = product.product_attribute_value_qty_ids
                attr_qty_list = []
                session = self.env["product.config.session"].create_get_session(
                    product_tmpl_id=int(vals.get("product_tmpl_id"))
                )
                flag = False
                for attr in product_attr_qty:
                    session_attr = session.session_value_quantity_ids.filtered(
                        lambda l: l.attr_value_id.id == attr.attr_value_id.id
                        and l.qty == int(attr.qty)
                    )
                    if not session_attr:
                        attr_qty_list.append(
                            (
                                0,
                                0,
                                {
                                    "product_attribute_id": attr.attr_value_id.attribute_id.id,
                                    "attr_value_id": attr.attr_value_id.id,
                                    "qty": int(attr.qty),
                                    "attribute_value_qty_id": attr.attribute_value_qty_id.id,
                                },
                            )
                        )
                if attr_qty_list:
                    vals.update({"session_value_quantity_ids": attr_qty_list})
        return super().create(vals_list)

    def get_form_vals(
        self,
        dynamic_fields,
        domains,
        cfg_val_ids=None,
        product_tmpl_id=None,
        config_session_id=None,
        values=None,
    ):
        vals = super().get_form_vals(
            dynamic_fields,
            domains,
            cfg_val_ids=cfg_val_ids,
            product_tmpl_id=product_tmpl_id,
            config_session_id=config_session_id,
            values=values,
        )

        print(self.value_ids,"/////////////Valsssss",vals)
        vals.update({"val_qty_ids":[]})
        field_prefix = self._prefixes.get("field_prefix")
        qty_prefix = self._prefixes.get("qty_field")
        qty_dynamic_fields = {k: v for k, v in values.items() if k.startswith(qty_prefix)}
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        product_template_attribute_value = self.env["product.template.attribute.value"]
        product_template_attribute_line = self.env["product.template.attribute.line"]
        qty_field_value = False
        local_dict = {}
        new_price = vals["price"]
        values_dict = (
            self.values_dict
            and ast.literal_eval(self.values_dict)
            or {}
        )
        print("AAAAAAAAAAA",vals,values_dict)
        for k,v in vals.items():
            if k.startswith(field_prefix):
                attrb_line_id = k.split(field_prefix)[1]
                attrb_id = attrb_line_id.split("_")[1]
                line_id = attrb_line_id.split("_")[0]
                pt_attribute_line = product_template_attribute_line.search(
                    [
                        ("attribute_id", "=", int(attrb_id)),
                        ("product_tmpl_id", "=", self.product_tmpl_id.id),
                        ("is_qty_required", "=", True),
                        ("id","=",int(line_id))
                    ]
                )
                if pt_attribute_line and config_session_id:
                    template_attribute_value_qty = product_template_attribute_value.search(
                        [
                            ("product_tmpl_id", "=", self.product_tmpl_id.id),
                            ("product_attribute_value_id", "=", int(v)),
                            ("is_qty_required", "=", True),
                        ]
                    )
                    default_attribute_value_qty = attribute_value_qty_obj.search(
                        [
                            ("product_tmpl_id", "=", self.product_tmpl_id.id),
                            ("product_attribute_value_id", "=", int(v)),
                            ("qty", "=", int(template_attribute_value_qty.default_qty)),
                            ("template_attri_value_id","=",template_attribute_value_qty.id)
                        ]
                    )
                    product_attrs2 = attribute_value_qty_obj.search(
                        [
                            ("product_tmpl_id", "=", self.product_tmpl_id.id),
                            ("product_attribute_value_id", "=", int(v)),
                            ("template_attri_value_id","=",template_attribute_value_qty.id)
                        ]
                    )
                    qty_field_name = qty_prefix + str(pt_attribute_line.id)+"_"+str(attrb_id)
                    qty_field_value = default_attribute_value_qty.id
                    if qty_dynamic_fields and qty_dynamic_fields.get(qty_field_name) and int(qty_dynamic_fields.get(qty_field_name)) in product_attrs2.ids:
                        qty_field_value = int(qty_dynamic_fields.get(qty_field_name))
                        default_attribute_value_qty = attribute_value_qty_obj.browse(qty_field_value)
                    local_dict[qty_field_name] = qty_field_value
                    if default_attribute_value_qty.product_attribute_value_id.product_id:
                        updatedprice = new_price - default_attribute_value_qty.product_attribute_value_id.product_id.lst_price
                        price = updatedprice + (default_attribute_value_qty.product_attribute_value_id.product_id.lst_price * default_attribute_value_qty.qty)
                        local_dict["price"] = price
                        new_price = price
                    if not default_attribute_value_qty.product_attribute_value_id.product_id and default_attribute_value_qty.template_attri_value_id.price_extra:
                        updatedprice = new_price - default_attribute_value_qty.template_attri_value_id.price_extra
                        price = updatedprice + (default_attribute_value_qty.template_attri_value_id.price_extra * default_attribute_value_qty.qty)
                        local_dict["price"] = price


                    if values_dict.get(qty_field_name):
                        values_dict[qty_field_name] = product_attrs2.ids
                    else:
                        values_dict.update({qty_field_name:product_attrs2.ids})

        self.values_dict = values_dict
        vals |= local_dict
        print("////////@###########$$$$$$$$$",vals,local_dict)
        print("ZZZZZZZZZZZZZZZ",self.product_tmpl_id,self.product_tmpl_id.attribute_line_ids)
        return vals

    # def get_form_vals(
    #     self,
    #     dynamic_fields,
    #     domains,
    #     cfg_val_ids=None,
    #     product_tmpl_id=None,
    #     config_session_id=None,
    #     values=None,
    # ):
    #     """Generate a dictionary to return new values via onchange method.
    #     Domains hold the values available, this method enforces these values
    #     if a selection exists in the view that is not available anymore.

    #     :param dynamic_fields: Dictionary with the current {dynamic_field: val}
    #     :param domains: Odoo domains restricting attribute values

    #     :returns vals: Dictionary passed to {'value': vals} by onchange method
    #     """
    #     vals = {}
    #     dynamic_fields = {k: v for k, v in dynamic_fields.items() if v}
    #     # List to store multi-value IDs
    #     available_val_ids_m2m = []
    #     for k, v in dynamic_fields.items():
    #         if not v:
    #             continue
    #         available_val_ids = domains[k][0][2]
    #         # Get all value_ids linked to the current config session
    #         value_ids = self.config_session_id.value_ids
    #         # Filter attribute lines for multi-select attributes that match IDs
    #         # in value_ids
    #         attribute_line_ids = self.product_tmpl_id.attribute_line_ids.filtered(
    #             lambda line, value_ids=value_ids: line.multi
    #             and line.attribute_id.id in value_ids.mapped("attribute_id").ids
    #         )
    #         # Get multi-value IDs that match attribute lines
    #         # Filter the `multi_value_ids` associated with attributes in
    #         # `attribute_line_ids`
    #         multi_value_ids = value_ids.filtered(
    #             lambda value,
    #             attribute_line_ids=attribute_line_ids: value.attribute_id.id
    #             in attribute_line_ids.mapped("attribute_id").ids
    #         )

    #         # Retrieve IDs of available multi-value options
    #         available_val_ids_m2m = multi_value_ids.ids

    #         # Process values for the current attribute field
    #         if isinstance(v, list):
    #             for sub_value in v:
    #                 if sub_value[0] == Command.UNLINK:
    #                     if sub_value[1] in available_val_ids_m2m:
    #                         available_val_ids_m2m.remove(sub_value[1])
    #                 elif sub_value[0] == Command.LINK:
    #                     if sub_value[1] not in available_val_ids_m2m:
    #                         available_val_ids_m2m.append(sub_value[1])
    #                 elif sub_value[0] == Command.SET:
    #                     available_val_ids_m2m = sub_value[2]

    #             # Update dynamic fields and set `vals` with modified multi-value IDs
    #             dynamic_fields.update({k: available_val_ids_m2m})
    #             vals[k] = [[Command.SET, 0, available_val_ids_m2m]]

    #         elif v not in available_val_ids:
    #             # Handle single values not in available IDs
    #             dynamic_fields.update({k: None})
    #             vals[k] = None
    #         else:
    #             # Use the single value if it exists in available IDs
    #             vals[k] = v

    #     field_prefix = self._prefixes.get("field_prefix")
    #     # List of attributes to remove from value_ids as they are currently changed
    #     attributes_to_consider_removal = []
    #     print("//////field_prefix//",field_prefix,vals)
    #     field_prefix = field_prefix + str(1675)
    #     for field in vals:
    #         print("//////field//",field_prefix ,field)
    #         if field_prefix in field:
    #             attribute_line_id = field.split(field_prefix)[1]
    #             attributes_to_consider_removal.append(int(attribute_line_id.split("_")[1]))
    #     # attributes_to_consider_removal = [
    #     #     int(field.split(field_prefix)[1]) for field in vals if field_prefix in field
    #     # ]
        
    #     filtered_value_ids = self.value_ids.filtered(
    #         lambda val: val.attribute_id.id not in attributes_to_consider_removal
    #     ).ids
    #     final_config_values = list(filtered_value_ids + list(dynamic_fields.values()))
    #     vals.update(self.get_onchange_vals(final_config_values, config_session_id))
    #     # To solve the Multi selection problem removing extra []
    #     if "value_ids" in vals:
    #         val_ids = vals["value_ids"][0]
    #         vals["value_ids"] = [[val_ids[0], val_ids[1], tools.flatten(val_ids[2])]]
    #     return vals

    def onchange(self, values, field_names, field_onchange):
        onchange_values = super().onchange(values, field_names, field_onchange)
        vals = onchange_values.get("value", {})
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        qty_prefix = self._prefixes.get("qty_field")
        for key, val in vals.items():
            if isinstance(val, int) and key.startswith(qty_prefix):
                att_qty_val = attribute_value_qty_obj.browse(val)
                attribute_value = att_qty_val.product_attribute_value_id
                vals[key] = (att_qty_val.id, str(att_qty_val.qty))
        return onchange_values

    @api.onchange("product_preset_id")
    def _onchange_product_preset(self):
        result = super()._onchange_product_preset()
        if (
            self.product_preset_id
            and self.product_preset_id.product_attribute_value_qty_ids
        ):
            preset_id = self.product_preset_id
            if not self._origin and self.product_tmpl_id and preset_id and self._context.get("allow_preset_selection"):
                self = self.env[self._name].create({"product_tmpl_id": self.product_tmpl_id.id})
            values_dict = self.values_dict and ast.literal_eval(self.values_dict) or {}
            product_attribute_value_qty_ids = (
                preset_id.product_attribute_value_qty_ids
            )
            default_val_lines = self.product_tmpl_id.attribute_line_ids.filtered("default_val")
            print(result,"?@@@@@@@@@default_val_lines",default_val_lines)
            attr_qty_list = []
            attribute_qty_value_obj = self.env["attribute.value.qty"]
            qty_prefix = self._prefixes.get("qty_field")
            field_prefix = self._prefixes.get("field_prefix")
            print(qty_prefix,"//////@@@@@@@@@@product_attribute_value_qty_ids",product_attribute_value_qty_ids,)
            for qty_attr_value in product_attribute_value_qty_ids:
                attribute_value_qty = attribute_qty_value_obj.search(
                    [
                        (
                            "product_attribute_value_id",
                            "=",
                            qty_attr_value.attr_value_id.id,
                        ),
                        ("product_tmpl_id", "=", self.product_tmpl_id.id),
                        (
                            "product_attribute_id",
                            "=",
                            qty_attr_value.attr_value_id.attribute_id.id,
                        ),
                    ]
                )
                if attribute_value_qty:
                    self._origin.domain_qty_ids = attribute_value_qty.ids
                    qty_field_name = f"{qty_prefix}{str(qty_attr_value.attribute_value_qty_id.template_attri_value_id.attribute_line_id.id)}_{str(qty_attr_value.attr_value_id.attribute_id.id)}"
                    self.dyn_qty_field_value = qty_field_name
                attr_qty_list.append(
                    (
                        0,
                        0,
                        {
                            "session_id": self._origin.config_session_id.id,
                            "product_attribute_id": qty_attr_value.attr_value_id.attribute_id.id,
                            "attr_value_id": qty_attr_value.attr_value_id.id,
                            "qty": int(qty_attr_value.qty),
                            "attribute_value_qty_id": qty_attr_value.attribute_value_qty_id.id,
                        },
                    )
                )
                values_dict.update(
                    {
                        self._origin.dyn_qty_field_value: qty_attr_value.attribute_value_qty_id.id
                    }
                )
            attribute_line_ids = self.product_tmpl_id.attribute_line_ids
            for value in self._origin.value_ids:
                attr_id = value.attribute_id.id
                attr_line = attribute_line_ids.filtered(
                    lambda line: line.attribute_id.id == attr_id and value.id in line.value_ids.ids
                )
                if not attr_line:
                    continue
                field_name = f"{field_prefix}{attr_line.id}_{attr_id}"
                if attr_line.multi:
                    multi_values = self._origin.value_ids.filtered(
                        lambda val: val.attribute_id.id == attr_id
                    )
                    values_dict[field_name] = [[6, 0, multi_values.ids]]
                else:
                    values_dict[field_name] = value.id
            values_dict.update({"preset_product": self.product_preset_id  and self.product_preset_id.id or preset_id.id})
            self._origin.values_dict = json.dumps(values_dict)
            self._origin.config_session_id.session_value_quantity_ids = attr_qty_list
            print("#######values_dict####",self._origin.values_dict)
            return result

    # # ============================
    # # OVERRIDE Methods
    # # ============================

    def prepare_attrs_initial(
        self,
        attr_lines,
        field_prefix,
        custom_field_prefix,
        qty_field_prefix,
        dynamic_fields,
        wiz,
    ):
        cfg_step_ids = []
        for attr_line in attr_lines:
            # attribute_id = attr_line.attribute_id.id
            # field_name = field_prefix + str(attribute_id)
            # custom_field = custom_field_prefix + str(attribute_id)
            # domain_field_prefix = self._prefixes.get("domain_field_prefix")
            # domain_field_name = domain_field_prefix + str(attribute_id)
            # qty_field = qty_field_prefix + str(attribute_id)

            attribute_id = attr_line.attribute_id.id
            field_name = field_prefix +str(attr_line.id)+"_"+str(attribute_id)
            domain_field_prefix = self._prefixes.get("domain_field_prefix")
            domain_field_name = domain_field_prefix +str(attr_line.id)+"_"+str(attribute_id)
            custom_field = custom_field_prefix + str(attribute_id)
            qty_field = qty_field_prefix +str(attr_line.id)+"_"+ str(attribute_id)

            # Check if the attribute line has been added to the db fields
            if field_name not in dynamic_fields:
                continue

            config_steps = wiz.product_tmpl_id.config_step_line_ids.filtered(
                lambda x: attr_line in x.attribute_line_ids
            )

            # attrs property for dynamic fields
            attrs = {"readonly": "", "required": "", "invisible": ""}
            invisible_str = ""
            readonly_str = ""
            required_str = ""

            if config_steps:
                cfg_step_ids = [str(id) for id in config_steps.ids]
                invisible_str = f"state not in {cfg_step_ids}"
                readonly_str = f"state not in {cfg_step_ids}"
                # If attribute is required make it so only in the proper step
                if attr_line.required:
                    required_str = f"state in {cfg_step_ids}"
            else:
                invisible_str = "state not in {}".format(["configure"])
                readonly_str = "state not in {}".format(["configure"])
                # If attribute is required make it so only in the proper step
                if attr_line.required:
                    required_str = "state in {}".format(["configure"])

            if attr_line.custom:
                pass
                # TODO: Implement restrictions for ranges

            config_lines = wiz.product_tmpl_id.config_line_ids
            dependencies = config_lines.filtered(
                lambda cl: cl.attribute_line_id == attr_line
            )

            # If an attribute field depends on another field from the same
            # configuration step then we must use attrs to enable/disable the
            # required and readonly depending on the value entered in the
            # dependee

            if attr_line.value_ids <= dependencies.mapped("value_ids"):
                attr_depends = {}
                domain_lines = dependencies.mapped("domain_id.domain_line_ids")
                for domain_line in domain_lines:
                    attr_id = domain_line.attribute_id.id
                    attr_field = f"{field_prefix}{str(attr_line.id)}_{str(attr_id)}"
                    attr_lines = wiz.product_tmpl_id.attribute_line_ids
                    # If the fields it depends on are not in the config step
                    # allow to update attrs for all attribute.\ otherwise
                    # required will not work with stepchange using statusbar.
                    # if config_steps and wiz.state not in cfg_step_ids:
                    #     continue
                    if attr_field not in attr_depends:
                        attr_depends[attr_field] = set()
                    if domain_line.condition == "in":
                        attr_depends[attr_field] |= set(domain_line.value_ids.ids)
                    elif domain_line.condition == "not in":
                        val_ids = attr_lines.filtered(
                            lambda line: line.attribute_id.id == attr_id
                        ).value_ids
                        val_ids = val_ids - domain_line.value_ids
                        attr_depends[attr_field] |= set(val_ids.ids)

                for dependee_field, val_ids in attr_depends.items():
                    if not val_ids:
                        continue

                    # if not attr_line.custom:
                    #     readonly_str = f"{dependee_field} not in {list(val_ids)}"
                    if attr_line.required and not attr_line.custom:
                        required_str += f" and {dependee_field} in {list(val_ids)}"

            attrs.update(
                {
                    "readonly": readonly_str,
                    "required": required_str,
                    "invisible": invisible_str,
                }
            )
        return attrs, field_name, custom_field, qty_field, config_steps, cfg_step_ids, domain_field_name

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        """Create the configuration view using the dynamically generated
        fields in fields_get()
        """

        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")
        qty_field_prefix = self._prefixes.get("qty_field")

        try:
            # Search for view container hook and add dynamic view and fields
            xml_view = etree.fromstring(res["arch"])
            xml_static_form = xml_view.xpath("//group[@name='static_form']")[0]
            xml_dynamic_form = etree.Element("group", colspan="2", name="dynamic_form")
            xml_parent = xml_static_form.getparent()
            xml_parent.insert(xml_parent.index(xml_static_form) + 1, xml_dynamic_form)
            xml_dynamic_form = xml_view.xpath("//group[@name='dynamic_form']")[0]
        except Exception as exc:
            raise UserError(
                _("There was a problem rendering the view " "(dynamic_form not found)")
            ) from exc

        # Get all dynamic fields inserted via fields_get method
        attr_lines = wiz.product_tmpl_id.attribute_line_ids.sorted()

        # Loop over the dynamic fields and add them to the view one by one
        for attr_line in attr_lines:  # TODO: NC: Added a filter for multi
            (
                attrs,
                field_name,
                custom_field,
                qty_field,
                config_steps,
                cfg_step_ids,
                domain_field_name,
            ) = self.prepare_attrs_initial(
                attr_line,
                field_prefix,
                custom_field_prefix,
                qty_field_prefix,
                dynamic_fields,
                wiz,
            )

            # Create the new field in the view
            node = etree.Element(
                "field",
                name=field_name,
                on_change="1",
                default_focus="1" if attr_line == attr_lines[0] else "0",
                attrib=attrs,
                context=str(
                    {
                        "show_attribute": False,
                        "show_price_extra": True,
                        "active_id": wiz.product_tmpl_id.id,
                        "wizard_id": wiz.id,
                        "field_name": field_name,
                        "is_m2m": attr_line.multi,
                        "value_ids": attr_line.value_ids.ids,
                        "active_model": self._name,
                    }
                ),
                options=str(
                    {
                        "no_create": True,
                        "no_create_edit": True,
                        "no_open": True,
                    }
                ),
            )
            xml_dynamic_form.append(node)
            domain_node = etree.Element(
                "field",
                name=domain_field_name,
                on_change="1",
                readonly="1",
                invisible="1",
            )
            xml_dynamic_form.append(domain_node)

            field_type = dynamic_fields[field_name].get("type")
            if field_type == "many2many":
                node.attrib["widget"] = "many2many_tags"
            # Apply the modifiers (attrs) on the newly inserted field in the
            # arch and add it to the view
            # self.setup_modifiers(node) # TODO: NC: Need to improve this method
            

            if attr_line.custom and custom_field in dynamic_fields:
                widget = ""
                config_session_obj = self.env["product.config.session"]
                custom_option_id = config_session_obj.get_custom_value_id().id

                if field_type == "many2many":
                    field_val = [(6, False, [custom_option_id])]
                else:
                    field_val = custom_option_id

                attrs.update(
                    {
                        "readonly": attrs.get("readonly")
                        + f" and {field_name} != {field_val}"
                    }
                )
                attrs.update(
                    {
                        "invisible": attrs.get("invisible")
                        + f" and {field_name} != {field_val}"
                    }
                )
                attrs.update(
                    {
                        "required": attrs.get("required")
                        + f" and {field_name} != {field_val}"
                    }
                )

                if config_steps:
                    attrs.update(
                        {
                            "required": attrs.get("required")
                            + f" and 'state' in {cfg_step_ids}"
                        }
                    )

                # TODO: Add a field2widget mapper
                if attr_line.attribute_id.custom_type == "color":
                    widget = "color"

                node = etree.Element(
                    "field", name=custom_field, attrib=attrs, widget=widget
                )
                # self.setup_modifiers(node) # TODO: NC: Need to improve this method
                xml_dynamic_form.append(node)
            if attr_line.is_qty_required and qty_field in dynamic_fields:
                node = etree.Element(
                    "field",
                    name=qty_field,
                    on_change="1",
                    attrib=attrs,
                    context=str(
                        {
                            "active_id": wiz.product_tmpl_id.id,
                            "wizard_id": wiz.id,
                            "field_name": qty_field,
                            "is_qty_required": attr_line.is_qty_required,
                            # "value_ids": self.env['attribute.value.qty'].search([]).ids,
                            "active_model": self._name,
                        }
                    ),
                    options=str(
                        {
                            "no_create": True,
                            "no_create_edit": True,
                            "no_open": True,
                        }
                    ),
                )
                # self.setup_modifiers(node) # TODO: NC: Need to improve this method
                xml_dynamic_form.append(node)
        return xml_view

    def read(self, fields=None, load="_classic_read"):
        """Remove dynamic fields from the fields list and update the
        returned values with the dynamic data stored in value_ids"""
        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")
        qty_field_prefix = self._prefixes.get("qty_field")
        domain_field_prefix = self._prefixes.get("domain_field_prefix")

        attr_vals = [f for f in fields if f.startswith(field_prefix)]
        custom_attr_vals = [f for f in fields if f.startswith(custom_field_prefix)]
        qty_attr_vals = [f for f in fields if f.startswith(qty_field_prefix)]
        domain_attr_vals = [f for f in fields if f.startswith(domain_field_prefix)]

        dynamic_fields = attr_vals + custom_attr_vals + qty_attr_vals + domain_attr_vals
        fields = self._remove_dynamic_fields(fields)

        custom_val = self.env["product.config.session"].get_custom_value_id()
        dynamic_vals = {}

        res = super().read(fields=fields, load=load)

        if not load:
            load = "_classic_read"

        if not dynamic_fields:
            return res

        for attr_line in self.product_tmpl_id.attribute_line_ids:
            attr_id = attr_line.attribute_id.id
            field_name = field_prefix +str(attr_line.id)+"_"+str(attr_id)
            if field_name not in dynamic_fields:
                continue

            custom_field_name = custom_field_prefix + str(attr_id)
            qty_field_name = qty_field_prefix+str(attr_line.id)+"_"+ str(attr_id)
            domain_field_name = domain_field_prefix +str(attr_line.id)+"_"+ str(attr_id)
            available_value_ids = self.config_session_id.values_available(
                check_val_ids=attr_line.value_ids.ids,
                product_template_attribute_line_id=attr_line.id,
            )

            # Handle default values for dynamic fields on Odoo frontend
            res[0].update(
                {
                    field_name: [] if attr_line.multi else False,
                    custom_field_name: False,
                    qty_field_name: False,
                    domain_field_name: [("id", "in", available_value_ids)],
                }
            )

            custom_vals = self.custom_value_ids.filtered(
                lambda x: x.attribute_id.id == attr_id
            ).with_context(show_attribute=False)
            vals = attr_line.value_ids.filtered(
                lambda v: v in self.value_ids
            ).with_context(
                show_attribute=False,
                show_price_extra=True,
                active_id=self.product_tmpl_id.id,
            )
            qty_field_values = self.session_value_quantity_ids.filtered(
                lambda l: l.product_attribute_id.id == attr_id and l.attr_value_id.id in attr_line.value_ids.ids
            )
            if not attr_line.custom and not vals:
                continue

            if attr_line.custom and custom_vals:
                custom_field_val = custom_val.id
                if load == "_classic_read":
                    # custom_field_val = custom_val.name_get()[0]
                    custom_field_val = (custom_val.id, custom_val.display_name or "")
                dynamic_vals.update(
                    {
                        field_name: custom_field_val,
                        custom_field_name: custom_vals.eval(),
                    }
                )
            elif attr_line.multi:
                dynamic_vals = {field_name: vals.ids}
            else:
                try:
                    vals.ensure_one()
                    field_value = vals.id
                    if load == "_classic_read":
                        # field_value = vals.name_get()[0]
                        field_value = (vals.id, vals.display_name or "")
                    dynamic_vals = {field_name: field_value}
                except Exception:
                    continue

            if qty_field_values:
                for attr_qty in qty_field_values:
                    dynamic_vals.update(
                        {
                            qty_field_name: (
                                attr_qty.attribute_value_qty_id.id,
                                str(attr_qty.attribute_value_qty_id.qty),
                            )
                        }
                    )
            res[0].update(dynamic_vals)
        return res


    def apply_onchange_values(self, values, field_names, field_onchange):
        """Called from web-controller
        - original onchage return M2o values in formate
        (attr-value.id, attr-value.name) but on website
        we need only attr-value.id"""

        print("########values",values)
        product_tmpl_id = self.env["product.template"].browse(
            values.get("product_tmpl_id", [])
        )
        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id

        config_session_id = self.env["product.config.session"].browse(
            values.get("config_session_id", [])
        )
        if not config_session_id:
            config_session_id = self.config_session_id

        state = values.get("state", False)
        if not state:
            state = self.state
        cfg_vals = self.env["product.attribute.value"]
        if values.get("value_ids", []):
            cfg_vals = self.env["product.attribute.value"].browse(
                values.get("value_ids", [])[0][2]
            )
        if not cfg_vals:
            cfg_vals = self.value_ids

        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")
        domain_field_prefix = self._prefixes.get("domain_field_prefix")
        qty_prefix = self._prefixes.get("qty_field")
        local_field_name = field_names and field_names[0].startswith(field_prefix)
        local_custom_field = field_names and field_names[0].startswith(
            custom_field_prefix
        )
        local_domain_prefix = field_names and field_names[0].startswith(
            domain_field_prefix
        )
        local_qty_prefix = field_names and field_names[0].startswith(
            qty_prefix
        )
        if not local_field_name and not local_custom_field and not local_domain_prefix and not local_qty_prefix:
            values = self._remove_dynamic_fields(values)
            field_onchange = self._remove_dynamic_fields(field_onchange)
            res = super(ProductConfigurator, self.with_context(parent_super=True)).onchange(values, field_names, field_onchange)
            return res

        view_val_ids = set()
        view_attribute_ids = set()

        try:
            cfg_step_id = int(state)
            cfg_step = product_tmpl_id.config_step_line_ids.filtered(
                lambda x: x.id == cfg_step_id
            )
        except Exception:
            cfg_step = self.env["product.config.step.line"]

        print("##@@@@@@@@@values",values,self.value_ids)
        dynamic_fields = {k: v for k, v in values.items() if k.startswith(field_prefix)}

        # Get the unstored values from the client view
        for k, v in dynamic_fields.items():
            zz = k.split(field_prefix)
            attr_line_id = k.split(field_prefix)[1]
            attr_id = int(attr_line_id.split("_")[1])
            print("#@@@@attr_id@@@",zz,attr_id,attr_line_id)
            # if isinstance(v, list):
            #    dynamic_fields[k] = v[0][2]

            line_attributes = cfg_step.attribute_line_ids.mapped("attribute_id")
            if not cfg_step or attr_id in line_attributes.ids:
                view_attribute_ids.add(attr_id)
            else:
                continue
            if not v:
                continue
            if isinstance(v, list):
                if v[0][0] == Command.SET:
                    view_val_ids |= set(v[0][2])
                else:
                    view_val_ids |= {a[1] for a in v}
            elif isinstance(v, int):
                view_val_ids.add(v)

        # Clear all DB values belonging to attributes changed in the wizard
        cfg_vals = cfg_vals.filtered(
            lambda v: v.attribute_id.id not in view_attribute_ids
        )
        # Combine database values with wizard values_available
        cfg_val_ids = cfg_vals.ids + list(view_val_ids)

        domains = self.get_onchange_domains(
            cfg_val_ids, product_tmpl_id, config_session_id
        )

        vals = self.get_form_vals(
            dynamic_fields=dynamic_fields,
            domains=domains,
            product_tmpl_id=product_tmpl_id,
            config_session_id=config_session_id,
            values=values,
        )
        vals.update(self._transform_onchange_domain_field_vals(domains))
        return {"value": vals, "domain": domains}