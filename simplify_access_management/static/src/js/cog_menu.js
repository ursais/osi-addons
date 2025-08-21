/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { registry } from "@web/core/registry";

import { useState, onMounted } from "@odoo/owl";
const cogMenuRegistry = registry.category("cogMenu");

patch(CogMenu.prototype, {
    setup() {
        super.setup();
        var self = this;
        this.access = useState({ removeSpreadsheet: false, exportHindButton: true });
        onMounted(async () => {
            let res = await this.orm.call(
                "access.management",
                "is_spread_sheet_available",
                [1, this?.env?.config?.actionType, this?.env?.config?.actionId]
            )

            if (res) {
                this.access.removeSpreadsheet = res;
            }
            const RestActions = await this.orm.call(
                "access.management",
                "get_remove_options",
                [1, this.props.resModel]
            );

            if (RestActions.includes('export')) {
                this.access.exportHindButton = !RestActions.includes('export')
            }
        })
    },
    async _registryItems() {
        const items = [];
        for (const item of cogMenuRegistry.getAll()) {

            if (item?.Component?.name === "SpreadsheetCogMenu" && this.access.removeSpreadsheet)
                continue;
            if (item?.Component?.name === "ExportAll" && !this.access.exportHindButton) {
                continue;
            }
            if ("isDisplayed" in item ? await item.isDisplayed(this.env) : true) {
                items.push({
                    Component: item.Component,
                    groupNumber: item.groupNumber,
                    key: item.Component.name,
                });
            }
        }
        return items;
    }
})
