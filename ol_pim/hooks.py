from odoo.tools.misc import file_path
import csv
import logging
from odoo import fields


_logger = logging.getLogger(__name__)


def load_attribute_csv_data(env):
    csv_files = {
        "attribute.set": file_path("ol_pim/data/attribute.set.csv"),
        "attribute.group": file_path("ol_pim/data/attribute.group.csv"),
        "attribute.attribute": file_path("ol_pim/data/attribute.attribute.csv"),
        "attribute.option": file_path("ol_pim/data/attribute.option.csv"),
    }

    models = {
        "attribute.set": "attribute.set",
        "attribute.group": "attribute.group",
        "attribute.attribute": "attribute.attribute",
        "attribute.option": "attribute.option",
    }

    _logger.warning("*************** STARTING CSV IMPORT ***************")

    for key, csv_path in csv_files.items():
        model_name = models.get(key)
        if not model_name:
            _logger.warning(f"No model defined for {key}, skipping...")
            continue

        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                search_domain = [("name", "=", row["name"])]

                # Convert model_id (if exists) from model name to ID
                if "model_id" in row and row["model_id"]:
                    model_record = env["ir.model"].search(
                        [("model", "=", row["model_id"])], limit=1
                    )
                    if model_record:
                        row["model_id"] = model_record.id
                        search_domain.append(("model_id", "=", model_record.id))
                    else:
                        _logger.warning(
                            f"Model '{row['model_id']}' not found, skipping record."
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
                    set_names = row["attribute_set_ids"].split(
                        ","
                    )  # Split names by comma
                    set_ids = (
                        env["attribute.set"].search([("name", "in", set_names)]).ids
                    )  # Get list of IDs
                    if set_ids:
                        row["attribute_set_ids"] = [
                            (6, 0, set_ids)
                        ]  # Format for Many2many field
                    else:
                        _logger.warning(
                            f"Attribute Sets '{row['attribute_set_ids']}' not found, skipping record."
                        )
                        continue

                # Convert attribute_id from name to ID
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

                existing_record = env[model_name].search(search_domain, limit=1)

                if existing_record:
                    updates = {}

                    for k, v in row.items():
                        if v:
                            # Handle Many2many field comparisons separately
                            if isinstance(
                                env[model_name]._fields[k], fields.Many2many
                            ):  # Check if it's a Many2many field
                                current_ids = getattr(existing_record, k).ids
                                new_ids = (
                                    v[0][2] if isinstance(v, list) else v
                                )  # Extract the list of ids from [(6, 0, ids)]
                                if sorted(current_ids) != sorted(new_ids):
                                    updates[k] = [(6, 0, new_ids)]
                                    _logger.info(
                                        f"Updated Many2many field {k} for {model_name}: {row['name']}"
                                    )
                                continue  # Skip to next field after handling Many2many

                            # Handle Many2one and other relational fields
                            elif isinstance(
                                env[model_name]._fields[k], fields.Many2one
                            ):  # Check if it's a Many2one field
                                current_id = getattr(existing_record, k, None)
                                if current_id:
                                    current_id = current_id.id
                                if current_id != v:
                                    updates[k] = v
                                    _logger.info(
                                        f"Updated Many2one field {k} for {model_name}: {row['name']}"
                                    )
                                continue  # Skip to next field after handling Many2one

                            # For other fields, do normal comparison
                            elif getattr(existing_record, k, None) != v:
                                updates[k] = v

                    if updates:
                        existing_record.write(updates)
                        _logger.info(f"Updated {model_name}: {row['name']}")
                else:
                    env[model_name].create(row)
                    _logger.info(f"Created {model_name}: {row['name']}")


# def load_xml_import(env):
#     # Define the path to the XML file in the module's `data` folder
#     xml_file_path = file_path("ol_pim/data/attribute_attribute_domain.xml")

#     # Trigger the XML import
#     with open(xml_file_path, "r") as f:
#         env["ir.importexport"].with_context(module="ol_pim").import_file(f.read())
