# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMoveInherit(models.Model):
    _inherit = 'account.move'

    @api.model
    def default_get(self, fields):
        vals = super(AccountMoveInherit, self).default_get(fields)
        terms_condition = self.env['ir.config_parameter'].sudo().get_param('promokings_customisation.invoice_terms_condition')
        is_terms_condition = self.env['ir.config_parameter'].sudo().get_param('promokings_customisation.is_invoice_terms_condition')
        for record in self:
            if vals.get('move_type') == 'out_invoice' and is_terms_condition:
                vals['narration'] = terms_condition
            elif record.move_type == 'out_invoice':
                record.narration = terms_condition
        return vals

    def get_picking_name(self):
        picking = ''
        for rec in self.picking_ids:
            picking += rec.name
        return picking
