from odoo.tools.misc import file_path
import csv
import logging

from odoo import fields
from odoo.addons.ol_base.fields.fields import NullableInteger, NullableFloat

# Ensure these types are known at import time
fields.Field.by_type.setdefault("nullable_integer", NullableInteger)
fields.Field.by_type.setdefault("nullable_float", NullableFloat)

_logger = logging.getLogger(__name__)


def import_attribute_sets(env):
    """Import Attribute Sets from CSV"""
    csv_path = file_path("ol_pim/data/attribute.set.csv")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            search_domain = [
                "|",
                ("code", "=", row["code"]),
                "&",
                ("code", "=", False),
                ("name", "=", row["name"]),
            ]
            existing_record = env["attribute.set"].search(search_domain, limit=1)

            if existing_record:
                # Compare values and update if necessary
                update_fields = {}
                if existing_record.name != row["name"]:
                    update_fields["name"] = row["name"]
                if existing_record.code != row["code"]:
                    update_fields["code"] = row["code"]
                if update_fields:
                    _logger.info(f"Updating Attribute Set: {row['name']}")
                    existing_record.write(update_fields)
                continue

            # Convert model_id from name to ID
            if "model_id" in row and row["model_id"]:
                model_record = env["ir.model"].search(
                    [("model", "=", row["model_id"])], limit=1
                )
                if model_record:
                    row["model_id"] = model_record.id
                else:
                    _logger.warning(
                        f"ir.model '{row['model_id']}' not found, skipping record."
                    )
                    continue

            env["attribute.set"].create(row)
            _logger.info(f"Created Attribute Set: {row['name']}")


def import_attribute_groups(env):
    """Import Attribute Groups from CSV"""
    csv_path = file_path("ol_pim/data/attribute.group.csv")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            search_domain = [
                "|",
                ("code", "=", row["code"]),
                "&",
                ("code", "=", False),
                ("name", "=", row["name"]),
            ]
            existing_record = env["attribute.group"].search(search_domain, limit=1)

            if existing_record:
                # Compare values and update if necessary
                update_fields = {}
                if existing_record.name != row["name"]:
                    update_fields["name"] = row["name"]

                # Check and safely convert sequence
                try:
                    update_fields["sequence"] = (
                        int(row["sequence"]) if row["sequence"].isdigit() else 10
                    )
                except ValueError:
                    update_fields["sequence"] = 10

                if existing_record.code != row["code"]:
                    update_fields["code"] = row["code"]
                if update_fields:
                    _logger.info(f"Updating Attribute Group: {row['name']}")
                    existing_record.write(update_fields)
                continue

            # Convert model_id from name to ID
            if "model_id" in row and row["model_id"]:
                model_record = env["ir.model"].search(
                    [("model", "=", row["model_id"])], limit=1
                )
                if model_record:
                    row["model_id"] = model_record.id
                else:
                    _logger.warning(
                        f"ir.model '{row['model_id']}' not found, skipping record."
                    )
                    continue

            env["attribute.group"].create(row)
            _logger.info(f"Created Attribute Group: {row['name']}")


