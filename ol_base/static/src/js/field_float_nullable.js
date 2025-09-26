/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useNumpadDecimal } from "@web/views/fields/numpad_decimal_hook";
import { formatFloat } from "@web/views/fields/formatters";
import { parseFloat } from "@web/views/fields/parsers";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, useState } from "@odoo/owl";

export class NullableFloatField extends Component {
    static template = "web.FloatField";
    static props = {
        ...standardFieldProps,
        formatNumber: { type: Boolean, optional: true },
        inputType: { type: String, optional: true },
        step: { type: Number, optional: true },
        digits: { type: Array, optional: true },
        placeholder: { type: String, optional: true },
        humanReadable: { type: Boolean, optional: true },
        decimals: { type: Number, optional: true },
    };
    static defaultProps = {
        formatNumber: true,
        inputType: "text",
        humanReadable: false,
        decimals: 0,
    };

    setup() {
        this.state = useState({
            hasFocus: false,
        });
        this.inputRef = useInputField({
            getValue: () => this.formattedValue,
            refName: "numpadDecimal",
            // IMPORTANT: empty => false (so ORM writes NULL)
            parse: (v) => (v === "" ? false : this.parse(v)),
        });
        useNumpadDecimal();
    }

    onFocusIn() {
        this.state.hasFocus = true;
    }

    onFocusOut() {
        this.state.hasFocus = false;
    }

    parse(value) {
        return this.props.inputType === "number" ? Number(value) : parseFloat(value);
    }

    get digits() {
        const fieldDigits = this.props.record.fields[this.props.name].digits;
        return !this.props.digits && Array.isArray(fieldDigits) ? fieldDigits : this.props.digits;
    }
    get formattedValue() {
        const val = this.value;
        // IMPORTANT: false, null and undefined are represented as an empty string
        if (val === false || val === null || val === undefined) {
            return "";
        }
        if (
            !this.props.formatNumber ||
            (this.props.inputType === "number" && !this.props.readonly && this.value)
        ) {
            return this.value;
        }
        if (this.props.humanReadable && !this.state.hasFocus) {
            return formatFloat(this.value, {
                digits: this.digits,
                humanReadable: true,
                decimals: this.props.decimals,
            });
        } else {
            return formatFloat(this.value, { digits: this.digits, humanReadable: false });
        }
    }

    get value() {
        return this.props.record.data[this.props.name];
    }
}

export const nullableFloatField = {
    component: NullableFloatField,
    displayName: _t("Float"),
    supportedOptions: [
        {
            label: _t("Format number"),
            name: "enable_formatting",
            type: "boolean",
            help: _t(
                "Format the value according to your language setup - e.g. thousand separators, rounding, etc."
            ),
            default: true,
        },
        {
            label: _t("Digits"),
            name: "digits",
            type: "digits",
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
    supportedTypes: ["float"],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => {
        // Sadly, digits param was available as an option and an attr.
        // The option version could be removed with some xml refactoring.
        let digits;
        if (attrs.digits) {
            digits = JSON.parse(attrs.digits);
        } else if (options.digits) {
            digits = options.digits;
        }

        return {
            formatNumber:
                options?.enable_formatting !== undefined
                    ? Boolean(options.enable_formatting)
                    : true,
            inputType: options.type,
            humanReadable: !!options.human_readable,
            step: options.step,
            digits,
            placeholder: attrs.placeholder,
            decimals: options.decimals || 0,
        };
    },
};

registry.category("fields").add("nullable_float", nullableFloatField);