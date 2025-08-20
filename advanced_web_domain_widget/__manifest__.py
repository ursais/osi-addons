# -*- coding: utf-8 -*-
#################################################################################
# Author      : Terabits Technolab (<www.terabits.xyz>)
# Copyright(c): 2023-2025
# All Rights Reserved.
#
# This module is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    "name": "Advanced Web Domain Widget",
    "version": "17.0.4.4.4",
    "summary": "Set all relational fields domain by selecting its records unsing `in, not in` operator.",
    "sequence": 10,
    "author": "Terabits Technolab",
    "license": "OPL-1",
    "website": "https://www.terabits.xyz",
    "description": """
      
        """,
    "price": "5.00",
    "currency": "USD",
    "depends": ["web"],
    "data": [
        # 'views/assets.xml',
    ],
    "assets": {
        "web._assets_core": [
            # "advanced_web_domain_widget/static/src/domain/domain_field.js",
            # "advanced_web_domain_widget/static/src/domain/domain_field.xml",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_autocomplete.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_operator_editor.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_value_editors.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor.xml",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector_operator_editor.js",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector.js",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector.xml",
            "advanced_web_domain_widget/static/src/domain_selector_dialog/domain_selector_dialog.js",
            "advanced_web_domain_widget/static/src/domain_selector_dialog/domain_selector_dialog.xml",
            "advanced_web_domain_widget/static/src/dateSelectionBits/dateSelectionBits.js",
            "advanced_web_domain_widget/static/src/dateSelectionBits/dateSelectionBits.xml",
            "advanced_web_domain_widget/static/src/model_field_selector/model_field_selector.js",
            "advanced_web_domain_widget/static/src/model_field_selector/model_field_selector.xml",
        ],
        "web.assets_backend": [
            "advanced_web_domain_widget/static/src/domain/domain_field.js",
            "advanced_web_domain_widget/static/src/domain/domain_field.xml",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_autocomplete.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_operator_editor.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor_value_editors.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor.js",
            "advanced_web_domain_widget/static/src/tree_editor/tree_editor.xml",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector_operator_editor.js",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector.js",
            "advanced_web_domain_widget/static/src/domain_selector/domain_selector.xml",
            "advanced_web_domain_widget/static/src/domain_selector_dialog/domain_selector_dialog.js",
            "advanced_web_domain_widget/static/src/domain_selector_dialog/domain_selector_dialog.xml",
            "advanced_web_domain_widget/static/src/dateSelectionBits/dateSelectionBits.js",
            "advanced_web_domain_widget/static/src/dateSelectionBits/dateSelectionBits.xml",
            "advanced_web_domain_widget/static/src/model_field_selector/model_field_selector.js",
            "advanced_web_domain_widget/static/src/model_field_selector/model_field_selector.xml",
        ],
    },
    "images": ["static/description/banner.png"],
    "application": True,
    "installable": True,
    "auto_install": False,
}
