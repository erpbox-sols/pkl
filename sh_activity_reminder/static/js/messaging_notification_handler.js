odoo.define('sh_activity_reminder.notification_manager', function (require) {
    'use strict';

    var AbstractService = require('web.AbstractService');
    var core = require("web.core");


    var sh_activity_reminder_notification_manager = AbstractService.extend({
        dependencies: ['bus_service'],
        // dependencies: ["notification"],

        /**
         * @override
         */

        start: function () {
            this._super.apply(this, arguments);
            this.call('bus_service', 'onNotification', this, this._onNotification);
        },

        _onNotification: function (notifications) {

            var save = function () {
                // window.location.replace("https://www.google.com");
                window.open("https://www.google.com", "_blank");
            };

            for (const { payload, type } of notifications) {
                if (type === "sh_activity_reminder_simple_notification") {
                    console.log('massage', payload.message)
                    this.displayNotification({
                        title: payload.title, type: 'warning', sticky: true, buttons: [{
                            text: 'Activity',
                            classes: 'btn btn-primary',
                            primary: true,
                            click:
                                function () {
                                    window.open(payload.message, "_blank");
                                },
                        },
                        ]
                    });
                }
            }
        }


    });
    core.serviceRegistry.add('sh_activity_reminder_notification_manager', sh_activity_reminder_notification_manager);
    return sh_activity_reminder_notification_manager;
});
