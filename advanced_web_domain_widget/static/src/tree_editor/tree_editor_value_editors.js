/** @odoo-module **/

import {
    deserializeDate,
    deserializeDateTime,
    serializeDate,
    serializeDateTime,
} from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import {
    DomainSelectorAutocompleteBits,
    DomainSelectorSingleAutocompleteBits,
} from "@advanced_web_domain_widget/tree_editor/tree_editor_autocomplete";
import { unique } from "@web/core/utils/arrays";
import { Input, Select, List, Range } from "@web/core/tree_editor/tree_editor_components";
import { formatValue } from "@web/core/tree_editor/condition_tree";
import { getResModel, disambiguate, isId } from "@web/core/tree_editor/utils";
const { DateTime } = luxon;

// ============================================================================

const formatters = registry.category("formatters");
const parsers = registry.category("parsers");

function parseValue(fieldType, value) {
    const parser = parsers.get(fieldType, (value) => value);
    try {
        return parser(value);
    } catch {
        return value;
    }
}

function isParsable(fieldType, value) {
    const parser = parsers.get(fieldType, (value) => value);
    try {
        parser(value);
    } catch {
        return false;
    }
    return true;
}

function genericSerializeDate(type, value) {
    return type === "date" ? serializeDate(value) : serializeDateTime(value);
}

function genericDeserializeDate(type, value) {
    return type === "date" ? deserializeDate(value) : deserializeDateTime(value);
}

const STRING_EDITOR = {
    component: Input,
    extractProps: ({ value, update }) => ({ value, update }),
    isSupported: (value) => typeof value === "string",
    defaultValue: () => "",
};

function makeSelectEditor(options, params = {}) {
    const getOption = (value) => options.find(([v]) => v === value) || null;
    return {
        component: Select,
        extractProps: ({ value, update }) => ({
            value,
            update,
            options,
            addBlankOption: params.addBlankOption,
        }),
        isSupported: (value) => Boolean(getOption(value)),
        defaultValue: () => options[0]?.[0] ?? false,
        stringify: (value, disambiguate) => {
            const option = getOption(value);
            return option ? option[1] : disambiguate ? formatValue(value) : String(value);
        },
        message: _t("Value not in selection"),
    };
}

function makeAutoCompleteEditor(fieldDef) {
    return {
        component: DomainSelectorAutocompleteBits,
        extractProps: ({ value, update }) => {
            return {
                resModel: getResModel(fieldDef),
                fieldString: fieldDef.string,
                update: (value) => update(unique(value)),
                resIds: unique(value),
            };
        },
        isSupported: (value) => Array.isArray(value),
        defaultValue: () => [],
    };
}

// ============================================================================

