# Copyright (C) 2017 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Mexican Localization Fiscal Regime Scan From CSF",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "summary": "Mexican Localization Fiscal Regime Scan From CSF",
    "author": "Open Source Integrators",
    "maintainer": "Open Source Integrators",
    "website": "https://github.com/ursais/osi-addons",
    "depends": [
        "contacts",
        "l10n_mx_edi_40",
        "l10n_mx_res_partner_csf",
    ],
    "external_dependencies": {
        "python": ["pdfminer", "pdfminer.six==20220319"],
    },
    "application": False,
    "maintainers": ["ursais"],
}
