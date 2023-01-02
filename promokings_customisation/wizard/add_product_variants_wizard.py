# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AddProductVariantsWizard(models.TransientModel):
    _name = 'add.product.variants.wizard'
    _description = 'Add Product Variants'

    sale_order_id = fields.Many2one('sale.order', readonly=True, string="Sale Order")
    product_template_ids = fields.Many2many('product.template', 'product_tmpl_add_variant_wizard_rel',
                                            'add_variant_wizard_id', 'product_template_id', readonly=True,
                                            string="Parent Product(s)")
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True)
    customise = fields.Selection([
        ('required', 'Required'),
        ('not_required', 'Not Required')], string="Customisation", readonly=True)
    customisation_details = fields.Char(string="Customisation Details", readonly=True)
    line_ids = fields.One2many('add.product.variants.wizard.line', 'wizard_id', string="Product Variants Line",
                               required=True)

    def add_product_variants_to_order_line(self):
        order_lines = []
        if self.line_ids and self.product_template_ids:
            quantity = 0
            if set(self.product_template_ids.ids) == set(self.line_ids.mapped('product_id').product_tmpl_id.ids):
                for line in self.line_ids:
                    quantity += line.product_uom_qty
                    order_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom': line.product_uom_id.id,
                        'price_unit': line.price_unit,
                        'customise': self.customise,
                        'customisation_details': self.customisation_details,
                    }))
            else:
                raise ValidationError(_("Variants are not added for all products"))

            if quantity > self.product_uom_qty:
                raise ValidationError(
                    _("Quantity (%s) entered for variants and quantity (%s) of parent product is not equal") % (
                        quantity, self.product_uom_qty))
        else:
            raise ValidationError(_("Please add product variants"))

        if self.sale_order_id and order_lines:
            self.sale_order_id.order_line.unlink()
            self.sale_order_id.order_line = order_lines
            self.sale_order_id.product_variants_added = True


class AddProductVariantsWizardLine(models.TransientModel):
    _name = 'add.product.variants.wizard.line'
    _description = 'Add Product Variants Line'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    price_unit = fields.Float(string='Price Unit', required=True)
    wizard_id = fields.Many2one('add.product.variants.wizard')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            if self.product_id.product_tmpl_id:
                so_line_id = self.wizard_id.sale_order_id.order_line.filtered(
                    lambda line: line.product_template_id == self.product_id.product_tmpl_id)
                if so_line_id:
                    self.price_unit = so_line_id.price_unit
        product_list = []
        if self.wizard_id.product_template_ids:
            for product_tmpl in self.wizard_id.product_template_ids:
                for product in product_tmpl.product_variant_ids:
                    if product._origin.id not in product_list:
                        product_list.append(product._origin.id)
        domain = {'domain': {'product_id': [('id', 'in', product_list)]}}
        return domain
