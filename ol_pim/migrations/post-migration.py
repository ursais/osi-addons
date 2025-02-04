import csv
import logging
import io
from odoo.modules.module import get_module_resource
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def migration(env):
    csv_files = {
        "attribute.set": get_module_resource("ol_pim", "data", "attribute.set.csv"),
        # "attribute.group": get_module_resource("ol_pim", "data", "attribute.group.csv"),
        # "attribute.attribute": get_module_resource(
        #     "ol_pim", "data", "attribute.attribute.csv"
        # ),
        # "attribute.option": get_module_resource(
        #     "ol_pim", "data", "attribute.option.csv"
        # ),
    }

    models = {
        "attribute.set": "attribute_set.attribute.set",
        "attribute.group": "attribute_set.attribute.group",
        "attribute.attribute": "attribute_set.attribute.attribute",
        "attribute.option": "attribute_set.attribute.option",
    }

    _logger.warning(
        "******************************** STARTING CSV IMPORT ************************"
    )

    for key, csv_path in csv_files.items():
        model_name = models.get(key)
        if not model_name:
            _logger.warning(f"No model defined for {key}, skipping...")
            continue

        with open(csv_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames

            if not fieldnames:
                _logger.warning(f"⚠️ No columns found in {csv_path}, skipping...")
                continue

            records = []
            for row in reader:
                # Convert `model_id` from name to ID
                if "model_id" in row and row["model_id"]:
                    model_record = env["ir.model"].search(
                        [("model", "=", row["model_id"])], limit=1
                    )
                    raise UserError("Made it here")
                    if model_record:
                        row["model_id"] = model_record.id  # Convert name to ID
                    else:
                        _logger.warning(
                            f"⚠️ Model '{row['model_id']}' not found in ir.model, skipping record: {row}"
                        )
                        continue

                records.append(row)

            if not records:
                _logger.warning(
                    f"⚠️ No valid records found for {model_name}, skipping import..."
                )
                continue

            # Use Odoo's built-in `load` method for bulk import
            _logger.info(f"🆕 Loading {len(records)} records into {model_name}...")
            field_list = fieldnames  # Fields must match CSV headers
            result = env[model_name].load(field_list, records)

            if result.get("messages"):
                _logger.warning(
                    f"⚠️ Import warnings for {model_name}: {result['messages']}"
                )

            _logger.info(
                f"✅ Successfully loaded {result.get('ids', 0)} records into {model_name}."
            )


# import csv
# import logging
# from odoo.modules.module import get_module_resource

# _logger = logging.getLogger(__name__)


# def migration(env):
#     csv_files = {
#         "attribute.set": get_module_resource("ol_pim", "data", "attribute.set.csv"),
#         "attribute.group": get_module_resource("ol_pim", "data", "attribute.group.csv"),
#         "attribute.attribute": get_module_resource(
#             "ol_pim", "data", "attribute.attribute.csv"
#         ),
#         "attribute.option": get_module_resource(
#             "ol_pim", "data", "attribute.option.csv"
#         ),
#     }

#     models = {
#         "attribute.set": "attribute_set.attribute.set",
#         "attribute.group": "attribute_set.attribute.group",
#         "attribute.attribute": "attribute_set.attribute.attribute",
#         "attribute.option": "attribute_set.attribute.option",
#     }

#     _logger.warning(
#         "******************************** STARTING CSV IMPORT ************************"
#     )

#     for key, csv_path in csv_files.items():
#         model_name = models.get(key)
#         if not model_name:
#             _logger.warning(f"No model defined for {key}, skipping...")
#             continue

#         with open(csv_path, mode="r", encoding="utf-8") as file:
#             reader = csv.DictReader(file)
#             for row in reader:
#                 search_domain = [("name", "=", row["name"])]

#                 # 🔥 Ensure model_id is an integer by looking up ir.model
#                 if "model_id" in row and row["model_id"]:
#                     model_record = env["ir.model"].search(
#                         [("model", "=", row["model_id"])], limit=1
#                     )
#                     if model_record:
#                         row["model_id"] = (
#                             model_record.id
#                         )  # Replace string with integer ID
#                         search_domain.append(("model_id", "=", model_record.id))
#                     else:
#                         _logger.warning(
#                             f"⚠️ Model '{row['model_id']}' not found in ir.model, skipping record: {row}"
#                         )
#                         continue  # Skip the row if model_id is invalid

#                 existing_record = env[model_name].search(search_domain, limit=1)

#                 # 🔥 Convert fields that should be integers
#                 for field in row:
#                     if row[
#                         field
#                     ].isdigit():  # Convert number strings to actual integers
#                         row[field] = int(row[field])

#                 if existing_record:
#                     updates = {
#                         k: v
#                         for k, v in row.items()
#                         if v and getattr(existing_record, k, None) != v
#                     }
#                     if updates:
#                         existing_record.write(updates)
#                         _logger.info(f"✅ Updated {model_name}: {row['name']}")
#                 else:
#                     _logger.info(
#                         f"🆕 Creating {model_name}: {row['name']} with data {row}"
#                     )
#                     env[model_name].create(row)
#                     _logger.info(f"✔️ Created {model_name}: {row['name']}")
