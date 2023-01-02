# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class ActitivyAlarm(models.Model):
    _name = "sh.activity.alarm"
    _description = "Alarm Reminder"

    name = fields.Char(string="Name", readonly=True)
    type = fields.Selection([('email', 'Email'), ('popup', 'Popup')],
                            string="Type",
                            required=True,
                            default='email')
    sh_remind_before = fields.Integer(string="Reminder Before")
    sh_reminder_unit = fields.Selection([('Hour(s)', 'Hour(s)'),
                                         ('Minute(s)', 'Minute(s)'),
                                         ('Second(s)', 'Second(s)')],
                                        string="Reminder Unit",
                                        default='Hour(s)',
                                        required=True)
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 default=lambda self: self.env.company)

    @api.constrains('sh_remind_before')
    def _check_sh_currency_rate(self):
        if self.filtered(lambda c: c.sh_reminder_unit == 'Minute(s)' and c.
                         sh_remind_before < 5):
            raise ValidationError(
                _("Reminder Before can't set less than 5 Minutes."))
        elif self.filtered(lambda c: c.sh_reminder_unit == 'Second(s)' and c.
                           sh_remind_before < 300):
            raise ValidationError(
                _("Reminder Before can't set less than 300 Seconds."))
        elif self.filtered(lambda c: c.sh_reminder_unit == 'Hour(s)' and c.
                           sh_remind_before < 1):
            raise ValidationError(
                _("Reminder Before can't set less than 1 Hour."))

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(
            ['sh_remind_before', 'sh_reminder_unit', 'type'])
        return [
            (alarm.id, '%s%s%s' %
             (str(alarm.sh_remind_before) + ' ',
              str(alarm.sh_reminder_unit) + ' ', '[' + str(alarm.type) + ']'))
            for alarm in self
        ]

    @api.onchange('sh_remind_before', 'type', 'sh_reminder_unit')
    def _onchange_name(self):
        for rec in self:
            rec.name = rec.name_get()[0][1]

    @api.model
    def _run_activity_reminder(self):
        # dic= {
        #                                     'title': _('Private Event Excluded'),
        #                                     'message': _('Grouping by is not allowed on private events.')
        #                                 }
        # res = self.env['bus.bus']._sendone(self.env.user.partner_id, 'mail.simple_notification', dic)
        # print("\n\n res",res)
        if self.env.company.sh_display_activity_reminder:
            alarm_ids = self.env['sh.activity.alarm'].sudo().search([])
            if alarm_ids:
                for alarm in alarm_ids:
                    activity_ids = self.env['mail.activity'].sudo().search([
                        ('sh_activity_alarm_ids', 'in', [alarm.id])
                    ])
                    if activity_ids:
                        for activity in activity_ids:
                            deadline_date = False
                            if alarm.sh_reminder_unit == 'Hour(s)' and activity.sh_date_deadline:
                                deadline_date_hours_added = activity.sh_date_deadline + timedelta(
                                    hours=5, minutes=30, seconds=0)
                                deadline_date = deadline_date_hours_added - timedelta(
                                    hours=alarm.sh_remind_before)
                            elif alarm.sh_reminder_unit == 'Minute(s)' and activity.sh_date_deadline:
                                deadline_date_minutes_added = activity.sh_date_deadline + timedelta(
                                    hours=5, minutes=30, seconds=0)
                                deadline_date = deadline_date_minutes_added - timedelta(
                                    minutes=alarm.sh_remind_before)
                            elif alarm.sh_reminder_unit == 'Second(s)' and activity.sh_date_deadline:
                                deadline_date_seconds_added = activity.sh_date_deadline + timedelta(
                                    hours=5, minutes=30, seconds=0)
                                deadline_date = deadline_date_seconds_added - timedelta(
                                    seconds=alarm.sh_remind_before)
                            if deadline_date and deadline_date != False:
                                if alarm.type == 'popup':
                                    now = fields.Datetime.now() + timedelta(
                                        hours=5, minutes=30, seconds=0)
                                    if fields.Date.today(
                                    ) == deadline_date.date(
                                    ) and deadline_date.hour == now.hour and deadline_date.minute == now.minute:
                                        notifications = []
                                        message = str(
                                            self.env['ir.config_parameter'].
                                            sudo().get_param('web.base.url')
                                        ) + '/web#id=' + str(
                                            activity.res_id) + '&model=' + str(
                                                activity.res_model)
                                        if activity.user_id:
                                            notifications.append([
                                                (self._cr.dbname,
                                                 'res.partner',
                                                 activity.user_id.partner_id.id
                                                 ),
                                                {
                                                    'type':
                                                    'sh_activity_reminder_simple_notification',
                                                    'title':
                                                    _('Activity Reminder ' +
                                                      '(' +
                                                      str(activity.
                                                          activity_type_id.name
                                                          ) + ')'),
                                                    'message':
                                                    message,
                                                    'sticky':
                                                    True,
                                                    'warning':
                                                    False
                                                }  # sorted to make deterministic for tests
                                            ])
                                        self.env['bus.bus']._sendone(
                                            activity.user_id.partner_id,
                                            'sh_activity_reminder_simple_notification',
                                            {
                                                'title':
                                                _('Activity Reminder ' + '(' +
                                                  str(activity.activity_type_id
                                                      .name) + ')'),
                                                'message':
                                                message,
                                            })

                                elif alarm.type == 'email':
                                    now = fields.Datetime.now() + timedelta(
                                        hours=5, minutes=30, seconds=0)
                                    if fields.Date.today(
                                    ) == deadline_date.date(
                                    ) and deadline_date.hour == now.hour and deadline_date.minute == now.minute:
                                        reminder_template = self.env.ref(
                                            'sh_activity_reminder.sh_activity_reminder_mail_template'
                                        )
                                        if reminder_template:
                                            reminder_template.sudo().write({
                                                'partner_to':
                                                str(activity.user_id.
                                                    partner_id.id)
                                            })
                                            reminder_template.sudo().send_mail(
                                                activity.id,
                                                force_send=True,
                                                notif_layout=
                                                'mail.mail_notification_light')
