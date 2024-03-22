/* @odoo-module */
/*eslint-disable*/
import {patch} from "@web/core/utils/patch";
import {FormController} from "@web/views/form/form_controller";
import {ListController} from "@web/views/list/list_controller";
import {KanbanController} from "@web/views/kanban/kanban_controller";
import {onMounted} from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            var form_element = this.rootRef.el;
            var self = this;
            if (
                self.model.config.resModel === "product.product" &&
                self.model.config.context.custom_create_variant
            ) {
                var buttons = form_element.querySelector(
                    ".o_control_panel_main_buttons"
                );
                var createButtons = buttons.querySelectorAll(".o_form_button_create");
                createButtons.forEach((button) => {
                    button.style.display = "none";
                });
            }
        });
    },
    // Async beforeExecuteActionButton(clickParams) {
    //     console.log("beforeExecuteActionButton", clickParams);
    //     if (clickParams.special === "no_save") {
    //         delete clickParams.special;
    //         return true;
    //     }
    //     return super.beforeExecuteActionButton(...arguments);
    // },
});

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            var form_element = this.rootRef.el;
            var self = this;
            if (
                self.model.config.resModel === "product.product" &&
                self.model.config.context.custom_create_variant
            ) {
                var buttons = form_element.querySelector(
                    ".o_control_panel_main_buttons"
                );
                var createButtons = buttons.querySelectorAll(".o_list_button_add");
                createButtons.forEach((button) => {
                    button.style.display = "none";
                });
            }
        });
    },
});

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            var form_element = this.rootRef.el;
            var self = this;
            if (
                self.model.config.resModel === "product.product" &&
                self.model.config.context.custom_create_variant
            ) {
                var buttons = form_element.querySelector(
                    ".o_control_panel_main_buttons"
                );
                var createButtons = buttons.querySelectorAll(".o-kanban-button-new");
                createButtons.forEach((button) => {
                    button.style.display = "none";
                });
            }
        });
    },
});
