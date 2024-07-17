# Copyright 2011 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# @author Raphaël VALYI <raphael.valyi@akretion.com>
# Copyright 2015 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import logging
import re

from lxml import etree
from unidecode import unidecode

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..utils.orm import setup_modifiers

_logger = logging.getLogger(__name__)


def safe_column_name(string):
    """Prevent portability problem in database column name
    with other DBMS system
    Use case : if you synchronise attributes with other applications"""
    string = unidecode(string.replace(" ", "_").lower())
    return re.sub(r"[^0-9a-z_]", "", string)


class AttributeAttribute(models.Model):
    _name = "attribute.attribute"
    _description = "Attribute"
    _inherits = {"ir.model.fields": "field_id"}
    _order = "sequence_group,sequence,name"

    field_id = fields.Many2one(
        "ir.model.fields", "Ir Model Fields", required=True, ondelete="cascade"
    )

    nature = fields.Selection(
        [("custom", "Custom"), ("native", "Native")],
        string="Attribute Nature",
        required=True,
        default="custom",
        store=True,
    )

    attribute_type = fields.Selection(
        [
            ("char", "Char"),
            ("text", "Text"),
            ("select", "Select"),
            ("multiselect", "Multiselect"),
            ("boolean", "Boolean"),
            ("integer", "Integer"),
            ("date", "Date"),
            ("datetime", "Datetime"),
            ("binary", "Binary"),
            ("float", "Float"),
        ],
    )

    serialized = fields.Boolean(
        help="""If serialized, the attribute's field will be stored in the serialization
            field 'x_custom_json_attrs' (i.e. a JSON containing all the serialized
            fields values) instead of creating a new SQL column for this
            attribute's field. Useful to increase speed requests if creating a
            high number of attributes.""",
    )

    option_ids = fields.One2many(
        "attribute.option", "attribute_id", "Attribute Options"
    )

    create_date = fields.Datetime("Created date", readonly=True)

    relation_model_id = fields.Many2one(
        "ir.model", "Relational Model", ondelete="cascade"
    )

    widget = fields.Char(help="Specify widget to add to the field on the views.")

    required_on_views = fields.Boolean(
        "Required (on views)",
        help="If activated, the attribute will be mandatory on the views, "
        "but not in the database",
    )

    attribute_set_ids = fields.Many2many(
        comodel_name="attribute.set",
        string="Attribute Sets",
        relation="rel_attribute_set",
        column1="attribute_id",
        column2="attribute_set_id",
    )

    attribute_group_id = fields.Many2one(
        "attribute.group", "Attribute Group", required=True, ondelete="cascade"
    )

    sequence_group = fields.Integer(
        "Sequence of the Group",
        related="attribute_group_id.sequence",
        help="The sequence of the group",
        store="True",
    )

    sequence = fields.Integer(
        "Sequence in Group", help="The attribute's order in his group"
    )

    @api.model
    def _build_attribute_field(self, attribute_egroup):
        """Add field into given attribute group.

        Conditional invisibility based on its attribute sets.
        """
        self.ensure_one()
        kwargs = {"name": f"{self.name}"}
        if self.attribute_set_ids:
            attribute_sets = self.attribute_set_ids.ids
            kwargs["invisible"] = f"attribute_set_id not in {attribute_sets}"
            if self.required or self.required_on_views:
                kwargs["required"] = f"attribute_set_id in {attribute_sets}"
        if self.widget:
            kwargs["widget"] = self.widget

        if self.readonly:
            kwargs["readonly"] = str(True)

        if self.ttype in ["many2one", "many2many"]:
            if self.relation_model_id:
                # TODO update related attribute.option in cascade to allow
                # attribute.option creation from the field.
                kwargs["options"] = "{'no_create': True}"
                # attribute.domain is a string, it may be an empty list
                try:
                    domain = ast.literal_eval(self.domain)
                except ValueError:
                    domain = None

                if domain:
                    kwargs["domain"] = self.domain
                else:
                    # Display only options linked to an existing object
                    ids = [op.value_ref.id for op in self.option_ids if op.value_ref]
                    kwargs["domain"] = f"[('id', 'in', {ids})]"
                # Add color options if the attribute's Relational Model
                # has a color field
                relation_model_obj = self.env[self.relation_model_id.model]
                if "color" in relation_model_obj.fields_get().keys():
                    kwargs["options"] = "{'color_field': 'color', 'no_create': True}"
            elif self.nature == "custom":
                # Define field's domain and context with attribute's id to go along with
                # Attribute Options search and creation
                kwargs["domain"] = f"[('attribute_id', '=', {self.id})]"
                kwargs["context"] = f"{{'default_attribute_id': {self.id}}}"
            elif self.nature != "custom":
                kwargs["context"] = self._get_native_field_context()

        if self.ttype == "text":
            # Display field label above his value
            field_title = etree.SubElement(
                attribute_egroup,
                "b",
                colspan="2",
                invisible=kwargs["invisible"],
            )
            field_title.text = self.field_description
            kwargs["nolabel"] = "1"
            kwargs["colspan"] = "2"
            setup_modifiers(field_title)
        efield = etree.SubElement(attribute_egroup, "field", **kwargs)
        setup_modifiers(efield)

    def _get_native_field_context(self):
        return str(self.env[self.field_id.model]._fields[self.field_id.name].context)

    def _build_attribute_eview(self):
        """Generate group element for all attributes in the current recordset.

        Return an 'attribute_eview' including all the Attributes (in the current
        recorset 'self') distributed in different 'attribute_egroup' for each
        Attribute's group.
        """
        attribute_eview = etree.Element("group", name="attributes_group", col="4")
        groups = []
        for attribute in self:
            att_group = attribute.attribute_group_id
            att_group_name = att_group.name.capitalize()
            if att_group in groups:
                xpath = f".//group[@string='{att_group_name}']"
                attribute_egroup = attribute_eview.find(xpath)
            else:
                att_set_ids = []
                for att in att_group.attribute_ids:
                    att_set_ids += att.attribute_set_ids.ids
                # Hide the Group if none of its attributes are in
                # the destination object's Attribute set
                hide_domain = f"attribute_set_id not in {list(set(att_set_ids))}"
                attribute_egroup = etree.SubElement(
                    attribute_eview,
                    "group",
                    string=att_group_name,
                    colspan="2",
                    invisible=f"{hide_domain}",
                )
                groups.append(att_group)

            setup_modifiers(attribute_egroup)
            attribute_with_env = (
                attribute.sudo() if attribute.check_access_rights("read") else self
            )
            attribute_with_env._build_attribute_field(attribute_egroup)

        return attribute_eview

    @api.onchange("model_id")
    def onchange_model_id(self):
        return {"domain": {"field_id": [("model_id", "=", self.model_id.id)]}}

    @api.onchange("field_description")
    def onchange_field_description(self):
        if self.field_description and not self.create_date:
            self.name = unidecode("x_" + safe_column_name(self.field_description))

    @api.onchange("name")
    def onchange_name(self):
        name = self.name
        if not name.startswith("x_"):
            self.name = f"x_{name}"

    @api.onchange("attribute_type")
    def onchange_attribute_type(self):
        if self.attribute_type == "multiselect":
            self.widget = "many2many_tags"

    @api.onchange("relation_model_id")
    def _onchange_relation_model_id(self):
        """Remove selected options as they would be inconsistent"""
        self.option_ids = [(5, 0)]

    @api.onchange("domain")
    def _onchange_domain(self):
        if self.domain not in ["", False]:
            try:
                ast.literal_eval(self.domain)
            except ValueError:
                raise ValidationError(
                    _(
                        "`%(domain)s` is an invalid Domain name.\n"
                        "Specify a Python expression defining a list of triplets.\n"
                        "For example : `[('color', '=', 'red')]`",
                        domain=self.domain,
                    )
                ) from ValueError
            # Remove selected options as the domain will predominate on actual options
            if self.domain != "[]":
                self.option_ids = [(5, 0)]

    def button_add_options(self):
        self.ensure_one()
        # Before adding another option delete the ones which are linked
        # to a deleted object
        for option in self.option_ids:
            if not option.value_ref:
                option.unlink()
        # Then open the Options Wizard which will display an 'opt_ids' m2m field related
        # to the 'relation_model_id' model
        return {
            "context": dict(self.env.context, attribute_id=self.id),
            "name": _("Options Wizard"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "attribute.option.wizard",
            "type": "ir.actions.act_window",
            "target": "new",
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Create an attribute.attribute

        - In case of a new "custom" attribute, a new field object 'ir.model.fields' will
        be created as this model "_inherits" 'ir.model.fields'.
        So we need to add here the mandatory 'ir.model.fields' instance's attributes to
        the new 'attribute.attribute'.

        - In case of a new "native" attribute, it will be linked to an existing
        field object 'ir.model.fields' (through "field_id") that cannot be modified.
        That's why we remove all the 'ir.model.fields' instance's attributes values
        from `vals` before creating our new 'attribute.attribute'.

        """
        for vals in vals_list:
            if vals.get("nature") == "native":
                # Remove all the values that can modify the related native field
                # before creating the new 'attribute.attribute'
                for key in set(vals).intersection(self.env["ir.model.fields"]._fields):
                    del vals[key]
                continue

            if vals.get("relation_model_id"):
                model = self.env["ir.model"].browse(vals["relation_model_id"])
                relation = model.model
            else:
                relation = "attribute.option"

            attr_type = vals.get("attribute_type")

            if attr_type == "select":
                vals["ttype"] = "many2one"
                vals["relation"] = relation

            elif attr_type == "multiselect":
                vals["ttype"] = "many2many"
                vals["relation"] = relation
                # Specify the relation_table's name in case of m2m not serialized
                # to avoid creating the same default relation_table name
                # for any attribute
                # linked to the same attribute.option
                # or relation_model_id's model.
                if not vals.get("serialized"):
                    att_model_id = self.env["ir.model"].browse(vals["model_id"])
                    table_name = (
                        "x_"
                        + att_model_id.model.replace(".", "_")
                        + "_"
                        + vals["name"]
                        + "_"
                        + relation.replace(".", "_")
                        + "_rel"
                    )
                    # avoid too long relation_table names
                    vals["relation_table"] = table_name[0:60]

            else:
                vals["ttype"] = attr_type

            if vals.get("serialized"):
                field_obj = self.env["ir.model.fields"]

                serialized_fields = field_obj.search(
                    [
                        ("ttype", "=", "serialized"),
                        ("model_id", "=", vals["model_id"]),
                        ("name", "=", "x_custom_json_attrs"),
                    ]
                )

                if serialized_fields:
                    vals["serialization_field_id"] = serialized_fields[0].id

                else:
                    f_vals = {
                        "name": "x_custom_json_attrs",
                        "field_description": "Serialized JSON Attributes",
                        "ttype": "serialized",
                        "model_id": vals["model_id"],
                    }

                    vals["serialization_field_id"] = (
                        field_obj.with_context(manual=True).create(f_vals).id
                    )

            vals["state"] = "manual"
        return super().create(vals_list)

    def _delete_related_option_wizard(self, option_vals):
        """Delete related attribute's options wizards."""
        self.ensure_one()
        for option_change in option_vals:
            if option_change[0] == 2:
                self.env["attribute.option.wizard"].search(
                    [("attribute_id", "=", self.id)]
                ).unlink()
                break

    def _delete_old_fields_options(self, options):
        """Delete outdated attribute's field values on existing records."""
        self.ensure_one()
        custom_field = self.name
        for obj in self.env[self.model].search([]):
            if obj.fields_get(custom_field):
                for value in obj[custom_field]:
                    if value not in options:
                        if self.attribute_type == "select":
                            obj.write({custom_field: False})
                        elif self.attribute_type == "multiselect":
                            obj.write({custom_field: [(3, value.id, 0)]})

    def write(self, vals):
        # Prevent from changing Attribute's type
        if "attribute_type" in list(vals.keys()):
            if self.search_count(
                [
                    ("attribute_type", "!=", vals["attribute_type"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    _(
                        "Can't change the type of an attribute. "
                        "Please create a new one."
                    )
                )
            else:
                vals.pop("attribute_type")
        # Prevent from changing relation_model_id for multiselect Attributes
        # as the values of the existing many2many Attribute fields won't be
        # deleted if changing relation_model_id
        if "relation_model_id" in list(vals.keys()):
            if self.search_count(
                [
                    ("relation_model_id", "!=", vals["relation_model_id"]),
                    ("id", "in", self.ids),
                ]
            ):
                raise ValidationError(
                    _(
                        """Can't change the attribute's Relational Model in order to
                        avoid conflicts with existing objects using this attribute.
                        Please create a new one."""
                    )
                )
        # Prevent from changing 'Serialized'
        if "serialized" in list(vals.keys()):
            if self.search_count(
                [("serialized", "!=", vals["serialized"]), ("id", "in", self.ids)]
            ):
                raise ValidationError(
                    _(
                        """It is not allowed to change the boolean 'Serialized'.
                        A serialized field can not be change to non-serialized \
                        and vice versa."""
                    )
                )
        # Set the new values to self
        res = super().write(vals)

        for att in self:
            options = att.option_ids
            if att.relation_model_id:
                options = self.env[att.relation_model_id.model]
                if "option_ids" in list(vals.keys()):
                    # Delete related attribute.option.wizard if an attribute.option
                    # has been deleted
                    att._delete_related_option_wizard(vals["option_ids"])
                    # If there is still some attribute.option available, override
                    # 'options' with the objects they are refering to.
                    options = options.search(
                        [("id", "in", [op.value_ref.id for op in att.option_ids])]
                    )
                if "domain" in list(vals.keys()):
                    try:
                        domain = ast.literal_eval(att.domain)
                    except ValueError:
                        domain = []
                    if domain:
                        # If there is a Valid domain not null, it means that there is
                        # no more attribute.option.
                        options = options.search(domain)
            # Delete attribute's field values in the objects using our attribute
            # as a field, if these values are not in the new Domain or Options list
            if {"option_ids", "domain"} & set(vals.keys()):
                att._delete_old_fields_options(options)

        return res

    def unlink(self):
        """Delete the Attribute's related field when deleting a custom Attribute"""
        fields_to_remove = self.filtered(lambda s: s.nature == "custom").mapped(
            "field_id"
        )
        res = super().unlink()
        fields_to_remove.unlink()
        return res
