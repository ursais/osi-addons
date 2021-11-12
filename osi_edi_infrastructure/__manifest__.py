# Copyright (C) 2021 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "OSI EDI INFRASTRUCTURE",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "sequence": 25,
    "summery": "EDI Basic Infrastructure setup",
    "author": "Open Source Integrators",
    "maintainers": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "category": "",
    "depends": [
        "product",
        "mail",
        # "osi_customer_warehouse"
    ],
    "external_dependencies": {"python": ["unidecode"]},
    "data": [
        "security/edi_security.xml",
        "security/ir.model.access.csv",
        "views/edi_provider_view.xml",
        "views/edi_supp_doc_view.xml",
        "views/edi_message_queue_view.xml",
        "views/edi_comp_doc_view.xml",
        "views/edi_comp_view.xml",
        "views/edi_partner_doc_view.xml",
        "views/edi_partner_view.xml",
        "views/edi_prod_config_view.xml",
        "views/edi_product_view.xml",
    ],
    "auto_install": False,
    "application": True,
    "installable": True,
}
