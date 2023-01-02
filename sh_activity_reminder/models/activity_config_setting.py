# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    sh_display_activity_reminder = fields.Boolean('Activity Reminder ?',default=True)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sh_display_activity_reminder = fields.Boolean('Activity Reminder ?',related='company_id.sh_display_activity_reminder',readonly=False)