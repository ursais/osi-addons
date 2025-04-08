# pylint: disable=pointless-statement
{
    "name": "OnLogic Templates",
    # Used to filter our modules from various CLI functionality
    "onlogic": True,
    "version": "17.0.1.0.0",
    "summary": "Collection of OnLogic email and report template pieces",
    "depends": ["web", "ol_base"],
    "category": "Sales",
    "description": """Collection of OnLogic email and report template pieces""",
    "author": "OnLogic",
    "website": "https://www.onlogic.com",
    "license": "AGPL-3",
    "data": [
        # Data
        "data/email_templates.xml",
        "data/paper_formats.xml",
        # Styles
        "templates/style/font.xml",
        "templates/style/flexbox.xml",
        "templates/style/footer.xml",
        "templates/style/header.xml",
        "templates/style/page.xml",
        # Views
        "views/res_company.xml",
        "views/template_parts.xml",
        # Main Layout Sections
        "templates/layout/main.xml",
        "templates/layout/header.xml",
        "templates/layout/footer.xml",
        # Specific Layouts
        "templates/address.xml",
        "templates/shipment.xml",
        "templates/serial_numbers.xml",
        "templates/payment.xml",
        "templates/invoice_lines.xml",
        "templates/notes_and_totals.xml",
        "templates/notes_and_totals_refund_invoice.xml",
        "templates/invoice_notes_and_totals.xml",
        "templates/tax_exempt.xml",
        "templates/products.xml",
        "templates/quote_closing_text.xml",
    ],
}
