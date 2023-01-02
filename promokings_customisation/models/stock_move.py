# -*- coding: utf-8 -*-


from odoo import api, fields, models, _


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    art_work_image = fields.Binary(string="Art Work")

    @api.onchange('product_id')
    def onchange_product_id(self):
        product_category = self.env['product.category']
        if self.raw_material_production_id:
            if self.raw_material_production_id.branding_mo:
                ready_product_list = []
                ready_goods_categ = product_category.sudo().search([('name', 'in', ['Ready Goods', 'Raw Materials'])])
                for ready_product in self.env['product.product'].sudo().search(
                        ['|', ('categ_id', 'in', ready_goods_categ.child_id.ids),
                         ('categ_id', 'in', ready_goods_categ.ids)]):
                    ready_product_list.append(ready_product.id)
                domain = {'domain': {'product_id': [('id', 'in', ready_product_list)]}}
                return domain

            raw_product_list = []
            raw_materials_categ = product_category.sudo().search([('name', '=', 'Raw Materials')])
            for raw_product in self.env['product.product'].sudo().search(
                    ['|', ('categ_id', 'in', raw_materials_categ.child_id.ids),
                     ('categ_id', 'in', raw_materials_categ.ids)]):
                raw_product_list.append(raw_product.id)
            domain = {'domain': {'product_id': [('id', 'in', raw_product_list)]}}
            return domain

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    art_work_image = fields.Binary(string="Art Work")

