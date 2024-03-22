/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {listView} from "@web/views/list/list_view";
import {ListController} from "@web/views/list/list_controller";
import {useService} from "@web/core/utils/hooks";

export class ProductConfiguratorController extends ListController {
    setup() {
        super.setup();
        this.action = useService("action");
        this.rpc = useService("rpc");
        this.orm = useService("orm");
    }

    async _onConfigure() {
        let action = await this.orm.call("mrp.production", "action_config_start", []);
        this.action.doAction(action);
    }
}

ProductConfiguratorController.components = {
    ...ListController.components,
};

export const ProductConfiguratorListView = {
    ...listView,
    Controller: ProductConfiguratorController,
    buttonTemplate: "product_configurator_mrp.ListButtons",
};

registry
    .category("views")
    .add("product_configurator_mrp_tree", ProductConfiguratorListView);
