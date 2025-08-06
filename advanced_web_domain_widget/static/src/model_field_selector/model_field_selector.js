/** @odoo-module **/

import { ModelFieldSelectorPopover } from "@web/core/model_field_selector/model_field_selector_popover";
import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";

export class ModelFieldSelectorPopover2 extends ModelFieldSelectorPopover {
  static template = "web.ModelFieldSelectorPopover2";
}

export class ModelFieldSelector2 extends ModelFieldSelector {}

ModelFieldSelector2.components = {
  ...ModelFieldSelector.components,
  Popover: ModelFieldSelectorPopover2,
};
