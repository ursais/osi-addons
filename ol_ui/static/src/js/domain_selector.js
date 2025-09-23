/** @odoo-module **/
import { DomainSelector } from "@web/core/domain_selector/domain_selector";
import { patch } from "@web/core/utils/patch";
import { Input } from "@web/core/tree_editor/tree_editor_components";
import { _t } from "@web/core/l10n/translation";

const IN_LIST_OPERATOR = "in_list";
const SUPPORTED_FIELD_TYPES = ['char', 'text', 'integer', 'float'];

function parseInputValues(inputValue, fieldType = 'char') {
    if (!inputValue || inputValue.trim() === "") {
        return { values: [], error: null };
    }

    // Split by comma and process values
    const values = inputValue.split(',');
    const processedValues = [];

    for (let value of values) {
        value = value.trim();
        if (value.length === 0) continue;

        // Type-specific validation and conversion
        if (fieldType === 'integer') {
            const intValue = parseInt(value, 10);
            if (isNaN(intValue)) {
                return {
                    values: [],
                    error: _t("Invalid integer value: '%s'", value)
                };
            }
            processedValues.push(intValue);
        } else if (fieldType === 'float') {
            const floatValue = parseFloat(value);
            if (isNaN(floatValue)) {
                return {
                    values: [],
                    error: _t("Invalid decimal value: '%s'", value)
                };
            }
            processedValues.push(floatValue);
        } else {
            processedValues.push(value);
        }
    }

    return { values: [...new Set(processedValues)], error: null };
}

patch(DomainSelector.prototype, {
    getOperatorEditorInfo(node) {
        const info = super.getOperatorEditorInfo(node);
        const fieldDef = this.getFieldDef(node.path);
        const isSupportedFieldType = fieldDef && SUPPORTED_FIELD_TYPES.includes(fieldDef.type);
        
        if (isSupportedFieldType) {
            // Patch the info object similar to date_range approach
            patch(info, {
                extractProps({value: [operator, negate], update}) {
                    const props = super.extractProps.apply(this, arguments);
                    
                    // Add our custom operator to the options if not already present
                    const hasInListOperator = props.options.some(([key]) => 
                        key === IN_LIST_OPERATOR || key.includes(`"${IN_LIST_OPERATOR}"`)  
                    );
                    
                    if (!hasInListOperator) {
                        // Add the in_list operator option
                        props.options.push([IN_LIST_OPERATOR, _t("is in list")]);
                    }
                    
                    // Update the label for our custom operator if it's selected
                    if (operator === IN_LIST_OPERATOR) {
                        props.value = IN_LIST_OPERATOR;
                        // Find and update the label in options
                        props.options = props.options.map(([key, label]) => {
                            if (key === IN_LIST_OPERATOR || key.includes(`"${IN_LIST_OPERATOR}"`)) {
                                return [key, negate ? _t("is not in list") : _t("is in list")];
                            }
                            return [key, label];
                        });
                    }
                    
                    return props;
                },
                isSupported([operator]) {
                    if (operator === IN_LIST_OPERATOR) {
                        return true;
                    }
                    return super.isSupported.apply(this, arguments);
                }
            });
        }
        
        return info;
    },

    getValueEditorInfo(node) {
        const fieldDef = this.getFieldDef(node.path);
        const [operator] = node.value;
        if (operator === IN_LIST_OPERATOR) {
            return {
                component: Input,
                extractProps: ({ value, update }) => {
                    // Generate appropriate placeholder based on field type
                    let placeholder = _t("Enter comma-separated values...");
                    if (fieldDef) {
                        switch (fieldDef.type) {
                            case 'integer':
                                placeholder = _t("Enter comma-separated integers (e.g., 1, 2, 3)");
                                break;
                            case 'float':
                                placeholder = _t("Enter comma-separated decimals (e.g., 1.5, 2.0, 3.14)");
                                break;
                            case 'char':
                            case 'text':
                                placeholder = _t("Enter comma-separated text values (e.g., value1, value2, value3)");
                                break;
                        }
                    }
                    return {
                        value: Array.isArray(value) ? value.join(", ") : (value || ""),
                        update: (inputValue) => {
                            const { values, error } = parseInputValues(inputValue, fieldDef?.type || 'char');

                            if (error) {
                                console.error("in_list operator error:", error);
                                return;
                            }

                            update(values);
                        },
                        placeholder: placeholder
                    };
                },
                isSupported: (value) => {
                    return Array.isArray(value) ||
                        typeof value === "string" ||
                        typeof value === "number" ||
                        value === null ||
                        value === undefined;
                },
                defaultValue: () => [],
                stringify: (value) => {
                    if (Array.isArray(value)) {
                        return value.join(", ");
                    }
                    if (typeof value === "number") {
                        return value.toString();
                    }
                    return value || "";
                },
                message: _t("Invalid value format for list input")
            };
        }

        return super.getValueEditorInfo(node);
    }
});