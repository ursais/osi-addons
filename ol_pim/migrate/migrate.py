from odoo.tools.misc import file_path
import csv
import logging
from odoo import fields

_logger = logging.getLogger(__name__)


def import_attribute_sets(env):
    """Import Attribute Sets from CSV"""
    csv_path = file_path("ol_pim/data/attribute.set.csv")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            search_domain = [("name", "=", row["name"])]

            existing_record = env["attribute.set"].search(search_domain, limit=1)

            if existing_record:
                _logger.info(f"Skipping existing Attribute Set: {row['name']}")
                continue

            # Convert model_id from name ("product.template") to ID
            if "model_id" in row and row["model_id"]:
                model_record = env["ir.model"].search(
                    [("model", "=", row["model_id"])], limit=1
                )
                if model_record:
                    row["model_id"] = model_record.id  # Store the ID, not the name
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
            search_domain = [("name", "=", row["name"])]

            existing_record = env["attribute.group"].search(search_domain, limit=1)

            if existing_record:
                _logger.info(f"Skipping existing Attribute Group: {row['name']}")
                continue

            # Convert model_id from name ("product.template") to ID
            if "model_id" in row and row["model_id"]:
                model_record = env["ir.model"].search(
                    [("model", "=", row["model_id"])], limit=1
                )
                if model_record:
                    row["model_id"] = model_record.id  # Store the ID, not the name
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
            search_domain = [("field_description", "=", row["field_description"])]

            existing_record = env["attribute.attribute"].search(search_domain, limit=1)

            if existing_record:
                _logger.info(f"Skipping existing Attribute: {row['field_description']}")
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

            # Convert model_id from name ("product.template") to ID
            if "model_id" in row and row["model_id"]:
                model_record = env["ir.model"].search(
                    [("model", "=", row["model_id"])], limit=1
                )
                if model_record:
                    row["model_id"] = model_record.id  # Store the ID, not the name
                else:
                    _logger.warning(
                        f"ir.model '{row['model_id']}' not found, skipping record."
                    )
                    continue

            env["attribute.attribute"].create(row)
            _logger.info(f"Created Attribute: {row['field_description']}")


def import_attribute_options(env):
    """Import Attribute Options from CSV"""
    csv_path = file_path("ol_pim/data/attribute.option.csv")

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            search_domain = [("name", "=", row["name"])]

            existing_record = env["attribute.option"].search(search_domain, limit=1)

            if existing_record:
                _logger.info(f"Skipping existing Attribute Option: {row['name']}")
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


def migrate(env):
    """Main Function to Import Data in Correct Order"""
    _logger.warning("*************** STARTING CSV IMPORT ***************")

    import_attribute_sets(env)  # Step 1: Sets first
    import_attribute_groups(env)  # Step 2: Groups (must belong to a set)
    # import_attributes(env)  # Step 3: Attributes (must belong to a group)
    # import_attribute_options(env)  # Step 4: Options (must belong to an attribute)

    _logger.warning("*************** CSV IMPORT COMPLETE ***************")
