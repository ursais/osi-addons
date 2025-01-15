/* @odoo-module */
import {ListController} from "@web/views/list/list_controller";
import {patch} from "@web/core/utils/patch";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        if (
            this.props.resModel === "product.product" &&
            this.props.context.custom_create_variant
        ) {
            this.activeActions.create = false;
        }
    },
});
