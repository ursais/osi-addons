/** @odoo-module **/
import { PivotGroupByMenu } from "@web/views/pivot/pivot_group_by_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

patch(PivotGroupByMenu.prototype, {
  setup() {
    super.setup(...arguments);
    this.orm = useService("orm");
    this.hidden_fields = this.__owl__.parent.component.restricted_fields; 
    onWillStart(async () => { 
      this.fields = this.fields.filter((ele) => !this.hidden_fields.includes(ele.name));
    });
  },
});
