/** @odoo-module **/

import {WarningDialog} from "@web/core/errors/error_dialogs";
import {insertThousandsSep} from "@web/core/utils/numbers";
import {jsonrpc} from "@web/core/network/rpc_service";
import {localization} from "@web/core/l10n/localization";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProductConfigurator = publicWidget.Widget.extend({
    selector: ".product_configurator",
    events: {
        "change.datetimepicker #product_config_form .input-group.date":
            "_onChangeDateTime",
        "change #product_config_form .config_attribute": "_onChangeConfigAttribute",
        "change #product_config_form .custom_config_value.config_attachment":
            "_onChangeFile",
        "change #product_config_form .custom_config_value": "_onChangeCustomField",
        "click #product_config_form .config_step": "_onClickConfigStep",
        "click #product_config_form .btnNextStep": "_onClickBtnNext",
        "click #product_config_form .btnPreviousStep": "_onClickBtnPrevious",
        "submit #product_config_form": "_onSubmitConfigForm",
        "click #product_config_form .image_config_attr_value_radio":
            "_onClickRadioImage",
        "change #product_config_form .custom_config_value.spinner_qty":
            "_onChangeQtySpinner",
        "click #product_config_form .js_add_qty": "_onClickAddQty",
        "click #product_config_form .js_remove_qty": "_onClickRemoveQty",
    },

    start: function () {
        this._super.apply(this, arguments);
        this.config_form = this.$("#product_config_form");
        // For file (custom field)
        this.image_dict = {};
    },

    _onChangeConfigAttribute: async function (event) {
        const attribute = [event.currentTarget];
        this._checkRequiredFields(attribute);
        const flag = this._checkChange(attribute[0]);

        if (flag) {
            const form_data = this.config_form.serializeArray();
            for (const field_name in this.image_dict) {
                form_data.push({
                    name: field_name,
                    value: this.image_dict[field_name],
                });
            }

            this.call("ui", "block");

            const data = await jsonrpc("/website_product_configurator/onchange", {
                form_values: form_data,
                field_name: attribute[0].getAttribute("name"),
            });

            if (data.error) {
                this.openWarningDialog(data.error);
            } else {
                const {
                    value: values,
                    domain: domains,
                    open_cfg_step_line_ids,
                    config_image_vals,
                    decimal_precision,
                } = data;

                this._applyDomainOnValues(domains);
                this._setDataOldValId();
                this._handleOpenSteps(open_cfg_step_line_ids);
                this._setImageUrl(config_image_vals);
                this._setWeightPrice(values.weight, values.price, decimal_precision);
            }

            this.call("ui", "unblock");
            this._handleCustomAttribute(event);
        }
    },

    _checkChange: function (attr_field) {
        var flag = true;
        if (attr_field.classList.contains("cfg-radio")) {
            flag = !(
                attr_field.getAttribute("data-old-val-id") ===
                $(attr_field).find("input:checked").val()
            );
        } else if (attr_field.classList.contains("cfg-select")) {
            flag = !($(attr_field).attr("data-old-val-id") === attr_field.value);
        }
        return flag;
    },

    openWarningDialog: function (message) {
        this.call("dialog", "add", WarningDialog, {
            title: "Warning!!!",
            message: message,
        });
    },

    _applyDomainOnValues: function (domains) {
        var self = this;
        Object.entries(domains).forEach(function ([attr_id, domain]) {
            var $selection = self.config_form.find("#" + attr_id);
            var $options = $selection.find(".config_attr_value");
            $options.each(function (index, option) {
                var condition = domain[0][1];
                if (condition === "in" || condition === "=") {
                    if ($.inArray(parseInt(option.value, 10), domain[0][2]) < 0) {
                        $(option).attr("disabled", true);
                        if ($(option).parent().parent().find("label")) {
                            $(option)
                                .parent()
                                .parent()
                                .find("label")
                                .attr("enabled", "False");
                        }
                        if (option.selected) {
                            option.selected = false;
                        } else if (option.checked) {
                            option.checked = false;
                        }
                    } else {
                        $(option).attr("disabled", false);
                        if ($(option).parent().parent().find("label")) {
                            $(option)
                                .parent()
                                .parent()
                                .find("label")
                                .attr("enabled", "True");
                        }
                    }
                } else if (condition === "not in" || condition === "!=") {
                    if ($.inArray(parseInt(option.value, 10), domain[0][2]) < 0) {
                        $(option).attr("disabled", false);
                        if ($(option).parent().parent().find("label")) {
                            $(option)
                                .parent()
                                .parent()
                                .find("label")
                                .attr("enabled", "True");
                        }
                    } else {
                        $(option).attr("disabled", true);
                        if ($(option).parent().parent().find("label")) {
                            $(option)
                                .parent()
                                .parent()
                                .find("label")
                                .attr("enabled", "False");
                        }
                        if (option.selected) {
                            option.selected = false;
                        } else if (option.checked) {
                            option.checked = false;
                        }
                    }
                }
            });
            if (
                !domain[0][2].length &&
                $selection.attr("data-attr-required") &&
                $selection.hasClass("required_config_attrib")
            ) {
                $selection.removeClass("required_config_attrib");
                $selection.removeClass("textbox-border-color");
            } else if (
                domain[0][2].length &&
                !$selection.hasClass("required_config_attrib") &&
                $selection.attr("data-attr-required")
            ) {
                $selection.addClass("required_config_attrib");
            }
        });
    },

    _setDataOldValId: function () {
        var selections = this.$(".cfg-select.config_attribute");
        Array.prototype.forEach.call(selections, function (select) {
            $(select).attr("data-old-val-id", $(select).val());
        });
        var fieldsets = this.$(".cfg-radio.config_attribute");
        fieldsets.each(function () {
            var $fieldset = $(this);
            $fieldset.attr(
                "data-old-val-id",
                $fieldset.find("input:checked").val() || ""
            );
        });
    },

    _handleOpenSteps: function (open_cfg_step_line_ids) {
        var $steps = this.config_form.find(".config_step");
        for (var i = 0; i < $steps.length; i++) {
            var config_step = $($steps[i]);
            var step_id = config_step.attr("data-step-id");
            if ($.inArray(step_id, open_cfg_step_line_ids) < 0) {
                if (!config_step.hasClass("d-none")) {
                    config_step.addClass("d-none");
                }
            } else if (config_step.hasClass("d-none")) {
                config_step.removeClass("d-none");
            }
        }
    },

    _setImageUrl: function (config_image_vals) {
        var images = "";
        if (config_image_vals) {
            var model = config_image_vals.name;
            config_image_vals.config_image_ids.forEach(function (line) {
                images +=
                    "<img itemprop='image' class='cfg_image img img-responsive pull-right'";
                images += "src='/web/image/" + model + "/" + line + "/image_1920'/>";
            });
        }
        if (images) {
            this.$("#product_config_image").html(images);
        }
    },

    price_to_str: function (price, precision) {
        var formatted = price.toFixed(precision).split(".");
        const {thousandsSep, decimalPoint, grouping} = localization;
        formatted[0] = insertThousandsSep(formatted[0], thousandsSep, grouping);
        return formatted.join(decimalPoint);
    },

    weight_to_str: function (weight, precision) {
        var formatted = weight.toFixed(precision).split(".");
        const {thousandsSep, decimalPoint, grouping} = localization;
        formatted[0] = insertThousandsSep(formatted[0], thousandsSep, grouping);
        return formatted.join(decimalPoint);
    },

    _setWeightPrice: function (weight, price, decimal_precisions) {
        var formatted_price = this.price_to_str(price, decimal_precisions.price);
        var formatted_weight = this.weight_to_str(weight, decimal_precisions.weight);
        this.$(".config_product_weight").text(formatted_weight);
        this.$(".config_product_price")
            .find(".oe_currency_value")
            .text(formatted_price);
    },

    _handleCustomAttribute: function (event) {
        var container = $(event.currentTarget).closest(".tab-pane.container");
        var attribute_id = $(event.currentTarget).attr("data-oe-id");
        var custom_value = container.find(
            ".custom_config_value[data-oe-id=" + attribute_id + "]"
        );
        var custom_value_container = custom_value.closest(
            ".custom_field_container[data-oe-id=" + attribute_id + "]"
        );
        var attr_field = container.find(
            ".config_attribute[data-oe-id=" + attribute_id + "]"
        );
        var custom_config_attr = attr_field.find(".custom_config_attr_value");
        var flag_custom = false;
        if (
            custom_config_attr.length &&
            custom_config_attr[0].tagName === "OPTION" &&
            custom_config_attr[0].selected
        ) {
            flag_custom = true;
        } else if (
            custom_config_attr.length &&
            custom_config_attr[0].tagName === "INPUT" &&
            custom_config_attr[0].checked
        ) {
            flag_custom = true;
        }
        if (flag_custom && custom_value_container.hasClass("d-none")) {
            custom_value_container.removeClass("d-none");
            custom_value.addClass("required_config_attrib");
        } else if (!flag_custom && !custom_value_container.hasClass("d-none")) {
            custom_value_container.addClass("d-none");
            if (custom_value.hasClass("required_config_attrib")) {
                custom_value.removeClass("required_config_attrib");
            }
        }
    },

    _onChangeDateTime: function (event) {
        var attribute = $(event.currentTarget).find("input.required_config_attrib");
        this._checkRequiredFields(attribute);
    },

    _checkRequiredFields: function (config_attr) {
        var flag_all = true;
        for (var i = 0; i < config_attr.length; i++) {
            var flag = true;
            if (!$(config_attr[i]).hasClass("required_config_attrib")) {
                flag = true;
            } else if ($(config_attr[i]).hasClass("cfg-radio")) {
                flag = this._checkRequiredFieldsRadio($(config_attr[i]));
            } else if (!config_attr[i].value.trim() || config_attr[i].value === "0") {
                flag = false;
            }
            if (!flag) {
                this.$(config_attr[i]).addClass("textbox-border-color");
            } else if (flag && $(config_attr[i]).hasClass("textbox-border-color")) {
                this.$(config_attr[i]).removeClass("textbox-border-color");
            }
            flag_all &= flag;
        }
        return flag_all;
    },

    _checkRequiredFieldsRadio: function (parent_container) {
        var radio_inputs = parent_container.find(".config_attr_value:checked");
        if (radio_inputs.length) {
            return true;
        }
        return false;
    },

    _onChangeFile: function (ev) {
        var result = $.Deferred();
        var file = ev.target.files[0];
        if (!file) {
            return true;
        }
        var files_data = "";
        var BinaryReader = new FileReader();
        // File read as DataURL
        BinaryReader.readAsDataURL(file);
        BinaryReader.onloadend = function (upload) {
            var buffer = upload.target.result;
            buffer = buffer.split(",")[1];
            files_data = buffer;
            this.image_dict[ev.target.name] = files_data;
            result.resolve();
        };
        return result.promise();
    },

    _onChangeCustomField: function (event) {
        var attribute = [event.currentTarget];
        this._checkRequiredFields(attribute);
    },

    _onClickConfigStep: function (event) {
        var next_step = event.currentTarget.getAttribute("data-step-id");
        var result = this._onChangeConfigStep(event, next_step);
        if (result) {
            this._handleFooterButtons($(event.currentTarget));
        } else {
            event.preventDefault();
            event.stopPropagation();
        }
    },

    _onChangeConfigStep: function (event, next_step) {
        var self = this;
        var active_step = self.config_form
            .find(".tab-content")
            .find(".tab-pane.active.show");

        var config_attr = active_step.find(".form-control.required_config_attrib");
        var flag = self._checkRequiredFields(config_attr);
        var config_step_header = self.config_form.find(".nav.nav-tabs");
        var current_config_step = config_step_header
            .find(".nav-item.config_step > a.active")
            .parent()
            .attr("data-step-id");
        var form_data = self.config_form.serializeArray();
        for (var field_name in self.image_dict) {
            form_data.push({name: field_name, value: self.image_dict[field_name]});
        }
        if (flag) {
            self.call("ui", "block");
            return jsonrpc("/website_product_configurator/save_configuration", {
                form_values: form_data,
                next_step: next_step || false,
                current_step: current_config_step || false,
                submit_configuration: event.type === "submit",
            }).then(function (data) {
                if (data.error) {
                    self.openWarningDialog(data.error);
                }
                self.call("ui", "unblock");
                return data;
            });
        }
        return false;
    },

    _handleFooterButtons: function (step) {
        var step_count = step.attr("data-step-count");
        var total_steps = $("#total_attributes").val();
        if (step_count === "1") {
            $(".btnPreviousStep").addClass("d-none");
            $(".btnNextStep").removeClass("d-none");
            $(".configureProduct").addClass("d-none");
        } else if (step_count === total_steps) {
            $(".btnPreviousStep").removeClass("d-none");
            $(".btnNextStep").addClass("d-none");
            $(".configureProduct").removeClass("d-none");
        } else {
            $(".btnPreviousStep").removeClass("d-none");
            $(".btnNextStep").removeClass("d-none");
            $(".configureProduct").addClass("d-none");
        }
    },

    _onClickBtnNext: function () {
        var active_step = this.config_form
            .find(".tab-content")
            .find(".tab-pane.active.show");

        var config_attr = active_step.find(".form-control.required_config_attrib");
        var flag = this._checkRequiredFields(config_attr);
        var nextTab = $(".nav-tabs > .config_step > .active")
            .parent()
            .nextAll("li:not(.d-none):first")
            .find("a")
            .trigger("click");
        if (flag) {
            nextTab.tab("show");
        }
    },

    _onClickBtnPrevious: function () {
        var active_step = this.config_form
            .find(".tab-content")
            .find(".tab-pane.active.show");

        var config_attr = active_step.find(".form-control.required_config_attrib");
        var flag = this._checkRequiredFields(config_attr);
        var previousTab = $(".nav-tabs > .config_step > .active")
            .parent()
            .prevAll("li:not(.d-none):first")
            .find("a")
            .trigger("click");
        if (flag) {
            previousTab.tab("show");
        }
    },

    _onSubmitConfigForm: function (event) {
        var self = this;
        event.preventDefault();
        event.stopPropagation();

        var result = self._onChangeConfigStep(event, false);
        if (result) {
            result.then(function (data) {
                if (data) {
                    if (data.next_step) {
                        self._openNextStep(data.next_step);
                    }
                    if (data.redirect_url) {
                        window.location = data.redirect_url;
                    }
                }
            });
        }
    },

    _openNextStep: function (step) {
        var config_step_header = this.config_form.find(".nav.nav-tabs");
        var config_step = config_step_header.find(
            ".nav-item.config_step > .nav-link.active"
        );
        if (config_step.length) {
            config_step.removeClass("active");
        }
        var active_step = this.config_form
            .find(".tab-content")
            .find(".tab-pane.active.show");
        active_step.removeClass("active");
        active_step.removeClass("show");

        var next_step = config_step_header.find(
            ".nav-item.config_step[data-step-id=" + step + "] > .nav-link"
        );
        if (next_step.length) {
            next_step.addClass("active");
            var selector = next_step.attr("href");
            var step_to_active = this.config_form.find(".tab-content").find(selector);
            step_to_active.addClass("active");
            step_to_active.addClass("show");
        }
    },

    _onClickRadioImage: function (event) {
        var val_id = $(event.currentTarget).data("val-id");
        var value_input = $(event.currentTarget)
            .closest(".cfg-radio")
            .find('.config_attr_value[data-oe-id="' + val_id + '"]');
        if (value_input.prop("disabled")) {
            return;
        }
        if (value_input.length) {
            if (
                value_input.attr("type") === "checkbox" &&
                value_input.prop("checked")
            ) {
                value_input.prop("checked", false);
            } else {
                value_input.prop("checked", "checked");
            }
            value_input.change();
        }
    },

    _onChangeQtySpinner: function (ev) {
        this._handleSppinerCustomValue(ev);
    },

    _onClickAddQty: function (ev) {
        var custom_value = this._handleSppinerCustomValue(ev);
        this._checkRequiredFields(custom_value);
    },

    _onClickRemoveQty: function (ev) {
        var custom_value = this._handleSppinerCustomValue(ev);
        this._checkRequiredFields(custom_value);
    },

    _handleSppinerCustomValue: function (ev) {
        var self = this;
        ev.preventDefault();
        ev.stopPropagation();

        var current_target = $(ev.currentTarget);
        var custom_value = current_target
            .closest(".input-group")
            .find("input.custom_config_value");
        var max_val = parseFloat(custom_value.attr("max") || Infinity);
        var min_val = parseFloat(custom_value.attr("min") || 0);
        var new_qty = min_val;
        var ui_val = parseFloat(custom_value.val());
        var custom_type = custom_value.attr("data-type");
        var message = "";
        var attribute_name = custom_value;
        if (isNaN(ui_val)) {
            message = "Please enter a number.";
            self._displayTooltip(custom_value, message);
        } else if (custom_type === "int" && ui_val % 1 !== 0) {
            message = "Please enter a Integer.";
            self._displayTooltip(custom_value, message);
        } else {
            var quantity = ui_val || 0;
            new_qty = quantity;
            if (current_target.has(".fa-minus").length) {
                new_qty = quantity - 1;
            } else if (current_target.has(".fa-plus").length) {
                new_qty = quantity + 1;
            }
            if (new_qty > max_val) {
                attribute_name = custom_value
                    .closest(".tab-pane")
                    .find(
                        'label[data-oe-id="' + custom_value.attr("data-oe-id") + '"]'
                    );
                message =
                    "Selected custom value " +
                    attribute_name.text() +
                    " must not be greater than " +
                    max_val;
                self._displayTooltip(custom_value, message);
                new_qty = max_val;
            } else if (new_qty < min_val) {
                attribute_name = custom_value
                    .closest(".tab-pane")
                    .find(
                        'label[data-oe-id="' + custom_value.attr("data-oe-id") + '"]'
                    );
                message =
                    "Selected custom value " +
                    attribute_name.text() +
                    " must be at least " +
                    min_val;
                self._displayTooltip(custom_value, message);
                new_qty = min_val;
            }
        }
        custom_value.val(new_qty);
        self._disableEnableAddRemoveQtyButton(
            current_target,
            new_qty,
            max_val,
            min_val
        );
        return custom_value;
    },

    _displayTooltip: function (config_attribute, message) {
        $(config_attribute)
            .tooltip({
                title: message,
                placement: "bottom",
                trigger: "manual",
            })
            .tooltip("show");
        setTimeout(function () {
            $(config_attribute).tooltip("dispose");
        }, 4000);
    },

    _disableEnableAddRemoveQtyButton: function (
        current_target,
        quantity,
        max_val,
        min_val
    ) {
        var container = current_target.closest(".custom_field_container");
        if (quantity >= max_val) {
            container.find(".js_add_qty").addClass("btn-disabled");
        } else if (quantity < max_val && $(".js_add_qty").hasClass("btn-disabled")) {
            container.find(".js_add_qty").removeClass("btn-disabled");
        }
        if (quantity <= min_val) {
            container.find(".js_remove_qty").addClass("btn-disabled");
        } else if (quantity > min_val && $(".js_remove_qty").hasClass("btn-disabled")) {
            container.find(".js_remove_qty").removeClass("btn-disabled");
        }
    },
});
export default publicWidget.registry.ProductConfigurator;
