/* @odoo-module */
import {FormController} from "@web/views/form/form_controller";
import {patch} from "@web/core/utils/patch";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        if (
            this.props.resModel === "product.product" &&
            this.props.context.custom_create_variant
        ) {
            this.canCreate = false;
        }
    },
    async beforeExecuteActionButton(clickParams) {
        if (clickParams.special === "no_save") {
            delete clickParams.special;
            return true;
        }
        return super.beforeExecuteActionButton(...arguments);
    },
});
