# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CustomisationType(models.Model):
    _name = "customisation.type"
    _description = "Customisation Type"

    name = fields.Char(string="Name")