def import_attributes(env):
    """Import Attributes from CSV"""
    csv_path = file_path("ol_pim/data/attribute.attribute.csv")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            search_domain = [
                "|",
                ("code", "=", row["code"]),
                "&",
                ("code", "=", False),
                ("name", "=", row["name"]),
            ]
            existing_record = env["attribute.attribute"].search(search_domain, limit=1)

            if existing_record:
                # Compare values and update if necessary
                update_fields = {}
                if existing_record.field_description != row["field_description"]:
                    update_fields["field_description"] = row["field_description"]
                if existing_record.attribute_type != row["attribute_type"]:
                    update_fields["attribute_type"] = row["attribute_type"]
                if existing_record.widget != row["widget"]:
                    update_fields["widget"] = row["widget"]
                if existing_record.domain != row["domain"]:
                    update_fields["domain"] = row["domain"]
                if existing_record.required != (row["required"] == "TRUE"):
                    update_fields["required"] = row["required"] == "TRUE"

                # Check and safely convert sequence
                try:
                    update_fields["sequence"] = (
                        int(row["sequence"]) if row["sequence"].isdigit() else 10
                    )
                except ValueError:
                    update_fields["sequence"] = 10

                if existing_record.code != row["code"]:
                    update_fields["code"] = row["code"]

                # Compare attribute_set_ids (Many2many field)
                if "attribute_set_ids" in row and row["attribute_set_ids"]:
                    set_names = row["attribute_set_ids"].split(
                        ","
                    )  # Split names by comma
                    set_ids = (
                        env["attribute.set"].search([("name", "in", set_names)]).ids
                    )

                    # Ensure set_ids is a list of integers
                    existing_set_ids = existing_record.attribute_set_ids.ids
                    if set_ids != existing_set_ids:
                        update_fields["attribute_set_ids"] = [(6, 0, set_ids)]

                # Compare attribute_group_id (Many2one field)
                if "attribute_group_id" in row and row["attribute_group_id"]:
                    group_record = env["attribute.group"].search(
                        [("name", "=", row["attribute_group_id"])], limit=1
                    )
                    if group_record:
                        new_group_id = group_record.id
                        if existing_record.attribute_group_id.id != new_group_id:
                            update_fields["attribute_group_id"] = new_group_id
                    else:
                        _logger.warning(
                            f"Attribute Group '{row['attribute_group_id']}' not found, skipping record."
                        )
                        continue

                if update_fields:
                    _logger.info(f"Updating Attribute: {row['field_description']}")
                    existing_record.write(update_fields)
                continue

            # Convert model_id from name to ID
            if "model_id" in row and row["model_id"]:
                model_record = env["ir.model"].search(
                    [("model", "=", row["model_id"])], limit=1
                )
                if model_record:
                    row["model_id"] = model_record.id
                else:
                    _logger.warning(
                        f"ir.model '{row['model_id']}' not found, skipping record."
                    )
                    continue

            # Convert attribute_group_id from name to ID
            if "attribute_group_id" in row and row["attribute_group_id"]:
                group_record = env["attribute.group"].search(
                    [("name", "=", row["attribute_group_id"])], limit=1
                )
                if group_record:
                    row["attribute_group_id"] = group_record.id
                else:
                    _logger.warning(
                        f"Attribute Group '{row['attribute_group_id']}' not found, skipping record."
                    )
                    continue

            # Convert attribute_set_ids from names to IDs (Many2many)
            if "attribute_set_ids" in row and row["attribute_set_ids"]:
                set_names = row["attribute_set_ids"].split(",")  # Split names by comma
                set_ids = env["attribute.set"].search([("name", "in", set_names)]).ids

                # Ensure set_ids is a list of integers
                if set_ids:
                    row["attribute_set_ids"] = [(6, 0, set_ids)]

            # Convert relation_model_id from name to ID
            if "relation_model_id" in row and row["relation_model_id"]:
                relation_model_record = env["ir.model"].search(
                    [("model", "=", row["relation_model_id"])], limit=1
                )
                if relation_model_record:
                    row["relation_model_id"] = relation_model_record.id  # Convert to ID
                else:
                    _logger.warning(
                        f"Relation Model '{row['relation_model_id']}' not found, skipping record."
                    )
                    continue

            # Create new attribute
            env["attribute.attribute"].create(row)
            _logger.info(f"Created Attribute: {row['field_description']}")


def import_attribute_options(env):
    """Import Attribute Options from CSV"""
    csv_path = file_path("ol_pim/data/attribute.option.csv")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            search_domain = [
                "|",
                ("code", "=", row["code"]),
                "&",
                ("code", "=", False),
                ("name", "=", row["name"]),
            ]
            existing_record = env["attribute.option"].search(search_domain, limit=1)

            if existing_record:
                # Compare values and update if necessary
                update_fields = {}
                if existing_record.name != row["name"]:
                    update_fields["name"] = row["name"]

                # Check and safely convert sequence
                try:
                    update_fields["sequence"] = (
                        int(row["sequence"]) if row["sequence"].isdigit() else 10
                    )
                except ValueError:
                    update_fields["sequence"] = 10

                if existing_record.code != row["code"]:
                    update_fields["code"] = row["code"]
                if update_fields:
                    _logger.info(f"Updating Attribute Option: {row['name']}")
                    existing_record.write(update_fields)
                continue

            # Convert attribute_id from field_description to ID
            if "attribute_id" in row and row["attribute_id"]:
                attribute_record = env["attribute.attribute"].search(
                    [("field_description", "=", row["attribute_id"])], limit=1
                )
                if attribute_record:
                    row["attribute_id"] = attribute_record.id
                else:
                    _logger.warning(
                        f"Attribute '{row['attribute_id']}' not found, skipping record."
                    )
                    continue

            env["attribute.option"].create(row)
            _logger.info(f"Created Attribute Option: {row['name']}")


def load_attribute_set_group_option_csv_data(env):
    """Main Function to Import Data in Correct Order"""
    _logger.warning("*************** STARTING CSV IMPORT ***************")

    import_attribute_sets(env)  # Step 1: Sets first
    import_attribute_groups(env)  # Step 2: Groups (must belong to a set)
    import_attributes(env)  # Step 3: Attributes (must belong to a group)
    import_attribute_options(env)  # Step 4: Options (must belong to an attribute)

    _logger.warning("*************** CSV IMPORT COMPLETE ***************")
