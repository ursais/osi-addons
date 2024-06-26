/** @odoo-module **/

import {patch} from "@web/core/utils/patch";
import { View } from "@web/views/view";

patch(View.prototype, {
    async loadView(props){
        var element = super.loadView(...arguments);
        if (this?.props?.context?.is_product_configurator){
            this.env.bus.trigger("CLEAR-CACHES");
        }
        return element
    },
});