function getPartialValueEditorInfo(fieldDef, operator, params = {}) {
    if(fieldDef.name === "id" && ["in", "not in"].includes(operator) && params.resModel) {
        return {
            component: DomainSelectorAutocompleteBits,
            extractProps: ({ value, update }) => {
                return {
                    resModel: params.resModel,
                    fieldString: fieldDef.string,
                    update: (value) => update(unique(value)),
                    resIds: unique(value),
                };
            },
            isSupported: (value) => Array.isArray(value),
            defaultValue: () => [],
        };
    }

    if(operator === "date_filter" && ["date", "datetime"].includes(fieldDef.type)) {
        const options = [
            ['today', _t('Today')],
            ['this_week', _t('This week')],
            ['this_month', _t('Thismonth')],
            ['this_quarter', _t('This quarter')],
            ['this_year', _t('This year')],
            ['last_day', _t('last day')],
            ['last_week', _t('last week')],
            ['last_month', _t('last month')],
            ['last_quarter', _t('last quarter')],
            ['last_year', _t('last year')],
            ['last_7_days', _t('last 7 days')],
            ['last_30_days', _t('last 30 days')],
            ['last_90_days', _t('last 90 days')],
            ['last_365_days', _t('last 365 days')],
            ['next_day', _t('Next day')],
            ['next_week', _t('Next week')],
            ['next_month', _t('Next month')],
            ['next_quarter', _t('next quarter')],
            ['next_year', _t('Next year')],
        ]
        return makeSelectEditor(options);
    }
    switch (operator) {
        case "set":
        case "not_set":
            return {
                component: null,
                extractProps: null,
                isSupported: (value) => value === false,
                defaultValue: () => false,
            };
        case "=like":
        case "=ilike":
        case "like":
        case "not like":
        case "ilike":
        case "not ilike":
            return STRING_EDITOR;
        case "between": {
            const editorInfo = getValueEditorInfo(fieldDef, "=");
            return {
                component: Range,
                extractProps: ({ value, update }) => ({
                    value,
                    update,
                    editorInfo,
                }),
                isSupported: (value) => Array.isArray(value) && value.length === 2,
                defaultValue: () => {
                    const { defaultValue } = editorInfo;
                    return [defaultValue(), defaultValue()];
                },
            };
        }
        case "in":
        case "not in": {
            switch (fieldDef.type) {
                case "tags":
                    return STRING_EDITOR;
                case "many2one":
                case "many2many":
                case "one2many":
                    return makeAutoCompleteEditor(fieldDef);
                default: {
                    const editorInfo = getValueEditorInfo(fieldDef, "=", {
                        addBlankOption: true,
                        startEmpty: true,
                    });
                    return {
                        component: List,
                        extractProps: ({ value, update }) => {
                            if (!disambiguate(value)) {
                                const { stringify } = editorInfo;
                                editorInfo.stringify = (val) => stringify(val, false);
                            }
                            return {
                                value,
                                update,
                                editorInfo,
                            };
                        },
                        isSupported: (value) => Array.isArray(value),
                        defaultValue: () => [],
                    };
                }
            }
        }
    }

    const { type } = fieldDef;
    switch (type) {
        case "integer":
        case "float":
        case "monetary": {
            const formatType = type === "integer" ? "integer" : "float";
            return {
                component: Input,
                extractProps: ({ value, update }) => ({
                    value: String(value),
                    update: (value) => update(parseValue(formatType, value)),
                    startEmpty: params.startEmpty,
                }),
                isSupported: () => true,
                defaultValue: () => 1,
                shouldResetValue: (value) => parseValue(formatType, value) === value,
            };
        }
        case "date":
        case "datetime":
            return {
                component: DateTimeInput,
                extractProps: ({ value, update }) => ({
                    value:
                        params.startEmpty || value === false
                            ? false
                            : genericDeserializeDate(type, value),
                    type,
                    onApply: (value) => {
                        if (!params.startEmpty || value) {
                            update(genericSerializeDate(type, value || DateTime.local()));
                        }
                    },
                }),
                isSupported: (value) =>
                    value === false || (typeof value === "string" && isParsable(type, value)),
                defaultValue: () => genericSerializeDate(type, DateTime.local()),
                stringify: (value) => {
                    if (value === false) {
                        return _t("False");
                    }
                    if (typeof value === "string" && isParsable(type, value)) {
                        const formatter = formatters.get(type, formatValue);
                        return formatter(genericDeserializeDate(type, value));
                    }
                    return formatValue(value);
                },
                message: _t("Not a valid %s", type),
            };
        case "char":
        case "html":
        case "text":
            return STRING_EDITOR;
        case "boolean": {
            if (["is", "is_not"].includes(operator)) {
                const options = [
                    [true, _t("set")],
                    [false, _t("not set")],
                ];
                return makeSelectEditor(options, params);
            }
            const options = [
                [true, _t("True")],
                [false, _t("False")],
            ];
            return makeSelectEditor(options, params);
        }
        case "many2one": {
            if (["=", "!=", "parent_of", "child_of"].includes(operator)) {
                return {
                    component: DomainSelectorSingleAutocompleteBits,
                    extractProps: ({ value, update }) => {
                        return {
                            resModel: getResModel(fieldDef),
                            fieldString: fieldDef.string,
                            update,
                            resId: value,
                        };
                    },
                    isSupported: () => true,
                    defaultValue: () => false,
                    shouldResetValue: (value) => value !== false && !isId(value),
                };
            }
            break;
        }
        case "many2many":
        case "one2many":
            if (["=", "!="].includes(operator)) {
                return makeAutoCompleteEditor(fieldDef);
            }
            break;
        case "selection": {
            const options = fieldDef.selection || [];
            return makeSelectEditor(options, params);
        }
        case undefined: {
            const options = [[1, "1"]];
            return makeSelectEditor(options, params);
        }
    }

    // Global default for visualization mainly. It is there to visualize what
    // has been produced in the debug textarea (in o_domain_selector_debug_container)
    // It is hardly useful to produce a string in general.
    return {
        component: Input,
        extractProps: ({ value, update }) => ({
            value: String(value),
            update,
        }),
        isSupported: () => true,
        defaultValue: () => "",
    };
}

export function getValueEditorInfo(fieldDef, operator, options = {}) {
    const info = getPartialValueEditorInfo(fieldDef || {}, operator, options);
    return {
        extractProps: ({ value, update }) => ({ value, update }),
        message: _t("Value not supported"),
        stringify: (val, disambiguate = true) => {
            if (disambiguate) {
                return formatValue(val);
            }
            return String(val);
        },
        ...info,
    };
}

export function getDefaultValue(fieldDef, operator, value = null) {
    const { isSupported, shouldResetValue, defaultValue } = getValueEditorInfo(fieldDef, operator);
    if (value === null || !isSupported(value) || shouldResetValue?.(value)) {
        return defaultValue();
    }
    return value;
}
