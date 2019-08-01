odoo.define('osi_analytic_segments.ReconciliationModel', function (require) {
    "use strict";

    var BasicModel = require('web.BasicModel');
    var field_utils = require('web.field_utils');
    var utils = require('web.utils');
    var session = require('web.session');
    var CrashManager = require('web.CrashManager');
    var core = require('web.core');
    var _t = core._t;

    BasicModel.extend({
        avoidCreate: false,
        quickCreateFields: ['account_id', 'amount', 'analytic_account_id', 'label', 'tax_id', 'force_tax_included', 'analytic_tag_ids', 'analytic_segment_one_id', 'analytic_segment_two_id'],

        /**
         * Add lines into the propositions from the reconcile model
         * Can add 2 lines, and each with its taxes. The second line become editable
         * in the create mode.
         *
         * @see 'updateProposition' method for more informations about the
         * 'amount_type'
         *
         * @param {string} handle
         * @param {integer} reconcileModelId
         * @returns {Deferred}
         */
        quickCreateProposition: function (handle, reconcileModelId) {
            var line = this.getLine(handle);
            var reconcileModel = _.find(this.reconcileModels, function (r) {return r.id === reconcileModelId;});
            var fields = ['account_id', 'amount', 'amount_type', 'analytic_account_id', 'journal_id', 'label', 'force_tax_included', 'tax_id', 'analytic_tag_ids', 'analytic_segment_one_id', 'analytic_segment_two_id'];
            this._blurProposition(handle);

            var focus = this._formatQuickCreate(line, _.pick(reconcileModel, fields));
            focus.reconcileModelId = reconcileModelId;
            line.reconciliation_proposition.push(focus);

            if (reconcileModel.has_second_line) {
                var second = {};
                _.each(fields, function (key) {
                    second[key] = ("second_"+key) in reconcileModel ? reconcileModel["second_"+key] : reconcileModel[key];
                });
                focus = this._formatQuickCreate(line, second);
                focus.reconcileModelId = reconcileModelId;
                line.reconciliation_proposition.push(focus);
                this._computeReconcileModels(handle, reconcileModelId);
            }
            line.createForm = _.pick(focus, this.quickCreateFields);
            return this._computeLine(line);
        },
        /**
         * Apply default values for the proposition, format datas and format the
         * base_amount with the decimal number from the currency
         *
         * @private
         * @param {Object} line
         * @param {Object} values
         * @returns {Object}
         */
        _formatQuickCreate: function (line, values) {
            values = values || {};
            var today = new moment().utc().format();
            var account = this._formatNameGet(values.account_id);
            var formatOptions = {
                currency_id: line.st_line.currency_id,
            };

            console.log("File is loaded!")
            var amount = values.amount !== undefined ? values.amount : line.balance.amount;
            var prop = {
                'id': _.uniqueId('createLine'),
                'label': values.label || line.st_line.name,
                'account_id': account,
                'account_code': account ? this.accounts[account.id] : '',
                'analytic_account_id': this._formatNameGet(values.analytic_account_id),
                'analytic_tag_ids': this._formatMany2ManyTags(values.analytic_tag_ids || []),
                'analytic_segment_one_id': this._formatNameGet(values.analytic_segment_one_id),
                'analytic_segment_two_id': this._formatNameGet(values.analytic_segment_two_id),
                'journal_id': this._formatNameGet(values.journal_id),
                'tax_id': this._formatNameGet(values.tax_id),
                'debit': 0,
                'credit': 0,
                'date': values.date ? values.date : field_utils.parse.date(today, {}, {isUTC: true}),
                'base_amount': values.amount_type !== "percentage" ?
                    (amount) : line.balance.amount * values.amount / 100,
                'percent': values.amount_type === "percentage" ? values.amount : null,
                'link': values.link,
                'display': true,
                'invalid': true,
                '__tax_to_recompute': true,
                'is_tax': values.is_tax,
                '__focus': '__focus' in values ? values.__focus : true,
            };
            if (prop.base_amount) {
                // Call to format and parse needed to round the value to the currency precision
                var sign = prop.base_amount < 0 ? -1 : 1;
                var amount = field_utils.format.monetary(Math.abs(prop.base_amount), {}, formatOptions);
                prop.base_amount = sign * field_utils.parse.monetary(amount, {}, formatOptions);
            }

            if(prop.tax_id){
                // Set the amount_type value.
                prop.tax_id.amount_type = this.taxes[prop.tax_id.id].amount_type;
                // Set the price_include value.
                prop.tax_id.price_include = this.taxes[prop.tax_id.id].price_include;
            }

            // Set the force_tax_included value.
            if(prop.tax_id && values.force_tax_included !== undefined)
                prop.force_tax_included = values.force_tax_included;
            else if(prop.tax_id && this.taxes[prop.tax_id.id].price_include)
                prop.force_tax_included = this.taxes[prop.tax_id.id].price_include;
            prop.amount = prop.base_amount;
            return prop;
        },
    });
});
