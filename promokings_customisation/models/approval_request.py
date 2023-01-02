# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    sale_order = fields.Many2one('sale.order', string="Sale order")
    mrp_order = fields.Many2one('mrp.production', string="Manufacturing order")

    @api.onchange('sale_order')
    def _onchange_sale_order(self):
        """Onchange function for adding sale order line in approval product line"""
        if self.sale_order:
            product_lines = [(5, 0, 0)]
            for lines in self.sale_order.order_line:
                order_lines = (0, 0, {
                    'product_id': lines.product_id.id,
                    'description': lines.name,
                    'quantity': lines.product_uom_qty,
                    'product_uom_id': lines.product_uom.id
                })
                product_lines.append(order_lines)
            self.product_line_ids = product_lines

    @api.onchange('mrp_order')
    def _onchange_mrp_order(self):
        """Onchange function for adding Manufacturing order line in approval product line"""
        if self.mrp_order:
            product_lines = [(5, 0, 0)]
            for lines in self.mrp_order.move_raw_ids:
                order_lines = (0, 0, {
                    'product_id': lines.product_id.id,
                    'description': lines.product_id.display_name,
                    'quantity': lines.product_uom_qty,
                    'product_uom_id': lines.product_uom.id
                })
                product_lines.append(order_lines)
            self.product_line_ids = product_lines
