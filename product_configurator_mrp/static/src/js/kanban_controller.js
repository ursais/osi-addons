/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {kanbanView} from "@web/views/kanban/kanban_view";
import {KanbanController} from "@web/views/kanban/kanban_controller";

export class ProductConfiguratorKanbanController extends KanbanController {
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
ProductConfiguratorKanbanController.components = {
    ...KanbanController.components,
};

export const ProductConfiguratorKanbanView = {
    ...kanbanView,
    Controller: ProductConfiguratorKanbanController,
    buttonTemplate: "product_configurator_mrp.KanbanButtons",
};
registry
    .category("views")
    .add("product_configurator_mrp_kanban", ProductConfiguratorKanbanView);
