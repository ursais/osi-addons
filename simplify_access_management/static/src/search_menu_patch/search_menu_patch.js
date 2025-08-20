/** @odoo-module **/
import { SearchBarMenu } from "@web/search/search_bar_menu/search_bar_menu";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, useState } from "@odoo/owl";

patch(SearchBarMenu.prototype, {
  setup() {
    super.setup(...arguments);
    this.orm = useService("orm");
    this.access = useState({
      removeCustomFilter: false,
      removeCustomGroup: false,
    });
    onWillStart(async () => {
      const res = await this.orm.call(
        "access.management",
        "is_custom_filter_and_group_available",
        ["", this?.env?.searchModel?.resModel]
      );
      this.access.removeCustomFilter = res.filter;
      this.access.removeCustomGroup = res.group;
    });
  },

  get hideCustomGroupBy() {
    return (
      this.env.searchModel.hideCustomGroupBy || this.access.removeCustomGroup
    );
  },
});
