/** @odoo-module **/

import { MultiRecordSelector } from "@web/core/record_selectors/multi_record_selector";
import { _t } from "@web/core/l10n/translation";
import { formatAST, toPyValue } from "@web/core/py_js/py_utils";
import { Expression } from "@web/core/tree_editor/condition_tree";
import { RecordSelector } from "@web/core/record_selectors/record_selector";
import { RecordAutocomplete } from "@web/core/record_selectors/record_autocomplete";
import { registry } from "@web/core/registry";

const SEARCH_LIMIT = 7;
const SEARCH_MORE_LIMIT = 320;

export const isId = (val) => Number.isInteger(val) && val >= 1;

export const getFormat = (val, displayNames) => {
  let text;
  let colorIndex; 
  if (isId(val) || displayNames[0] === "Enviroment company" || displayNames[0] === "Enviroment user") {
    text =
      typeof displayNames[val] === "string"
        ? displayNames[val]
        : _t("Inaccessible/missing record ID: %s", val);
    colorIndex = typeof displayNames[val] === "string" ? 0 : 2; // 0 = grey, 2 = orange
  } else {
    text =
      val instanceof Expression
        ? String(val)
        : _t("Invalid record ID: %s", formatAST(toPyValue(val)));
    colorIndex = val instanceof Expression ? 2 : 1; // 1 = red
  }
  return { text, colorIndex };
};

export class RecordAutocompleteBits extends RecordAutocomplete {
  search(name, limit) {
    const domain = this.getDomain();
    return this.orm.call(this.props.resModel, "domain_name_search", [], {
        name,
        args: domain,
        limit,
        context: this.props.context || {},
    });
  }
  async loadOptionsSource(name) {
    if (this.lastProm) {
      this.lastProm.abort(false);
    }
    this.lastProm = this.search(name, SEARCH_LIMIT + 1);
    const nameGets = (await this.lastProm).map(([id, label]) => [
      id,
      label ? label.split("\n")[0] : _t("Unnamed"),
    ]);

    if (this.props.resModel === "res.users") {
      nameGets.unshift([0, "Environment user"]);
    }
    if (this.props.resModel === "res.company") {
      nameGets.unshift([0, "Environment company"]);
    }

    this.addNames(nameGets);
    const options = nameGets.map(([value, label]) => ({ value, label }));
    if (SEARCH_LIMIT < nameGets.length) {
      options.push({
        label: _t("Search More..."),
        action: this.onSearchMore.bind(this, name),
        classList: "o_m2o_dropdown_option",
      });
    }
    if (options.length === 0) {
      options.push({ label: _t("(no result)"), unselectable: true });
    }
    return options;
  }

  async onSearchMore(name) {
    const { fieldString, multiSelect, resModel } = this.props;
    let operator;
    const ids = [];
    if (name) {
      const nameGets = await this.search(name, SEARCH_MORE_LIMIT);

      if (this.props.resModel === "res.users") {
        nameGets.unshift([0, "Enviornment user"]);
      }
      if (this.props.resModel === "res.company") {
        nameGets.unshift([0, "Enviornment company"]);
      }

      this.addNames(nameGets);
      operator = "in";
      ids.push(...nameGets.map((nameGet) => nameGet[0]));
    } else {
      operator = "not in";
      ids.push(...this.getIds());
    }
    const dynamicFilters = ids.length
      ? [
          {
            description: _t("Quick search: %s", name),
            domain: [["id", operator, ids]],
          },
        ]
      : undefined;
    // fine for now but we don't like this kind of dependence of core to views
    const SelectCreateDialog = registry.category("dialogs").get("select_create");
    this.addDialog(SelectCreateDialog, {
      title: _t("Search: %s", fieldString),
      dynamicFilters,
      resModel,
      noCreate: true,
      multiSelect,
      context: this.props.context || {},
      onSelected: (resId) => {
        const resIds = Array.isArray(resId) ? resId : [resId];
        this.props.update([...resIds]);
      },
    });
  }
}

export class DomainSelectorAutocompleteBits extends MultiRecordSelector {
  static props = {
    ...MultiRecordSelector.props,
    resIds: true, //resIds could be an array of ids or an array of expressions
  };

  static components = {
    ...MultiRecordSelector.components,
    RecordAutocomplete: RecordAutocompleteBits,
  };

  getIds(props = this.props) {
    return props.resIds.filter((val) => isId(val));
  }

  getTags(props, displayNames) {
    return props.resIds.map((val, index) => {
      if (val === 0 && props.resModel === "res.users") {
        const { text, colorIndex } = getFormat(val, ["Enviroment user"]);
        return {
          text,
          colorIndex,
          onDelete: () => {
            this.props.update([
              ...this.props.resIds.slice(0, index),
              ...this.props.resIds.slice(index + 1),
            ]);
          },
        };
      }
      if (val === 0 && props.resModel === "res.company") {
        const { text, colorIndex } = getFormat(val, ["Enviroment company"]);
        return {
          text,
          colorIndex,
          onDelete: () => {
            this.props.update([
              ...this.props.resIds.slice(0, index),
              ...this.props.resIds.slice(index + 1),
            ]);
          },
        };
      }
      const { text, colorIndex } = getFormat(val, displayNames);
      return {
        text,
        colorIndex,
        onDelete: () => {
          this.props.update([
            ...this.props.resIds.slice(0, index),
            ...this.props.resIds.slice(index + 1),
          ]);
        },
      };
    });
  }
}

export class DomainSelectorSingleAutocompleteBits extends RecordSelector {
  static props = {
    ...RecordSelector.props,
    resId: true,
  };

  static components = {
    ...MultiRecordSelector.components,
    RecordAutocomplete: RecordAutocompleteBits,
  };

  getDisplayName(props = this.props, displayNames) {
    const { resId } = props;
    if (resId === false) {
      return "";
    }
    const { text } = getFormat(resId, displayNames);
    return text;
  }

  getIds(props = this.props) {
    if (isId(props.resId)) {
      return [props.resId];
    }
    return [];
  }
}
