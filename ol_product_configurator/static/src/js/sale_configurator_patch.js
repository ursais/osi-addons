/** @odoo-module **/

import { SaleOrderLineProductField } from "@sale/js/sale_product_field";
import { patch } from "@web/core/utils/patch";

patch(SaleOrderLineProductField.prototype, {
    get isConfigurableTemplate() {
        return (
            // Keep Odoo's default logic *only if config_ok is not True*
            (super.isConfigurableTemplate && this.props.record.data.config_ok !== true) ||

            // Add your custom flag, but also only when config_ok is not True
            (this.props.record.data.is_configurable_product === true &&
             this.props.record.data.config_ok !== true)
        );
    }
});
