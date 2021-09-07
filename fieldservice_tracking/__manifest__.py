# Copyright (C) 2021 Open Source Integrators
# Copyright (C) 2021 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Field Service Tracking",
    "summary": "This module will add tracking functionality in Fieldservice.",
    "license": "AGPL-3",
    "version": "14.0.1.0.0",
    "category": "Field Service",
    "author": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "fieldservice_substatus",
        "uom",
    ],
    "data": [
        "security/fsm_tracking_group.xml",
        "security/ir.model.access.csv",
        "views/fsm_person_view.xml",
        "views/fsm_stage_view.xml",
    ],
    "installable": True,
    "development_status": "Beta",
    "maintainers": [
        "wolfhall",
    ],
}
