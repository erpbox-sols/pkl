# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api
from datetime import timedelta


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    sh_activity_alarm_ids = fields.Many2many('sh.activity.alarm',string = 'Reminders')
    sh_date_deadline = fields.Datetime('Reminder Due Date', default=lambda self: fields.Datetime.now())

    @api.onchange('date_deadline')
    def _onchange_sh_date_deadline(self):
        if self:
            for rec in self:
                if rec.date_deadline:
                    rec.sh_date_deadline = rec.date_deadline + timedelta(hours=0, minutes=0, seconds=0)
