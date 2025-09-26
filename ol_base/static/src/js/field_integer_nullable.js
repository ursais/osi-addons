/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useNumpadDecimal } from "@web/views/fields/numpad_decimal_hook";
import { parseInteger } from "@web/views/fields/parsers";
import { formatInteger } from "@web/views/fields/formatters";

export class NullableIntegerField extends Component {
    static template = "web.IntegerField";
    static props = {
        ...standardFieldProps,
        formatNumber: { type: Boolean, optional: true },
        humanReadable: { type: Boolean, optional: true },
        decimals: { type: Number, optional: true },
        inputType: { type: String, optional: true },
        step: { type: Number, optional: true },
        placeholder: { type: String, optional: true },
    };
    static defaultProps = {
        formatNumber: true,
        humanReadable: false,
        inputType: "text",
        decimals: 0,
    };

    setup() {
        this.state = useState({ hasFocus: false });
        useInputField({
            getValue: () => this.formattedValue,
            refName: "numpadDecimal",
            // IMPORTANT: empty => false (so ORM writes NULL)
            parse: (v) => (v === "" ? false : parseInteger(v)),
        });
        useNumpadDecimal();
    }

    onFocusIn() { this.state.hasFocus = true; }
    onFocusOut() { this.state.hasFocus = false; }

    get formattedValue() {
        const val = this.value;
        // IMPORTANT: false, null and undefined are represented as an empty string
        if (val === false || val === null || val === undefined) {
            return "";
        }
        if (!this.props.formatNumber ||
            (!this.props.readonly && this.props.inputType === "number")) {
            return val;
        }
        if (this.props.humanReadable && !this.state.hasFocus) {
            return formatInteger(val, {
                humanReadable: true,
                decimals: this.props.decimals,
            });
        }
        return formatInteger(val, { humanReadable: false });
    }

    get value() {
        return this.props.record.data[this.props.name];
    }
}

export const nullableIntegerField = {
    component: NullableIntegerField,
    displayName: _t("NullableInteger"),
    supportedOptions: [
        {
            label: _t("Format number"),
            name: "enable_formatting",
            type: "boolean",
            help: _t(
                "Format the value according to your language setup - e.g. thousand separators, rounding, etc."
            ),
            default: true,
        },
        {
            label: _t("Type"),
            name: "type",
            type: "string",
        },
        {
            label: _t("Step"),
            name: "step",
            type: "number",
        },
        {
            label: _t("User-friendly format"),
            name: "human_readable",
            type: "boolean",
            help: _t("Use a human readable format (e.g.: 500G instead of 500,000,000,000)."),
        },
        {
            label: _t("Decimals"),
            name: "decimals",
            type: "number",
            default: 0,
            help: _t("Use it with the 'User-friendly format' option to customize the formatting."),
        },
    ],
    supportedTypes: ["integer"],
    isEmpty: (record, fieldName) => record.data[fieldName] === false,
    extractProps: ({ attrs, options }) => ({
        formatNumber: options?.enable_formatting !== undefined ? Boolean(options.enable_formatting) : true,
        humanReadable: !!options.human_readable,
        inputType: options.type,
        step: options.step,
        placeholder: attrs.placeholder,
        decimals: options.decimals || 0,
    }),
};

registry.category("fields").add("nullable_integer", nullableIntegerField);