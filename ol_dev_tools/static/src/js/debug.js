/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

function pythonDebug({ component, env }) {
    const { resId, resModel } = component.model.config;
    return {
        type: "item",
        description: _t("Python Debug"),
        callback: async () => {
            await env.services.orm.call(
                "base",
                "start_python_debug",
                [[], resId, resModel],
            );
        },
        sequence: 310,
    };
}


registry
    .category("debug")
    .category("form")
    .add("pythonDebug", pythonDebug);
