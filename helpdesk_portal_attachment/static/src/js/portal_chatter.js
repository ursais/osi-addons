odoo.define('helpdesk_portal_attachment.portal_chatter', function(require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var portal_chatter = require('portal.chatter').PortalChatter;

var qweb = core.qweb;
var _t = core._t;


portal_chatter.include({

    events: _.extend({}, portal_chatter.prototype.events, {
        'change .o_portal_chatter_file_input': '_onFileInputChange',
        'click .o_portal_chatter_attachment_btn': '_onAttachmentButtonClick',
        'click .o_portal_chatter_attachment_delete': '_onAttachmentDeleteClick',
    }),

    init: function(parent, options){
        this._super.apply(this, arguments);
//        this.options = _.defaults(options || {}, {
//            'allow_composer': true,
//            'display_composer': false,
//            'csrf_token': odoo.csrf_token,
//            'token': false,
//            'res_model': false,
//            'res_id': false,
//        });
        this.attachments = [];
    },

    start: function () {
        var self = this;
        this.$attachmentButton = this.$('.o_portal_chatter_attachment_btn');
        this.$fileInput = this.$('.o_portal_chatter_file_input');
        this.$sendButton = this.$('.o_portal_chatter_composer_btn');
        this.$attachments = this.$('.o_portal_chatter_composer_form .o_portal_chatter_attachments');
        this.$attachmentIds = this.$('.o_portal_chatter_attachment_ids');
        this.$attachmentTokens = this.$('.o_portal_chatter_attachment_tokens');

        return this._super.apply(this, arguments).then(function () {
            if (self.options.default_attachment_ids) {
                self.attachments = self.options.default_attachment_ids || [];
                _.each(self.attachments, function(attachment) {
                    attachment.state = 'done';
                });
                self._updateAttachments();
            }
            return Promise.resolve();
        });
    },

    _loadTemplates: function(){
        this._super();
        ajax.loadXML('/helpdesk_portal_attachment/static/src/xml/portal_chatter.xml', qweb);
    },

    /**
     * @private
     */
    _onAttachmentButtonClick: function () {
        this.$fileInput.click();
    },

    /**
     * @private
     * @param {Event} ev
     * @returns {Promise}
     */
    _onAttachmentDeleteClick: function (ev) {
        var self = this;
        var attachmentId = $(ev.currentTarget).closest('.o_portal_chatter_attachment').data('id');
        var accessToken = _.find(this.attachments, {'id': attachmentId}).access_token;
        ev.preventDefault();
        ev.stopPropagation();

        this.$sendButton.prop('disabled', true);
        ajax.post('/portal/attachment/remove', {
            'attachment_id': attachmentId,
            'access_token': accessToken
        }).then(function () {
            self.attachments = _.reject(self.attachments, {'id': attachmentId});
            self._updateAttachments();
            self.$sendButton.prop('disabled', false);
        });
    },

        /**
     * @private
     * @returns {Promise}
     */
    _onFileInputChange: function () {
        var self = this;

        this.$sendButton.prop('disabled', true);

        return Promise.all(_.map(this.$fileInput[0].files, function (file) {
            return new Promise(function (resolve, reject) {
                var data = {
                    'name': file.name,
                    'file': file,
                    'res_id': self.options.res_id,
                    'res_model': self.options.res_model,
                    'access_token': self.options.token,
                };
                ajax.post('/portal/attachment/add', data).then(function (attachment) {
                    attachment.state = 'pending';
                    self.attachments.push(attachment)
                    self._updateAttachments();
                    resolve();
                }).fail(function (error) {
                    self.do_notify(_t("Something went wrong."), _t("The file <strong>%s</strong> could not be saved."));
                    resolve();
                });
            });
        })).then(function () {
            self.$sendButton.prop('disabled', false);
        });
    },

    /**
     * @private
     */
    _updateAttachments: function () {
        // var self = this;
        this.$attachmentIds.val(_.pluck(this.attachments, 'id'));
        this.$attachmentTokens.val(_.pluck(this.attachments, 'access_token'));
        this.$attachments.html(qweb.render('Chatter.Attachments', {
            attachments: this.attachments,
            showDelete: true,
        }));
    },
});

});
