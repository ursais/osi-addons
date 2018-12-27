# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Purchase Workflow Customization",
    "summary": "PO Approval process that allows routing of POs for approval "
               "based on amount.",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Open Source Integrators",
    "category": "Purchase",
    "website": "http://www.opensourceintegrators.com",
    "depends": [
        "purchase",
        "hr",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/security_view.xml",
        "views/purchase_view.xml",
        "views/purchase_approval_view.xml",
    ],
    "installable": True,
    "maintainers": ["bodedra"]
}
