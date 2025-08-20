/* @odoo-module */
import { ModelFieldSelectorPopover } from "@web/core/model_field_selector/model_field_selector_popover";
import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(ModelFieldSelectorPopover.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");
  },
  async loadPages(resModel, path) {
    let page = await super.loadPages(...arguments);
    const res = await this.orm.call("access.management", "get_hidden_field", [
      "",
      resModel,
    ]);
    page.fieldNames = page.fieldNames.filter((ele) => !res.includes(ele));
    page.sortedFieldNames = page.sortedFieldNames.filter(
      (ele) => !res.includes(ele)
    );
    page.selectedName = res.includes(page.selectedName)
      ? ""
      : page.selectedName;
    return page;
  },
});

patch(ModelFieldSelector.prototype, {
  setup() {
    super.setup();
    this.orm = useService("orm");
  },
  async updateState(params, isConcurrent) {
    const { resModel, path } = params;
    const res = await this.orm.call("access.management", "get_hidden_field", [
      "",
      resModel,
    ]);
    if(res.includes(path) && path != "id") {
      params.path = "id";
      this.props.update("id", { resModel: this.props.resModel, fieodDef: null });
    }
    await super.updateState(...arguments);    
  }
});
