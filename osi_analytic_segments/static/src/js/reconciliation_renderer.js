
odoo.define('osi_analytic_sales_simple.osi_analytic_sales_simple', function (require) {
    "use strict"; 
var Widget = require('web.Widget');
var relational_fields = require('web.relational_fields');
var basic_fields = require('web.basic_fields');
var core = require('web.core');
var time = require('web.time');
var session = require('web.session');
var qweb = core.qweb;
var _t = core._t;
var ReconciliationRenderer = require('account.ReconciliationRenderer');

console.log("file has been called");
//ADD FIELDS
ReconciliationRenderer.LineRenderer.extend({
    /**
     * create account_id, tax_id, analytic_account_id, analytic_tag_ids, label and amount fields
     *
     * @private
     * @param {object} state - statement line
     */
    _renderCreate: function (state) {
        console.log("IT SHOULD BE CALLED!");
        var self = this;
        this.model.makeRecord('account.bank.statement.line', [{
            relation: 'account.account',
            type: 'many2one',
            name: 'account_id',
            domain: [['company_id', '=', state.st_line.company_id]],
        }, {
            relation: 'account.journal',
            type: 'many2one',
            name: 'journal_id',
            domain: [['company_id', '=', state.st_line.company_id]],
        }, {
            relation: 'account.tax',
            type: 'many2one',
            name: 'tax_id',
            domain: [['company_id', '=', state.st_line.company_id]],
        }, {
            relation: 'account.analytic.account',
            type: 'many2one',
            name: 'analytic_account_id',
        }, {
            relation: 'account.analytic.tag',
            type: 'many2many',
            name: 'analytic_tag_ids',
        }, {
            type: 'boolean',
            name: 'force_tax_included',
        }, {
            type: 'char',
            name: 'label',
        }, {
            type: 'float',
            name: 'amount',
        }, {
            type: 'char', //TODO is it a bug or a feature when type date exists ?
            name: 'date',
        }], {
            account_id: {
                string: _t("Account"),
                domain: [['deprecated', '=', false]],
            },
            label: {string: _t("Label")},
            amount: {string: _t("Account")},
        }).then(function (recordID) {
            self.handleCreateRecord = recordID;
            var record = self.model.get(self.handleCreateRecord);

            self.fields.account_id = new relational_fields.FieldMany2One(self,
                'account_id', record, {mode: 'edit'});

            self.fields.journal_id = new relational_fields.FieldMany2One(self,
                'journal_id', record, {mode: 'edit'});

            self.fields.tax_id = new relational_fields.FieldMany2One(self,
                'tax_id', record, {mode: 'edit', additionalContext: {append_type_to_tax_name: true}});

            self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                'analytic_account_id', record, {mode: 'edit'});

            self.fields.analytic_tag_ids = new relational_fields.FieldMany2ManyTags(self,
                'analytic_tag_ids', record, {mode: 'edit'});

            self.fields.force_tax_included = new basic_fields.FieldBoolean(self,
                'force_tax_included', record, {mode: 'edit'});

            self.fields.label = new basic_fields.FieldChar(self,
                'label', record, {mode: 'edit'});

            self.fields.amount = new basic_fields.FieldFloat(self,
                'amount', record, {mode: 'edit'});
            
            self.fields.date = new basic_fields.FieldDate(self,
                'date', record, {mode: 'edit'});

            var $create = $(qweb.render("reconciliation.line.create", {'state': state}));
            self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.account_id));
            self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
            self.fields.tax_id.appendTo($create.find('.create_tax_id .o_td_field'));
            self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
            self.fields.analytic_tag_ids.appendTo($create.find('.create_analytic_tag_ids .o_td_field'));
            self.fields.force_tax_included.appendTo($create.find('.create_force_tax_included .o_td_field'))
            self.fields.label.appendTo($create.find('.create_label .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.label));
            self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.amount));
            self.fields.date.appendTo($create.find('.create_date .o_td_field'))
            self.$('.create').append($create);

            function addRequiredStyle(widget) {
                widget.$el.addClass('o_required_modifier');
            }
        });
    },

    });
});