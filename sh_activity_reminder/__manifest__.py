# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name": "Activity Reminder",
    "author": "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "version": "15.0.2",
    "category": "Discuss",
    "summary": "Activities Daily Reminder,Mail Activity Reminder Notification,Popup Activity Reminder,Pop Up Activity Reminder,Activities Reminder,Schedule Activity And Notification,Activity Daily Reminder,Daily Activities Management,Due Date Reminder Odoo",
    "description": """This module allows to set an activity alarm that reminds of to-do various activities. You can set and send gentle reminders to perform activities so no need to remember daily tasks. You can send activity reminders at a particular date and time by email as well as popup. Activity reminders can be sent by schedule actions.""",
    "depends": [
        'base_setup',
        'mail'
    ],
    "data": [
        'security/activity_security.xml',
        'security/ir.model.access.csv',
        'views/activity_alarm.xml',
        'views/activity_config_setting.xml',
        'views/activity_views.xml',
        'data/activity_reminder_cron.xml',
        'data/activity_reminder_mail_template.xml',
    ],
        'assets': {
        'web.assets_backend': [
            'sh_activity_reminder/static/js/messaging_notification_handler.js',
        ],
    },
    "images": ["static/description/background.png", ],
    "license": "OPL-1",
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 30,
    "currency": "EUR"
}
