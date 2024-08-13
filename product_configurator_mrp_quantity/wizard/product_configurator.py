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
                res[qty_field_prefix + str(attribute.id)] = dict(
                    default_attrs,
                    type="many2one",
                    domain=[("product_tmpl_id", "=", wiz.product_tmpl_id.id)],
                    string="Qty",
                    relation="attribute.value.qty",
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

    def apply_onchange_values(self, values, field_name, field_onchange):
        result = super().apply_onchange_values(values, field_name, field_onchange)
        if not self._context.get("is_qty_required"):
            qty_prefix = self._prefixes.get("qty_field")
            field_prefix = self._prefixes.get("field_prefix")
            template_attribute_line = self.env["product.template.attribute.line"]
            attribute_value_qty_obj = self.env["attribute.value.qty"]
            values_dict = self.values_dict and ast.literal_eval(self.values_dict) or {}
            for value in result.get("value"):
                if value.startswith(field_prefix):
                    values_dict.update({value: result.get("value")[value]})
                    attr_id = value.split(field_prefix)[1]
                    attr_id = int(attr_id)
                    template_attr_line_id = template_attribute_line.search(
                        [
                            ("product_tmpl_id", "=", self.product_tmpl_id.id),
                            ("attribute_id", "=", attr_id),
                            ("is_qty_required", "=", True),
                        ],
                        limit=1,
                    )
                    if template_attr_line_id:
                        attr_value_id = result.get("value")[value]
                        attribute_value_qty = attribute_value_qty_obj.search(
                            [
                                ("product_attribute_value_id", "=", int(attr_value_id)),
                                ("product_tmpl_id", "=", self.product_tmpl_id.id),
                                ("product_attribute_id", "=", attr_id),
                            ]
                        )
                        qty_field_name = qty_prefix + str(attr_id)
                        self.dyn_qty_field_value = qty_field_name
                        self.domain_qty_ids = attribute_value_qty.ids
                        domains_dict = (
                            self.domains_dict
                            and ast.literal_eval(self.domains_dict)
                            or {}
                        )
                        if qty_field_name in domains_dict:
                            domains_dict[qty_field_name] = attribute_value_qty.ids
                        else:
                            domains_dict.update(
                                {qty_field_name: attribute_value_qty.ids}
                            )
                        self.domains_dict = domains_dict
                self.values_dict = json.dumps(values_dict)
        return result

    def get_form_vals(
        self,
        dynamic_fields,
        domains,
        cfg_val_ids=None,
        product_tmpl_id=None,
        config_session_id=None,
    ):
        vals = super().get_form_vals(
            dynamic_fields,
            domains,
            cfg_val_ids=cfg_val_ids,
            product_tmpl_id=product_tmpl_id,
            config_session_id=config_session_id,
        )
        field_prefix = self._prefixes.get("field_prefix")
        qty_prefix = self._prefixes.get("qty_field")
        new_val = {}
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        product_template_attribute_value = self.env["product.template.attribute.value"]
        product_template_attribute_line = self.env["product.template.attribute.line"]
        qty_field_value = False
        for k, v in dynamic_fields.items():
            attrb_id = k.split(field_prefix)[1]
            attribute_line = product_template_attribute_line.search(
                [
                    ("attribute_id", "=", int(attrb_id)),
                    ("product_tmpl_id", "=", self.product_tmpl_id.id),
                    ("is_qty_required", "=", True),
                ]
            )
            if k.startswith(field_prefix) and config_session_id and attribute_line:
                template_attribute_value_qty = product_template_attribute_value.search(
                    [
                        ("product_tmpl_id", "=", self.product_tmpl_id.id),
                        ("product_attribute_value_id", "=", int(v)),
                        ("is_qty_required", "=", True),
                    ]
                )
                product_attrs = attribute_value_qty_obj.search(
                    [
                        ("product_tmpl_id", "=", self.product_tmpl_id.id),
                        ("product_attribute_value_id", "=", int(v)),
                        ("qty", "=", int(template_attribute_value_qty.default_qty)),
                    ]
                )
                qty_field_name = qty_prefix + str(attrb_id)
                is_qty_attrb = (
                    config_session_id.product_tmpl_id.attribute_line_ids.filtered(
                        lambda line: line.attribute_id.id == int(attrb_id)
                        and line.is_qty_required
                    )
                )
                if is_qty_attrb and product_attrs:
                    value_qty_dict = (
                        self.value_qty_dict
                        and ast.literal_eval(self.value_qty_dict)
                        or {}
                    )
                    qty_field_value = product_attrs.id
                    attribute_value_qty_rec = attribute_value_qty_obj.browse(
                        value_qty_dict.get(qty_field_name)
                    )
                    if not value_qty_dict.get(qty_field_name):
                        vals[qty_field_name] = qty_field_value
                        value_qty_dict.update({qty_field_name: qty_field_value})
                    elif (
                        value_qty_dict.get(qty_field_name)
                        and int(v)
                        != attribute_value_qty_rec.product_attribute_value_id.id
                    ):
                        vals[qty_field_name] = qty_field_value
                        value_qty_dict[qty_field_name] = qty_field_value
                    self.value_qty_dict = value_qty_dict
        return vals

    def onchange(self, values, field_name, field_onchange):
        onchange_values = super().onchange(values, field_name, field_onchange)
        vals = onchange_values.get("value", {})
        qty_prefix = self._prefixes.get("qty_field")
        field_prefix = self._prefixes.get("field_prefix")
        attribute_value_qty_obj = self.env["attribute.value.qty"]
        attribute_value_obj = self.env["product.attribute.value"]
        qty = 1
        product_price = 1
        for key, val in vals.items():
            if isinstance(val, int) and key.startswith(qty_prefix):
                att_qty_val = attribute_value_qty_obj.browse(val)
                attribute_value = att_qty_val.product_attribute_value_id
                vals[key] = (att_qty_val.id, str(att_qty_val.qty))

        value_qty_dict = (
            self.value_qty_dict and ast.literal_eval(self.value_qty_dict) or {}
        )
        values_dict = self.values_dict and ast.literal_eval(self.values_dict) or {}
        if not onchange_values and values:
            for value in values:
                if value.startswith(qty_prefix):
                    if value_qty_dict.get(value):
                        value_qty_dict[value] = values.get(value)
                    self.with_context(is_abc=True).value_qty_dict = json.dumps(
                        value_qty_dict
                    )
        values_dict.update(value_qty_dict)
        self.values_dict = json.dumps(values_dict)
        update_price = self.product_tmpl_id.list_price
        for value_line in values_dict:
            if value_line.startswith(field_prefix):
                if isinstance(values_dict.get(value_line), int):
                    product_attribute_value = attribute_value_obj.browse(
                        values_dict[value_line]
                    )
                    update_price += product_attribute_value.product_id.lst_price
                elif isinstance(values_dict.get(value_line), list):
                    # Many2Many Values
                    data_list = values_dict[value_line][0][2]
                    product_attribute_values = attribute_value_obj.browse(data_list)
                    for product_attribute_value in product_attribute_values:
                        update_price += product_attribute_value.product_id.lst_price
            if value_line.startswith(qty_prefix):
                qty_rec = attribute_value_qty_obj.browse(values_dict[value_line])
                update_price = (
                    update_price
                    - qty_rec.product_attribute_value_id.product_id.lst_price
                )
                update_price = update_price + (
                    qty_rec.product_attribute_value_id.product_id.lst_price
                    * qty_rec.qty
                )

        if onchange_values.get("value", False):
            onchange_values.get("value")["price"] = update_price
        elif not onchange_values.get("value"):
            onchange_values.update({"value": {"price": update_price}})
        return onchange_values

    # ============================
    # OVERRIDE Methods
    # ============================

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
            attribute_id = attr_line.attribute_id.id
            field_name = field_prefix + str(attribute_id)
            custom_field = custom_field_prefix + str(attribute_id)
            qty_field = qty_field_prefix + str(attribute_id)

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
                    attr_field = field_prefix + str(attr_id)
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
        return attrs, field_name, custom_field, qty_field, config_steps, cfg_step_ids

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

            field_type = dynamic_fields[field_name].get("type")
            if field_type == "many2many":
                node.attrib["widget"] = "many2many_tags"
            # Apply the modifiers (attrs) on the newly inserted field in the
            # arch and add it to the view
            # self.setup_modifiers(node) # TODO: NC: Need to improve this method
            xml_dynamic_form.append(node)

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

        attr_vals = [f for f in fields if f.startswith(field_prefix)]
        custom_attr_vals = [f for f in fields if f.startswith(custom_field_prefix)]
        qty_attr_vals = [f for f in fields if f.startswith(qty_field_prefix)]

        dynamic_fields = attr_vals + custom_attr_vals + qty_attr_vals
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
            field_name = field_prefix + str(attr_id)
            if field_name not in dynamic_fields:
                continue

            custom_field_name = custom_field_prefix + str(attr_id)
            qty_field_name = qty_field_prefix + str(attr_id)

            # Handle default values for dynamic fields on Odoo frontend
            res[0].update(
                {field_name: False, custom_field_name: False, qty_field_name: False}
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
                lambda l: l.product_attribute_id.id == attr_id
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
