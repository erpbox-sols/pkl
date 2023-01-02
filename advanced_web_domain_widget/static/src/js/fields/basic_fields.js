odoo.define('advanced_web_domain_widget.basic_fields', function (require) {
    "use strict";
    
    /**
     * This module contains most of the basic (meaning: non relational) field
     * widgets. Field widgets are supposed to be used in views inheriting from
     * BasicView, so, they can work with the records obtained from a BasicModel.
     */
    
    var AbstractField = require('web.AbstractField');
    var config = require('web.config');
    var core = require('web.core');
    var Domain = require('web.Domain');
    var DomainSelector = require('advanced_web_domain_widget.TerabitsDomainSelector');
    var DomainSelectorDialog = require('web.DomainSelectorDialog');
    var view_dialogs = require('web.view_dialogs');
    
    // require("web.zoomodoo");
    
    var qweb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;
    
    /**
     * The "Domain" field allows the user to construct a technical-prefix domain
     * thanks to a tree-like interface and see the selected records in real time.
     * In debug mode, an input is also there to be able to enter the prefix char
     * domain directly (or to build advanced domains the tree-like interface does
     * not allow to).
     */
     var TerabitsFieldDomain = AbstractField.extend({
        resetOnAnyFieldChange: true,
        events: _.extend({}, AbstractField.prototype.events, {
            "click .o_domain_show_selection_button": "_onShowSelectionButtonClick",
            "click .o_field_domain_dialog_button": "_onDialogEditButtonClick",
            "click .o_refresh_count": "_onRefreshCountClick",
        }),
        custom_events: _.extend({}, AbstractField.prototype.custom_events, {
            domain_changed: "_onDomainSelectorValueChange",
            domain_selected: "_onDomainSelectorDialogValueChange",
            open_record: "_onOpenRecord",
        }),
        /**
         * @constructor
         * @override init from AbstractField
         */
        init: function () {
            this._super.apply(this, arguments);
    
            this.inDialog = !!this.nodeOptions.in_dialog;
            this.fsFilters = this.nodeOptions.fs_filters || {};
    
            this.className = "o_field_domain";
            if (this.mode === "edit") {
                this.className += " o_edit_mode";
            }
            if (!this.inDialog) {
                this.className += " o_inline_mode";
            }
    
            this._setState();
    
            this._isValidForModel = true;
            this.nbRecords = null;
            this.lastCountFetchKey = null; // used to prevent from unnecessary fetching the count
            this.debugEdition = false; // true iff the domain was edited with the textarea (in debug only)
        },
        /**
         * We use the on_attach_callback hook here when widget is attached to the DOM, so that
         * the inline 'DomainSelector' widget allows field selector to overflow if widget is
         * attached within a modal.
         */
        on_attach_callback() {
            if (this.domainSelector && !this.inDialog) {
                this.domainSelector.on_attach_callback();
            }
        },
    
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------
    
        /**
         * The record is about to be saved, we need to ensure that the current
         * domain is valid, if we manually edited it with the textarea. To do so,
         * we perform a search_count with that domain.
         *
         * @override
         * @returns {Promise|undefined}
         */
        commitChanges() {
            if (this.debugEdition) {
                return this._fetchCount();
            }
        },
        /**
         * A domain field is always set since the false value is considered to be
         * equal to "[]" (match all records).
         *
         * @override
         */
        isSet: function () {
            return true;
        },
        /**
         * @override isValid from AbstractField.isValid
         * Parsing the char value is not enough for this field. It is considered
         * valid if the internal domain selector was built correctly and that the
         * query to the model to test the domain did not fail.
         *
         * @returns {boolean}
         */
        isValid: function () {
            return (
                this._super.apply(this, arguments)
                && (!this.domainSelector || this.domainSelector.isValid())
                && this._isValidForModel
            );
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * Fetches the number of records matching the current domain.
         *
         * @private
         * @param {boolean} [force=false] if true, performs the rpc, even if the
         *   domain is the same as before
         * @returns {Promise}
         */
         _fetchCount(force = false) {
            if (!this._domainModel) {
                this._isValidForModel = true;
                this.nbRecords = 0;
                return Promise.resolve();
            }
    
            // do not re-fetch the count if nothing has changed
            const value = this.value || "[]"; // false stands for the empty domain
            const key = `${this._domainModel}/${value}`;
            if (!force && this.lastCountFetchKey === key) {
                return this.lastCountFetchProm;
            }
            this.lastCountFetchKey = key;
    
            this.nbRecords = null;
    
            const context = this.record.getContext({ fieldName: this.name });
            this.lastCountFetchProm = new Promise((resolve) => {
                this._rpc({
                    model: this._domainModel,
                    method: 'search_count',
                    args: [Domain.prototype.stringToArray(value, this.record.evalContext)],
                    context: context
                }, { shadow: true }).then((nbRecords) => {
                    this._isValidForModel = true;
                    this.nbRecords = nbRecords;
                    resolve();
                }).guardedCatch((reason) => {
                    reason.event.preventDefault(); // prevent traceback (the search_count might be intended to break)
                    this._isValidForModel = false;
                    this.nbRecords = 0;
                    resolve();
                });
            });
            return this.lastCountFetchProm;
        },
        /**
         * @private
         * @override _render from AbstractField
         * @returns {Promise}
         */
        _render: async function () {
            // If there is no model, only change the non-domain-selector content
            if (!this._domainModel) {
                this._replaceContent();
                return Promise.resolve();
            }
            // Convert char value to array value
            var value = this.value || "[]";
    
            // Create the domain selector or change the value of the current one...
            var def;
            if (!this.domainSelector) {
                this.domainSelector = new DomainSelector.TerabitsDomainSelector(this, this._domainModel, value, {
                    readonly: this.mode === "readonly" || this.inDialog,
                    filters: this.fsFilters,
                    debugMode: config.isDebug(),
                });
                def = this.domainSelector.prependTo(this.$el);
            } else if (!this.debugEdition) {
                // do not update the domainSelector if we edited the domain with the textarea
                // as we don't want it to format what we just wrote
                def = this.domainSelector.setDomain(value);
            }
    
            // ... then replace the other content (matched records, etc)
            await Promise.resolve(def);
            this._replaceContent();
    
            // Finally, fetch the number of records matching the domain, but do not
            // wait for it to render the field widget (simply update the number of
            // records when we know it)
            if (!this.debugEdition) {
                // do not automatically recompute the count if we're editing the
                // domain with the textarea
                this._fetchCount().then(() => this._replaceContent());
            }
        },
        /**
         * Render the field DOM except for the domain selector part. The full field
         * DOM is composed of a DIV which contains the domain selector widget,
         * followed by other content. This other content is handled by this method.
         *
         * @private
         */
        _replaceContent: function () {
            if (this._$content) {
                this._$content.remove();
            }
            this._$content = $(qweb.render("TerabitsFieldDomain.content", {
                hasModel: !!this._domainModel,
                isValid: !!this._isValidForModel,
                nbRecords: this.nbRecords,
                inDialog: this.inDialog,
                editMode: this.mode === "edit",
                isDebug: config.isDebug(),
            }));
            this._$content.appendTo(this.$el);
        },
        /**
         * @override _reset from AbstractField
         * Check if the model the field works with has (to be) changed.
         *
         * @private
         */
        _reset: function (record, ev) {
            this._super.apply(this, arguments);
            var oldDomainModel = this._domainModel;
            this._setState();
            if (this.domainSelector && this._domainModel !== oldDomainModel) {
                // If the model has changed, destroy the current domain selector
                this.domainSelector.destroy();
                this.domainSelector = null;
            }
            if (!ev || ev.target !== this) {
                this.debugEdition = false;
            }
        },
        /**
         * Sets the model the field must work with and whether or not the current
         * domain value is valid for this particular model. This is inferred from
         * the received special data.
         *
         * @private
         */
        _setState: function () {
            let domainModel = this.nodeOptions.model;
            if (Object.prototype.hasOwnProperty.call(this.record.data, domainModel)) {
                domainModel = this.record.data[domainModel];
            }
            this._domainModel = domainModel;
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * Recompute the number of records matching the domain when the user clicks
         * on the refresh button. Useful after manually editing the domain through
         * the textarea in debug mode, as in this case, the count isn't automatically
         * recomputed.
         *
         * @param {MouseEvent} ev
         */
        async _onRefreshCountClick(ev) {
            ev.stopPropagation();
            ev.currentTarget.setAttribute("disabled", "disabled");
            await this._fetchCount(true);
            this._replaceContent();
        },
        /**
         * Called when the "Show selection" button is clicked
         * -> Open a modal to see the matched records
         *
         * @param {Event} e
         */
        _onShowSelectionButtonClick: function (e) {
            e.preventDefault();
            new view_dialogs.SelectCreateDialog(this, {
                title: _t("Selected records"),
                res_model: this._domainModel,
                context: this.record.getContext({fieldName: this.name, viewType: this.viewType}),
                domain: this.value || "[]",
                no_create: true,
                readonly: true,
                disable_multiple_selection: true,
            }).open();
        },
        /**
         * Called when the "Edit domain" button is clicked (when using the in_dialog
         * option) -> Open a DomainSelectorDialog to edit the value
         *
         * @param {Event} e
         */
        _onDialogEditButtonClick: function (e) {
            e.preventDefault();
            new DomainSelectorDialog(this, this._domainModel, this.value || "[]", {
                readonly: this.mode === "readonly",
                filters: this.fsFilters,
                debugMode: config.isDebug(),
            }).open();
        },
        /**
         * Called when the domain selector value is changed
         * -> Adapt the internal value state
         *
         * @param {OdooEvent} e
         * @param {Domain} e.data.domain
         */
        _onDomainSelectorValueChange: function (e) {
            // we don't want to recompute the count if the domain has been edited
            // from the debug textarea (for performance reasons, as it might be costly)
            this.debugEdition = !!e.data.debug;
            this._setValue(e.data.domain);
        },
        /**
         * Called when the in-dialog domain selector value is confirmed
         * -> Adapt the internal value state
         *
         * @param {OdooEvent} e
         */
        _onDomainSelectorDialogValueChange: function (e) {
            this._setValue(Domain.prototype.arrayToString(e.data.domain));
        },
        /**
         * Stops the propagation of the 'open_record' event, as we don't want the
         * user to be able to open records from the list opened in a dialog.
         *
         * @param {OdooEvent} event
         */
        _onOpenRecord: function (event) {
            event.stopPropagation();
        },
        /**
         * Stops the enter navigation in a DomainSelector's textarea.
         *
         * @private
         * @param {OdooEvent} ev
         */
         _onKeydown: function (ev) {
            if (ev.which === $.ui.keyCode.ENTER && ev.target.tagName === "TEXTAREA") {
                ev.stopPropagation();
                return;
            }
            this._super.apply(this, arguments);
        },
    });
    
    return {
        TerabitsFieldDomain: TerabitsFieldDomain,
    };
    
    });
    