/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

function pythonDebug({ env }) {
    return {
        type: "item",
        description: _t("Python Debug"),
        callback: async () => {
            await env.services.orm.call(
                "base",
                "start_python_debug",
                [[]],
            );
        },
        sequence: 310,
    };
}


registry
    .category("debug")
    .category("form")
    .add("pythonDebug", pythonDebug);
