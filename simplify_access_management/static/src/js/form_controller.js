/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

import { onWillStart, useState } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this.access = useState({removeProperty: false});
        onWillStart(async() => {
            this.access.removeProperty = await this.orm.call(
                "access.management",
                "is_add_property_available",
                [1, this?.props?.resModel]
            );
        })
    },
    get actionMenuItems() {
        const menuItems = super.actionMenuItems;
        if(this.access.removeProperty)
            menuItems.action = menuItems.action.filter(ele => this.access.removeProperty && ele.key != "addPropertyFieldValue");
        return menuItems;
    }
})