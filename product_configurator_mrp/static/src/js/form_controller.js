/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {formView} from "@web/views/form/form_view";
import {FormController} from "@web/views/form/form_controller";

export class ProductConfiguratorFormController extends FormController {
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
ProductConfiguratorFormController.components = {
    ...FormController.components,
};

export const ProductConfiguratorFormView = {
    ...formView,
    Controller: ProductConfiguratorFormController,
    buttonTemplate: "product_configurator_mrp.FormButtons",
};

registry
    .category("views")
    .add("product_configurator_mrp_form", ProductConfiguratorFormView);
