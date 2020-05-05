# Copyright (C) 2019 Serpent Consulting Services Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Web External Help",
    'version': "12.0.1.0.0",
    'author': "Open Source Integrators, Serpent Consulting Services Pvt. Ltd.",
    'category': 'Web',
    'website': "https://www.opensourceintegrators.com, http://serpentcs.com",
    'license': 'AGPL-3',
    'depends': [
        'web'
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/res_groups.xml',
        'views/template.xml',
        'views/view_fields_external_help.xml',
        'views/view_model_external_help.xml',
    ],
    'qweb': [
        'views/debug_menu.xml',
    ],
}
