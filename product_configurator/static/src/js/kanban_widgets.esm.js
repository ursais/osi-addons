/* @odoo-module */
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {patch} from "@web/core/utils/patch";

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        if (
            this.props.resModel === "product.product" &&
            this.props.context.custom_create_variant
        ) {
            this.props.archInfo.activeActions.create = false;
        }
    },
});
