/* @odoo-module */
import { ActionMenus } from "@web/search/action_menus/action_menus";
import { patch } from "@web/core/utils/patch";

patch(ActionMenus.prototype, {
  async getActionItems(props) {
    var res = await super.getActionItems(props);
    if (res.length > 0) {
      const RestActions = await this.orm.call(
        "access.management",
        "get_remove_options",
        [1, this.props.resModel]
      );
      // const isExportHidden = await this.orm.call(
      //   "access.management",
      //   "is_export_hide",
      //   [1, this.props.resModel]
      // );
      // if (isExportHidden) {
      //   return res.filter(
      //     (ele) =>
      //       !RestActions.includes(ele.key) && ele.key != "export"
      //   );
      // }
      return res.filter((ele) => !RestActions.includes(ele.key));
    }
    return res
  },
});
