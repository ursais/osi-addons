# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json


def transfer_field_to_modifiers(field, modifiers):
    default_values = {}
    state_exceptions = {}
    for attr in ("invisible", "readonly", "required", "column_invisible"):
        state_exceptions[attr] = []
        default_values[attr] = field.get(attr)
    for state, modifs in field.get("states", {}).items():
        for modif in modifs:
            if default_values[modif[0]] != modif[1]:
                state_exceptions[modif[0]].append(state)

    for attr, default_value in default_values.items():
        if state_exceptions[attr]:
            modifiers[attr] = [
                ("state", "not in" if default_value else "in", state_exceptions[attr])
            ]
        else:
            modifiers[attr] = default_value


# Don't deal with groups, it is done by check_group().
# Need the context to evaluate the invisible attribute on tree views.
# For non-tree views, the context shouldn't be given.
def transfer_node_to_modifiers(node, modifiers, context=None, in_tree_view=False):
    if node.get("required"):
        modifiers["required"] = node.get("required")
    if node.get("invisible"):
        modifiers["invisible"] = node.get("invisible")
    if node.get("readonly"):
        modifiers["readonly"] = node.get("readonly")
    if node.get("column_invisible"):
        modifiers["column_invisible"] = node.get("column_invisible")


def simplify_modifiers(modifiers):
    for a in ("invisible", "readonly", "required", "column_invisible"):
        if a in modifiers and not modifiers[a]:
            del modifiers[a]


def transfer_modifiers_to_node(modifiers, node):
    if modifiers:
        simplify_modifiers(modifiers)
        node.set("modifiers", json.dumps(modifiers))


def setup_modifiers(node, field=None, context=None, in_tree_view=False):
    """Generate ``modifiers``  from node attributes and fields descriptors.
    Alters its first argument in-place.
    :param node: ``field`` node from an OpenERP view
    :type node: lxml.etree._Element
    :param dict field: field descriptor corresponding to the provided node
    :param dict context: execution context used to evaluate node attributes
    :param bool in_tree_view: triggers the ``column_invisible`` code
                              path (separate from ``invisible``): in
                              tree view there are two levels of
                              invisibility, cell content (a column is
                              present but the cell itself is not
                              displayed) with ``invisible`` and column
                              invisibility (the whole column is
                              hidden) with ``column_invisible``.
    :returns: None
    """
    modifiers = {}
    if field is not None:
        transfer_field_to_modifiers(field, modifiers)
    transfer_node_to_modifiers(
        node, modifiers, context=context, in_tree_view=in_tree_view
    )
    transfer_modifiers_to_node(modifiers, node)
