# Copyright (C) 2026 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR Attendance Read Access Fix",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "summary": """
    Let read-only users open the Attendances list/form without hitting a
    "hr.attendance - write" access error caused by stored computed fields.
    """,
    "author": "Open Source Integrators",
    "maintainers": ["Open Source Integrators"],
    "website": "https://github.com/ursais/osi-addons",
    "category": "Human Resources/Attendances",
    "depends": ["hr_attendance"],
    "data": [],
    "installable": True,
}
