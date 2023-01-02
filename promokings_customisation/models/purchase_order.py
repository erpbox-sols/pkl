# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    so_origin = fields.Many2one('sale.order', string='Source Document (SO)')

    @api.model
    def default_get(self, fields):
        vals = super(PurchaseOrderInherit, self).default_get(fields)
        terms_condition = self.env['ir.config_parameter'].sudo().get_param('promokings_customisation.purchase_terms_condition')
        is_terms_condition = self.env['ir.config_parameter'].sudo().get_param('promokings_customisation.is_purchase_terms_condition')
        if is_terms_condition:
            vals['notes'] = terms_condition
        return vals

    @api.onchange('so_origin')
    def onchange_so_origin(self):
        """ Adding value to origin field, when value changing from the so_origin"""
        for record in self:
            if record.so_origin:
                record.update({
                    'origin': record.so_origin.name
                })
