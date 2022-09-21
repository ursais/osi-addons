odoo.define("web_many2many_groupby.ListController", function (require) {
    "use strict";

    var core = require("web.core");
    const ListController = require("web.ListController");
    var Dialog = require("web.Dialog");

    var _t = core._t;

    ListController.include({
        _confirmSave: function (id) {
            var state = this.model.get(this.handle);
            return this._updateRendererState(state, {
                noRender: !state.isM2MGrouped,
            }).then(this._setMode.bind(this, "readonly", id));
        },
        _getActionMenuItems: function (state) {
            if (!this.hasActionMenus || !this.selectedRecords.length) {
                return null;
            }
            const {isM2MGrouped} = state;
            const props = this._super(...arguments);
            const otherActionItems = [];
            if (this.isExportEnable && !isM2MGrouped) {
                otherActionItems.push({
                    description: _t("Export"),
                    callback: () => this._onExportData(),
                });
            }
            if (this.archiveEnabled && !isM2MGrouped) {
                otherActionItems.push(
                    {
                        description: _t("Archive"),
                        callback: () => {
                            Dialog.confirm(
                                this,
                                _t(
                                    "Are you sure that you want to archive all the \
                                    selected records?"
                                ),
                                {
                                    confirm_callback: () =>
                                        this._toggleArchiveState(true),
                                }
                            );
                        },
                    },
                    {
                        description: _t("Unarchive"),
                        callback: () => this._toggleArchiveState(false),
                    }
                );
            }
            if (this.activeActions.delete) {
                otherActionItems.push({
                    description: _t("Delete"),
                    callback: () => this._onDeleteSelectedRecords(),
                });
            }
            return Object.assign(props, {
                items: Object.assign({}, this.toolbarActions, {
                    other: otherActionItems,
                }),
            });
        },
        _onReload(ev) {
            const {isM2MGrouped} = this.model.get(this.handle);
            if (isM2MGrouped) {
                // Ask for the main record to be reloaded.
                ev.data.db_id = this.handle;
            }
            this._super(...arguments);
        },
    });
});
