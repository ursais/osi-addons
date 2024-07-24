from lxml import etree

from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools import frozendict
from odoo.tools.misc import OrderedSet

from odoo.addons.base.models.ir_model import FIELD_TYPES

# from odoo.addons.base.models.ir_ui_view import (
#     transfer_field_to_modifiers,
#     transfer_modifiers_to_node,
#     transfer_node_to_modifiers,
# )


class Base(models.AbstractModel):
    _inherit = "base"

    def onchange(self, values: {}, field_names: [], fields_spec: {}):
        fields_spec = self.env["product.configurator"]._remove_dynamic_fields(
            fields_spec
        )
        return super().onchange(values, field_names, fields_spec)


class FreeSelection(fields.Selection):
    def convert_to_cache(self, value, record, validate=True):
        return super().convert_to_cache(value=value, record=record, validate=False)


class ProductConfigurator(models.TransientModel):
    _name = "product.configurator"
    _inherits = {"product.config.session": "config_session_id"}
    _description = "Product configuration Wizard"

    def _find_wizard_context(self):
        # TODO: For more ref. https://github.com/odoo/odoo/pull/135145
        wizard_id = (
            self.env.context.get("wizard_id_view_ref")
            or self.env.context.get("wizard_id")
            or False
        )
        return wizard_id

    @property
    def _prefixes(self):
        """Return a dictionary with all dynamic field prefixes used to generate
        fields in the wizard. Any module extending this functionality should
        override this method to add all extra prefixes"""
        return {
            "field_prefix": "__attribute_",
            "custom_field_prefix": "__custom_",
        }

    # TODO: Remove _prefix suffix as this is implied by the class property name

    @api.model
    def _remove_dynamic_fields(self, fields):
        """Remove elements from the fields dictionary/list that begin with any
        prefix from the _prefixes property
            :param fields: list or dict of the form [fn1, fn2] / {fn1: val}
        """

        prefixes = self._prefixes.values()

        field_type = type(fields)

        if field_type == list:
            static_fields = []
        elif field_type == dict:
            static_fields = {}

        for field_name in fields:
            if any(prefix in field_name for prefix in prefixes):
                continue
            if field_type == list:
                static_fields.append(field_name)
            elif field_type == dict:
                static_fields[field_name] = fields[field_name]
        return static_fields

    @api.depends("product_tmpl_id", "value_ids", "custom_value_ids")
    def _compute_cfg_image(self):
        # TODO: Update when allowing custom values to influence image
        for configurator in self:
            cfg_sessions = configurator.config_session_id.with_context(bin_size=False)
            image = cfg_sessions.get_config_image()
            configurator.product_img = image

    @api.depends("product_tmpl_id", "product_tmpl_id.attribute_line_ids")
    def _compute_attr_lines(self):
        """Use compute method instead of related due to increased flexibility
        and strange behavior when attempting to have a related field point
        to computed values"""
        for configurator in self:
            attribute_lines = configurator.product_tmpl_id.attribute_line_ids
            configurator.attribute_line_ids = attribute_lines

    # TODO: We could use a m2o instead of a monkeypatched select field but
    # adding new steps should be trivial via custom development
    def get_state_selection(self):
        """Get the states of the wizard using standard values and optional
        configuration steps set on the product.template via
        config_step_line_ids"""
        steps = [("select", "Select Template")]

        # Get the wizard id from context set via action_next_step method
        wizard_id = self._find_wizard_context()
        wiz = self.browse(wizard_id).exists()

        if not wiz:
            return steps

        open_lines = wiz.config_session_id.get_open_step_lines()
        if open_lines:
            open_steps = open_lines.mapped(lambda x: (str(x.id), x.config_step_id.name))
            steps = open_steps if wiz.product_id else steps + open_steps
        else:
            steps.append(("configure", "Configure"))
        return steps

    @api.onchange("product_tmpl_id")
    def onchange_product_tmpl(self):
        """set the preset_id if exist in session"""
        template = self.product_tmpl_id

        self.config_step_ids = template.config_step_line_ids.mapped("config_step_id")

        # Set product preset if exist in session
        if template:
            session = self.env["product.config.session"].search_session(
                product_tmpl_id=template.id
            )
            self.product_preset_id = session.product_preset_id

        if self.value_ids:
            # TODO: Add confirmation button an delete cfg session
            raise UserError(
                _(
                    "Changing the product template while having an active "
                    "configuration will erase reset/clear all values"
                )
            )

    def get_onchange_domains(
        self,
        values,
        cfg_val_ids,
        product_tmpl_id=False,
        config_session_id=False,
    ):
        """Generate domains to be returned by onchange method in order
        to restrict the availble values of dynamically inserted fields

        :param values: values argument passed to onchance wrapper
        :cfg_val_ids: current configuration passed as a list of value_ids
        (usually in the form of db value_ids + interface value_ids)

        :returns: a dictionary of domains returned by onchance method
        """

        field_prefix = self._prefixes.get("field_prefix")
        if not product_tmpl_id:
            product_tmpl_id = self.product_tmpl_id
        if not config_session_id:
            config_session_id = self.config_session_id

        domains = {}
        check_avail_ids = cfg_val_ids[:]
        for line in product_tmpl_id.attribute_line_ids.sorted():
            field_name = field_prefix + str(line.attribute_id.id)

            if field_name not in values:
                continue

            vals = values[field_name]

            # get available values

            avail_ids = config_session_id.values_available(
                check_val_ids=line.value_ids.ids, value_ids=check_avail_ids
            )

            domains[field_name] = [("id", "in", avail_ids)]
            check_avail_ids = list(
                set(check_avail_ids) - (set(line.value_ids.ids) - set(avail_ids))
            )
            # Include custom value in the domain if attr line permits it
            if line.custom:
                custom_val = config_session_id.get_custom_value_id()
                domains[field_name][0][2].append(custom_val.id)
                if line.multi and vals and custom_val.id in vals[0][2]:
                    continue
        return domains

    def get_onchange_vals(self, cfg_val_ids, config_session_id=None):
        """Onchange hook to add / modify returned values by onchange method"""
        if not config_session_id:
            config_session_id = self.config_session_id

        # Remove None from cfg_val_ids if exist
        cfg_val_ids = [val for val in cfg_val_ids if val]
        tobe_remove_attr = self.env.context.get("tobe_remove_attr", [])
        product_img = config_session_id.get_config_image(cfg_val_ids)
        price = config_session_id.with_context(
            tobe_remove_attr=tobe_remove_attr
        ).get_cfg_price(cfg_val_ids)
        weight = config_session_id.get_cfg_weight(value_ids=cfg_val_ids)

        return {
            "product_img": product_img,
            "value_ids": [(6, 0, cfg_val_ids)],
            "weight": weight,
            "price": price,
        }

    def get_form_vals(
        self,
        dynamic_fields,
        domains,
        cfg_val_ids=None,
        product_tmpl_id=None,
        config_session_id=None,
    ):
        """Generate a dictionary to return new values via onchange method.
        Domains hold the values available, this method enforces these values
        if a selection exists in the view that is not available anymore.

        :param dynamic_fields: Dictionary with the current {dynamic_field: val}
        :param domains: Odoo domains restricting attribute values

        :returns vals: Dictionary passed to {'value': vals} by onchange method
        """
        vals = {}
        dynamic_fields = {k: v for k, v in dynamic_fields.items() if v}
        for k, v in dynamic_fields.items():
            if not v:
                continue
            available_val_ids = domains[k][0][2]
            available_val_ids_m2m = []
            if isinstance(v, list) and self.env.context.get("is_m2m"):
                for sub_value in v:
                    available_val_ids_m2m.append(sub_value[1])
                dynamic_fields.update({k: available_val_ids_m2m})
                vals[k] = [[6, 0, available_val_ids_m2m]]
            elif v not in available_val_ids:
                dynamic_fields.update({k: []})
                vals[k] = []

            else:
                vals[k] = v
        tobe_remove_attr = []
        if (
            (
                self.env.context.get("is_action_previous")
                or self.env.context.get("is_preset")
                or self.env.context.get("is_m2m")
            )
            and config_session_id
            and config_session_id.value_ids
        ):
            session_attrb = config_session_id.value_ids
            product_tmpl_attrb = config_session_id.product_tmpl_id.attribute_line_ids
            dynamic_fields2 = {}
            restricted_attrs = []
            for tmpl_attr in product_tmpl_attrb:
                if not tmpl_attr.custom:
                    sess_attrs = session_attrb.filtered(
                        lambda value: value.attribute_id.id == tmpl_attr.attribute_id.id
                    )
                    for sess_attr in sess_attrs:
                        dyn_key = "__attribute_" + str(sess_attr.attribute_id.id)
                        product_tmpl_configs_attrs = (
                            config_session_id.product_tmpl_id.config_line_ids.filtered(
                                lambda line: line.attribute_line_id.attribute_id.id
                                == sess_attr.attribute_id.id
                            )
                        )
                        product_tmpl_restricted_attrs = (
                            config_session_id.product_tmpl_id.config_line_ids.mapped(
                                "domain_id.domain_line_ids"
                            ).mapped("attribute_id")
                        )
                        restricted_attrs = (
                            product_tmpl_configs_attrs.ids
                            + product_tmpl_restricted_attrs.ids
                        )
                        restricted_attrs = list(set(restricted_attrs))
                        if (
                            self.env.context.get("is_action_previous")
                            or self.env.context.get("is_preset")
                            and not self._context.get("is_m2m", False)
                        ):
                            if (
                                sess_attr
                                and sess_attr.attribute_id.id
                                in config_session_id.product_tmpl_id.config_line_ids.mapped(
                                    "attribute_line_id.attribute_id"
                                ).ids
                            ):
                                if dynamic_fields.get(dyn_key) == None or (
                                    dynamic_fields.get(dyn_key)
                                    and int(dynamic_fields.get(dyn_key))
                                    not in session_attrb.ids
                                ):
                                    tobe_remove_attr.append(sess_attr.id)
                                dynamic_fields2.update({dyn_key: sess_attr.id})
                            else:
                                if (
                                    sess_attr
                                    and dyn_key in dynamic_fields
                                    and dynamic_fields.get(dyn_key)
                                    and (
                                        int(dynamic_fields.get(dyn_key))
                                        not in session_attrb.ids
                                        or dynamic_fields.get(dyn_key) == None
                                    )
                                ):
                                    tobe_remove_attr.append(sess_attr.id)
                        elif (
                            self._context.get("is_m2m", False)
                            and dyn_key in dynamic_fields
                        ):
                            remove_value = dynamic_fields.get(dyn_key)
                            if isinstance(remove_value, int):
                                remove_value = [remove_value]
                            m2m_attrb_values = session_attrb.filtered(
                                lambda value: value.id in remove_value
                            )
                            if m2m_attrb_values:
                                tobe_remove_attr.extend(m2m_attrb_values.ids)
            origin_updated_fields = set(dynamic_fields)
            to_updated_fields = set(dynamic_fields2)
            updated_fields = to_updated_fields - origin_updated_fields
            for fi in updated_fields:
                dynamic_fields.update({fi: []})
                vals.update({fi: []})
        final_cfg_val_ids = list(dynamic_fields.values())
        vals.update(
            self.with_context(tobe_remove_attr=tobe_remove_attr).get_onchange_vals(
                final_cfg_val_ids, config_session_id
            )
        )
        # To solve the Multi selection problem removing extra []
        if "value_ids" in vals:
            val_ids = vals["value_ids"][0]
            vals["value_ids"] = [[val_ids[0], val_ids[1], tools.flatten(val_ids[2])]]
        return vals

    def apply_onchange_values(self, values, field_name, field_onchange):
        """Called from web-controller
        - original onchage return M2o values in formate
        (attr-value.id, attr-value.name) but on website
        we need only attr-value.id"""
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
        # TODO: VP Need to Check
        # if values.get("value_ids", []):
        #     cfg_vals = self.env["product.attribute.value"].browse(
        #         values.get("value_ids", [])[0][2]
        #     )
        if not cfg_vals:
            cfg_vals = self.value_ids

        field_type = type(field_name)
        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")
        local_field_name = field_name and field_name[0].startswith(field_prefix)
        local_custom_field = field_name and field_name[0].startswith(
            custom_field_prefix
        )
        if field_type == list and (not local_field_name and not local_custom_field):
            values = self._remove_dynamic_fields(values)
            res = super().onchange(values, field_name, field_onchange)
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

        dynamic_fields = {k: v for k, v in values.items() if k.startswith(field_prefix)}
        # self.dyn_field_2_value = False
        # Get the unstored values from the client view
        for k, v in dynamic_fields.items():
            attr_id = int(k.split(field_prefix)[1])
            valve_ids = self.env["product.attribute.value"]
            if isinstance(v, list):
                for att in v:
                    valve_ids |= product_tmpl_id.config_line_ids.filtered(
                        lambda line: int(att[1])
                        in line.domain_id.domain_line_ids.value_ids.ids
                    ).mapped("value_ids")
            else:
                valve_ids = product_tmpl_id.config_line_ids.filtered(
                    lambda line: int(v) in line.domain_id.domain_line_ids.value_ids.ids
                ).mapped("value_ids")

            self.domain_attr_2_ids = [(6, 0, valve_ids.ids)]

            line_attributes = cfg_step.attribute_line_ids.mapped("attribute_id")
            if not cfg_step or attr_id in line_attributes.ids:
                view_attribute_ids.add(attr_id)
            else:
                continue
            if not v:
                continue
            if isinstance(v, list):
                for a in v:
                    view_val_ids.add(a[1])
            elif isinstance(v, int):
                view_val_ids.add(v)

        # Clear all DB values belonging to attributes changed in the wizard
        cfg_vals = cfg_vals.filtered(
            lambda v: v.attribute_id.id not in view_attribute_ids
        )
        # Combine database values with wizard values_available
        cfg_val_ids = cfg_vals.ids + list(view_val_ids)

        domains = self.get_onchange_domains(
            values, cfg_val_ids, product_tmpl_id, config_session_id
        )
        if domains:
            for key, value in domains.items():
                if [key] == field_name:
                    if len(domains) == 1:
                        self.dyn_field_value = key
                        self.domain_attr_ids = [(6, 0, value[0][2])]
                    else:
                        self.dyn_field_2_value = key
                        self.domain_attr_2_ids = [(6, 0, value[0][2])]

                    continue
                elif values and value[0][2]:
                    self.dyn_field_2_value = key
                    self.domain_attr_2_ids = [(6, 0, value[0][2])]
        vals = self.get_form_vals(
            dynamic_fields=dynamic_fields,
            domains=domains,
            product_tmpl_id=product_tmpl_id,
            config_session_id=config_session_id,
        )
        return {"value": vals, "domain": domains}

    def onchange(self, values, field_name, field_onchange):
        """Override the onchange wrapper to return domains to dynamic
        fields as onchange isn't triggered for non-db fields
        """
        onchange_values = self.apply_onchange_values(
            values=values, field_name=field_name, field_onchange=field_onchange
        )
        field_prefix = self._prefixes.get("field_prefix")
        vals = onchange_values.get("value", {})
        for key, val in vals.items():
            if isinstance(val, int) and key.startswith(field_prefix):
                att_val = self.env["product.attribute.value"].browse(val)
                vals[key] = (att_val.id, att_val.name)
        return onchange_values

    config_session_id = fields.Many2one(
        required=True,
        ondelete="cascade",
        comodel_name="product.config.session",
        string="Configuration Session",
    )
    attribute_line_ids = fields.One2many(
        comodel_name="product.template.attribute.line",
        compute="_compute_attr_lines",
        string="Attributes",
        readonly=True,
        store=False,
    )
    config_step_ids = fields.Many2many(
        comodel_name="product.config.step",
        relation="product_config_config_steps_rel",
        column1="config_wiz_id",
        column2="config_step_id",
        string="Configuration Steps",
        readonly=True,
        store=False,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        readonly=True,
        string="Product Variant",
        help="Set only when re-configuring a existing variant",
    )
    product_img = fields.Binary(compute="_compute_cfg_image", readonly=True)
    state = FreeSelection(
        selection="get_state_selection", default="select", string="State"
    )
    domain_attr_ids = fields.Many2many(
        "product.attribute.value",
        "domain_attrs_values_rel",
        "wiz_id",
        "attribute_id",
        string="Domain",
    )

    dyn_field_value = fields.Char()

    domain_attr_2_ids = fields.Many2many(
        "product.attribute.value",
        "domain_attrs_2_values_rel",
        "wiz_id",
        "attribute_id",
        string="Domain",
    )
    dyn_field_2_value = fields.Char()

    @api.onchange("state")
    def _onchange_state(self):
        """Save values when change state of wizard by clicking on statusbar"""
        if self.env.context.get("allow_preset_selection"):
            self = self.with_context(allow_preset_selection=False)
        if self.config_session_id:
            self.config_session_id._origin.write(
                {
                    "value_ids": [[6, 0, self.value_ids.ids]],
                    "config_step": self.state,
                }
            )

    @api.onchange("product_preset_id")
    def _onchange_product_preset(self):
        """Set value ids as from product preset"""
        preset_id = self.product_preset_id
        if not preset_id and self.env.context.get("preset_values"):
            preset_id = self.env.context.get("preset_values").get("product_preset_id")
            preset_id = self.env["product.product"].browse(preset_id)
        pta_value_ids = preset_id.product_template_attribute_value_ids
        attr_value_ids = pta_value_ids.mapped("product_attribute_value_id")
        self.value_ids = attr_value_ids
        self.price = (
            preset_id and preset_id.lst_price or self.product_tmpl_id.list_price
        )

    @api.model
    def get_field_default_attrs(self):
        return {
            "company_dependent": False,
            "depends": (),
            "groups": False,
            "readonly": False,
            "manual": False,
            "required": False,
            "searchable": False,
            "store": False,
            "translate": False,
        }

    @api.model
    def fields_get(self, allfields=None, write_access=True, attributes=None):
        """Artificially inject fields which are dynamically created using the
        attribute_ids on the product.template as reference"""

        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")

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

        cfg_step_lines = wiz.product_tmpl_id.config_step_line_ids

        try:
            # Get only the attribute lines for the next step if defined
            active_step_line = cfg_step_lines.filtered(
                lambda line: line.id == int(active_step_id)
            )
            if active_step_line:
                attribute_lines = active_step_line.attribute_line_ids
            else:
                attribute_lines = wiz.product_tmpl_id.attribute_line_ids
        except Exception:
            # If no configuration steps exist then get all attribute lines
            attribute_lines = wiz.product_tmpl_id.attribute_line_ids

        attribute_lines = wiz.product_tmpl_id.attribute_line_ids

        # Generate relational fields with domains restricting values to
        # the corresponding attributes

        # Default field attributes
        default_attrs = self.get_field_default_attrs()

        for line in attribute_lines:
            attribute = line.attribute_id
            value_ids = line.value_ids.ids

            value_ids = wiz.config_session_id.values_available(check_val_ids=value_ids)

            # If attribute lines allows custom values add the
            # generic "Custom" attribute.value to the list of options
            if line.custom:
                config_session_obj = self.env["product.config.session"]
                custom_val = config_session_obj.get_custom_value_id()
                value_ids.append(custom_val.id)

                # Set default field type
                field_type = "char"

                if attribute.custom_type:
                    field_types = FIELD_TYPES
                    custom_type = line.attribute_id.custom_type
                    # TODO: Rename int to integer in values
                    if custom_type == "integer":
                        field_type = "integer"
                    elif custom_type in [f[0] for f in field_types]:
                        field_type = custom_type

                # TODO: Implement custom string on custom attribute
                res[custom_field_prefix + str(attribute.id)] = dict(
                    default_attrs,
                    string="Custom",
                    type=field_type,
                    sequence=line.sequence,
                )

            # Add the dynamic field to the result set using the convention
            # "__attribute_DBID" to later identify and extract it
            res[field_prefix + str(attribute.id)] = dict(
                default_attrs,
                type="many2many" if line.multi else "many2one",
                domain=[("id", "in", value_ids)],
                string=line.attribute_id.name,
                relation="product.attribute.value",
                # sequence=line.sequence,
            )
        return res

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        """Generate view dynamically using attributes stored on the
        product.template"""
        if view_type == "form" and not view_id:
            view_ext_id = "product_configurator.product_configurator_form"
            view_id = self.env.ref(view_ext_id).id
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        wizard_id = self._find_wizard_context()

        wizard_model = res["model"]
        if not wizard_id or not res["models"].get(wizard_model):
            return res

        wiz = self.browse(wizard_id)

        # Get updated fields including the dynamic ones
        fields = self.fields_get()

        # Include all dynamic fields in the view
        dynamic_field_prefixes = tuple(self._prefixes.values())

        dynamic_fields = {
            k: v for k, v in fields.items() if k.startswith(dynamic_field_prefixes)
        }

        # res["fields"].update(dynamic_fields)
        models = dict(res["models"])
        models[wizard_model] = models[wizard_model] + tuple(dynamic_fields.keys())
        res["models"] = frozendict(models)

        mod_view = self.add_dynamic_fields(res, dynamic_fields, wiz)

        # Update result dict from super with modified view
        res.update({"arch": etree.tostring(mod_view)})
        return res

    # TODO: NC: Need to improve this method
    # @api.model
    # def setup_modifiers(self, node, field=None):
    #     """Processes node attributes and field descriptors to generate
    #     the ``modifiers`` node attribute and set it on the provided node.
    #
    #     Alters its first argument in-place.
    #
    #     :param node: ``field`` node from an OpenERP view
    #     :type node: lxml.etree._Element
    #     :param dict field: field descriptor corresponding to the provided node
    #     :param dict context: execution context used to evaluate node attributes
    #     :param bool current_node_path: triggers the ``column_invisible`` code
    #                               path (separate from ``invisible``): in
    #                               tree view there are two levels of
    #                               invisibility, cell content (a column is
    #                               present but the cell itself is not
    #                               displayed) with ``invisible`` and column
    #                               invisibility (the whole column is
    #                               hidden) with ``column_invisible``.
    #     :returns: nothing
    #     """
    #     modifiers = {}
    #     if field is not None:
    #         transfer_field_to_modifiers(field=field, modifiers=modifiers)
    #     transfer_node_to_modifiers(node=node, modifiers=modifiers)
    #     transfer_modifiers_to_node(modifiers=modifiers, node=node)

    def prepare_attrs_initial(
        self, attr_lines, field_prefix, custom_field_prefix, dynamic_fields, wiz
    ):
        cfg_step_ids = []
        for attr_line in attr_lines:
            attribute_id = attr_line.attribute_id.id
            field_name = field_prefix + str(attribute_id)
            custom_field = custom_field_prefix + str(attribute_id)

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
        return attrs, field_name, custom_field, config_steps, cfg_step_ids

    @api.model
    def add_dynamic_fields(self, res, dynamic_fields, wiz):
        """Create the configuration view using the dynamically generated
        fields in fields_get()
        """

        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")

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
                config_steps,
                cfg_step_ids,
            ) = self.prepare_attrs_initial(
                attr_line, field_prefix, custom_field_prefix, dynamic_fields, wiz
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
        return xml_view

    @api.model_create_multi
    def create(self, vals_list):
        """Sets the configuration values of the product_id if given (if any).
        This is used in reconfiguration of a existing variant"""
        for vals in vals_list:
            if "product_id" in vals:
                product = self.env["product.product"].browse(vals["product_id"])
                pta_value_ids = product.product_template_attribute_value_ids
                attr_value_ids = pta_value_ids.mapped("product_attribute_value_id")
                vals.update(
                    {
                        "product_tmpl_id": product.product_tmpl_id.id,
                        "value_ids": [(6, 0, attr_value_ids.ids)],
                    }
                )

            # Get existing session for this product_template or create a new one
            session = self.env["product.config.session"].create_get_session(
                product_tmpl_id=int(vals.get("product_tmpl_id"))
            )
            vals.update({"user_id": self.env.uid, "config_session_id": session.id})
            wz_value_ids = vals.get("value_ids", [])
            if session.value_ids:
                vals.update({"value_ids": [(6, 0, session.value_ids.ids)]})
        return super().create(vals_list)

    def read(self, fields=None, load="_classic_read"):
        """Remove dynamic fields from the fields list and update the
        returned values with the dynamic data stored in value_ids"""

        field_prefix = self._prefixes.get("field_prefix")
        custom_field_prefix = self._prefixes.get("custom_field_prefix")
        attr_vals = [f for f in fields if f.startswith(field_prefix)]
        custom_attr_vals = [f for f in fields if f.startswith(custom_field_prefix)]

        dynamic_fields = attr_vals + custom_attr_vals
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

            # Handle default values for dynamic fields on Odoo frontend
            res[0].update({field_name: False, custom_field_name: False})

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
            res[0].update(dynamic_vals)
        return res

    def write(self, vals):
        """Prevent database storage of dynamic fields and instead write values
        to database persistent value_ids field"""

        # Remove all dynamic fields from write values
        self.config_session_id.update_session_configuration_value(
            vals=vals, product_tmpl_id=self.product_tmpl_id
        )
        vals = self._remove_dynamic_fields(vals)

        return super().write(vals)

    def action_next_step(self):
        """Proceeds to the next step of the configuration process. This usually
        implies the next configuration step (if any) defined via the
        config_step_line_ids on the product.template.

        More importantly it sets metadata on the context
        variable so the fields_get and fields_view_get methods can generate the
        appropriate dynamic content"""
        wizard_action = self.with_context(
            allow_preset_selection=False
        ).get_wizard_action(wizard=self)
        if not self.product_tmpl_id:
            return wizard_action

        if not self.product_tmpl_id.attribute_line_ids:
            raise ValidationError(
                _("Product Template does not have any attribute lines defined")
            )
        next_step = self.config_session_id.get_next_step(
            state=self.state,
            product_tmpl_id=self.product_tmpl_id,
            value_ids=self.config_session_id.value_ids,
            custom_value_ids=self.config_session_id.custom_value_ids,
        )
        if not next_step:
            return self.action_config_done()
        return self.open_step(step=next_step)

    def action_previous_step(self):
        """Proceeds to the next step of the configuration process. This usually
        implies the next configuration step (if any) defined via the
        config_step_line_ids on the product.template."""
        wizard_action = self.with_context(
            wizard_id=self.id, view_cache=False, allow_preset_selection=False
        ).get_wizard_action(wizard=self)
        if wizard_action.get("context") and "is_action_previous" in wizard_action.get(
            "context"
        ):
            wizard_action.get("context")["is_action_previous"] = True

        cfg_step_lines = self.product_tmpl_id.config_step_line_ids
        if not cfg_step_lines:
            self.state = "select"
            return wizard_action

        try:
            cfg_step_line_id = int(self.state)
            active_cfg_line_id = cfg_step_lines.filtered(
                lambda x: x.id == cfg_step_line_id
            ).id
        except Exception:
            active_cfg_line_id = None

        adjacent_steps = self.config_session_id.get_adjacent_steps(
            active_step_line_id=active_cfg_line_id
        )
        previous_step = adjacent_steps.get("previous_step")
        if previous_step:
            self.state = str(previous_step.id)
        else:
            self.state = "select"
        self.config_session_id.config_step = self.state
        return wizard_action

    def action_reset(self):
        """Delete wizard and configuration session then create
        a new wizard+session and return an action for the new wizard object"""
        try:
            session_product_tmpl_id = self.config_session_id.product_tmpl_id
            self.config_session_id.unlink()
        except Exception:
            session = self.env["product.config.step"]
        if session_product_tmpl_id:
            action = session_product_tmpl_id.with_context(
                dict(self.env.context)
            ).create_config_wizard(model_name=self._name, click_next=False)
            return action
        return False

    def get_wizard_action(self, view_cache=False, wizard=None):
        """Return action of wizard
        :param view_cache: Boolean (True/False)
        :param wizard: recordset of product.configurator
        :returns : dictionary
        """
        ctx = self.env.context.copy()
        ctx.update(
            {
                "view_cache": view_cache,
                "differentiator": ctx.get("differentiator", 1) + 1,
                "is_product_configurator": True,
                "is_action_previous": False,
                "is_preset": self.product_preset_id and True or False,
            }
        )
        if wizard:
            ctx.update({"wizard_id": wizard.id, "wizard_id_view_ref": wizard.id})
        wizard_action = {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "name": "Configure Product",
            "views": [
                [
                    self.env.ref("product_configurator.product_configurator_form").id,
                    "form",
                ]
            ],
            "view_mode": "form",
            "context": ctx,
            "target": "new",
        }
        if wizard:
            wizard_action.update({"res_id": wizard.id})
        if self and not self.state:
            self.state = "select"
        return wizard_action

    def open_step(self, step):
        """Open wizard step 'step'
        :param step: recordset of product.config.step.line
        """
        wizard_action = self.with_context(
            allow_preset_selection=False
        ).get_wizard_action(wizard=self)
        if not step:
            return wizard_action
        if isinstance(step, type(self.env["product.config.step.line"])):
            step = "%s" % (step.id)
        self.state = step
        self.config_session_id.config_step = step
        return wizard_action

    def action_config_done(self):
        """This method is for the final step which will be taken care by a
        separate module"""
        # This try except is too generic.
        # The create_variant routine could effectively fail for
        # a large number of reasons, including bad programming.
        # It should be refactored.
        # In the meantime, at least make sure that a validation
        # error legitimately raised in a nested routine
        # is passed through.
        step_to_open = self.config_session_id.check_and_open_incomplete_step()
        if step_to_open:
            return self.open_step(step_to_open)
        self.config_session_id.action_confirm()
        variant = self.config_session_id.product_id
        action = {
            "type": "ir.actions.act_window",
            "res_model": "product.product",
            "name": "Product Variant",
            "view_mode": "form",
            "context": dict(self.env.context, custom_create_variant=True),
            "res_id": variant.id,
        }
        return action

    def web_read(self, specification):
        values_list = super().web_read(specification)
        for field_name, field_spec in specification.items():
            field = self._fields.get(field_name)
            if field is None:
                if (
                    field_spec.get("context")
                    and "is_m2m" in field_spec.get("context")
                    and field_spec.get("context").get("is_m2m")
                ):
                    if not field_spec:
                        continue

                    co_records = self.env["product.attribute.value"]
                    if "order" in field_spec and field_spec["order"]:
                        co_records = co_records.search(
                            [("id", "in", co_records.ids)], order=field_spec["order"]
                        )
                        order_key = {
                            co_record.id: index
                            for index, co_record in enumerate(co_records)
                        }
                        for values in values_list:
                            # filter out inaccessible corecords in case of "cache pollution"
                            values[field_name] = [
                                id_ for id_ in values[field_name] if id_ in order_key
                            ]
                            values[field_name] = sorted(
                                values[field_name], key=order_key.__getitem__
                            )

                    if "context" in field_spec:
                        co_records = co_records.with_context(**field_spec["context"])
                    if "fields" in field_spec:
                        if field_spec.get("limit") is not None:
                            limit = field_spec["limit"]
                            ids_to_read = OrderedSet(
                                id_
                                for values in values_list
                                for id_ in values[field_name][:limit]
                            )
                            co_records = co_records.browse(ids_to_read)
                        x2many_data = {
                            vals["id"]: vals
                            for vals in co_records.web_read(field_spec["fields"])
                        }
                        for values in values_list:
                            if values[field_name]:
                                attribute_ids = self.env[
                                    "product.attribute.value"
                                ].browse(values[field_name])
                                x2many_data = {
                                    vals["id"]: vals
                                    for vals in attribute_ids.web_read(
                                        field_spec["fields"]
                                    )
                                }
                                values[field_name] = [
                                    x2many_data.get(id_) or {"id": id_}
                                    for id_ in x2many_data
                                ]
                            else:
                                values[field_name] = [
                                    x2many_data.get(id_) or {"id": id_}
                                    for id_ in x2many_data
                                ]
        return values_list


# class ProductConfiguratorCustomValue(models.TransientModel):
#     _name = "product.configurator.custom.value"
#     _description = "Product Configurator Custom Value"

#     attachment_ids = fields.Many2many(
#         comodel_name="ir.attachment",
#         column1="config_attachment",
#         column2="attachment_id",
#         string="Attachments",
#     )
#     attribute_id = fields.Many2one(
#         string="Attribute", comodel_name="product.attribute", required=True
#     )
#     user_id = fields.Many2one(
#         string="User",
#         comodel_name="res.users",
#         related="wizard_id.create_uid",
#         required=True,
#     )
#     value = fields.Char(string="Value")
#     wizard_id = fields.Many2one(comodel_name="product.configurator", string="Wizard")
# TODO: Current value ids to save frontend/backend session?
