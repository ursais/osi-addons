from pathlib import Path
import csv
from odoo import SUPERUSER_ID, api


def _run_normal_import(env, model_name, csv_file_path):
    """Run a CSV import programmatically in Odoo 17."""
    ImportWizard = env["base_import.import"]

    with csv_file_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        csv_rows = list(reader)

    if not csv_rows:
        raise ValueError(f"CSV file is empty: {csv_file_path}")

    headers = csv_rows[0]  # first row

    # Create wizard with CSV content as bytes
    import_wizard = ImportWizard.create(
        {
            "res_model": model_name,
            "file_type": "text/csv",
            "file_name": csv_file_path.name,
            "file": csv_file_path.read_bytes(),
        }
    )

    options = {
        "has_headers": True,  # skip first row automatically
        "separator": ",",
        "quoting": '"',
    }

    # Execute import
    import_wizard.execute_import(headers, [], options)


def post_init_hook(env):
    env = api.Environment(env.cr, SUPERUSER_ID, dict())
    module_path = Path(__file__).parent
    data_path = module_path / "data"

    normal_imports = [
        ("product.reporting.category", data_path / "product_reporting_category.csv"),
        ("product.reporting.line", data_path / "product_reporting_line.csv"),
        ("product.reporting.series", data_path / "product_reporting_series.csv"),
        ("product.reporting.system", data_path / "product_reporting_system.csv"),
    ]

    for model_name, file_path in normal_imports:
        _run_normal_import(env, model_name, file_path)

    # Set Reporting Category on Products
    ProductTemplate = env["product.template"]
    ReportingSystem = env["product.reporting.system"]

    csv_path = data_path / "product_reporting_values.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            default_code = row["default_code"].strip()
            display_name = row["reporting_system_id.display_name"].strip()

            product = ProductTemplate.search(
                [("default_code", "=", default_code)], limit=1
            )
            if not product:
                continue

            system = ReportingSystem.search(
                [("display_name", "=", display_name)], limit=1
            )
            if not system:
                continue

            product.write({"reporting_system_id": system.id})
