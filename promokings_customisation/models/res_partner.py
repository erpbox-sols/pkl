# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _check_is_contact_admin(self):
        """For checking user right for Sale admin"""
        user_ids = self.env['res.users'].search([])
        sale_admin_ids = user_ids.filtered(lambda l: l.has_group('base.group_partner_manager')).ids
        self.is_contact_admin = True if self.env.user.id in sale_admin_ids else False

    vendor_code = fields.Char('Vendor Code')
    is_contact_admin = fields.Boolean(compute=_check_is_contact_admin, readonly=True)
    ext_partner_id = fields.Integer("Ext ID")

    @api.model
    def default_get(self, fields):
        if self:
            if not self.is_contact_admin:
                raise UserError(_("You are not allow to create Contacts. Please contact Administrator"))
        return super(ResPartner, self).default_get(fields)

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)
        if self:
            if not self.is_contact_admin:
                raise UserError(_("You are not allow to create Contacts. Please contact Administrator"))
        return record

