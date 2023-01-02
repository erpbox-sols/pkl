# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MultipleSOCreationWizard(models.TransientModel):
    _name = 'multiple.so.creation.wizard'
    _description = 'Multiple Sale Order Creation Wizard'

    sale_order_id = fields.Many2one('sale.order', readonly=True, string="Sale Order")
    so_line_ids = fields.One2many('multiple.so.creation.wizard.line', 'wizard_id', string="SO Creation Wizard Line",
                                  required=True)

    @api.onchange('so_line_ids')
    def onchange_so_line_ids(self):
        if self.so_line_ids:
            data = {}
            for line in self.so_line_ids:
                if line.product_id.product_tmpl_id not in data:
                    data[line.product_id.product_tmpl_id] = [line.qty_to_do]
                else:
                    data[line.product_id.product_tmpl_id].append(line.qty_to_do)

                for product_tmpl, qty_to_do in data.items():
                    if product_tmpl == line.product_id.product_tmpl_id:
                        so_line_id = self.sale_order_id.order_line.filtered(
                            lambda l: l.product_template_id.id == product_tmpl.id)
                        if so_line_id and sum(so_line_id.mapped('qty_remaining')):
                            line.qty_remaining = sum(so_line_id.mapped('qty_remaining')) - sum(qty_to_do)
                        else:
                            line.qty_remaining = sum(so_line_id.mapped('product_uom_qty')) - sum(qty_to_do)

    def create_so_next_action_plan(self):
        if self.sale_order_id and self.so_line_ids:
            so_naming_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R',
                              'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

            order_id = False
            order_lines = []
            next_action_lines = []
            for so_line in self.so_line_ids:
                if so_line.qty_to_do <= 0:
                    raise ValidationError(_("Quantity must be positive"))
                so_line_id = self.sale_order_id.order_line.filtered(
                    lambda l: l.product_template_id.id == so_line.product_id.product_tmpl_id.id)
                if so_line_id:
                    qty_to_check_lines = self.so_line_ids.filtered(
                        lambda x: x.product_id.product_tmpl_id == so_line_id.product_template_id)
                    if qty_to_check_lines:
                        total_qty = sum(qty_to_check_lines.mapped('qty_to_do'))
                        if total_qty > sum(so_line_id.mapped('product_uom_qty')):
                            raise ValidationError(
                                _("Quantity (%s) entered and quantity (%s) of parent product is not equal") % (
                                    total_qty, sum(so_line_id.mapped('product_uom_qty'))))

                order_lines.append((0, 0, {
                    'product_id': so_line.product_id.id,
                    'product_uom_qty': so_line.qty_to_do,
                    'product_uom': so_line.product_uom_id.id,
                    'price_unit': so_line.price_unit,
                    'customise': so_line.customise,
                    'customisation_details': so_line.customisation_details,
                    'customisation_type_ids': so_line.customisation_type_ids,
                    'art_work_image': so_line.art_work_image,
                    'delivery_date': so_line.delivery_date
                }))
                next_action_lines.append((0, 0, {
                    'product_id': so_line.product_id.id,
                    'qty_ordered': so_line.qty_ordered,
                    'qty_to_do': so_line.qty_to_do,
                    'product_uom_id': so_line.product_uom_id.id,
                    'price_unit': so_line.price_unit,
                    'customise': so_line.customise,
                    'customisation_details': so_line.customisation_details,
                    'customisation_type_ids': so_line.customisation_type_ids,
                    'art_work_image': so_line.art_work_image
                }))

            sequence_letter = 'A'
            if self.sale_order_id.child_ids:
                sequence_letter = so_naming_list[len(self.sale_order_id.child_ids)]

            if order_lines:
                order_id = self.env['sale.order'].sudo().create({
                    'name': self.sale_order_id.name + ' - ' + sequence_letter,
                    'partner_id': self.sale_order_id.partner_id.id,
                    'pricelist_id': self.sale_order_id.pricelist_id.id,
                    'parent_so_id': self.sale_order_id.id,
                    'client_order_ref': self.sale_order_id.client_order_ref,
                    'estimated_po': self.sale_order_id.estimated_po,
                    'commitment_date': self.sale_order_id.commitment_date,
                    'order_line': order_lines
                })
                order_id.button_quotation_confirm()
                order_id.action_confirm()
                order_id.state = 'quotation_confirmed'

            if order_id:
                next_action_id = self.env['so.next.action'].sudo().create({
                    'sale_order_id': order_id.id,
                    'next_action_line_ids': next_action_lines,
                })
                order_id.sudo().write({'next_action_ids': [(4, next_action_id.id)]})
                self.sale_order_id.sudo().write({'child_ids': [(4, order_id.id)]})

            for line in self.sale_order_id.order_line:
                total_product_uom_qty = self.sale_order_id.child_ids.order_line.filtered(
                    lambda x: x.product_id.product_tmpl_id == line.product_template_id).mapped('product_uom_qty')
                line.qty_remaining = line.product_uom_qty - sum(total_product_uom_qty)

            if sum(self.sale_order_id.order_line.mapped('qty_remaining')) == 0:
                self.sale_order_id.action_confirm()
        else:
            raise ValidationError(_("Please select products"))


class MultipleSOCreationWizardLine(models.TransientModel):
    _name = 'multiple.so.creation.wizard.line'
    _description = 'Multiple Sale Order Creation Wizard Line'

    product_id = fields.Many2one('product.product', string="Product")
    qty_ordered = fields.Float(string='Quantity Ordered', digits='Product Unit of Measure')
    qty_to_do = fields.Float(string='Quantity To Do', digits='Product Unit of Measure')
    qty_remaining = fields.Float(string='Quantity Remaining', digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    delivery_date = fields.Date(
        'Delivery Date', default=fields.Date.context_today, copy=False)

    price_unit = fields.Float(string='Price Unit')
    customise = fields.Selection([
        ('required', 'Required'),
        ('not_required', 'Not Required')], string="Customisation")
    customisation_details = fields.Char(string="Customisation Details")
    customisation_type_ids = fields.Many2many('customisation.type', 'so_create_wizard_rel', 'wizard_line_id',
                                              'cust_type_id', 'Customisation Type')
    art_work_image = fields.Binary(string="Art Work")
    wizard_id = fields.Many2one('multiple.so.creation.wizard', 'Multiple Sale Order Creation Wizard')
    sale_line_id = fields.Many2one('sale.order.line', string="SO line")
    sale_line_count = fields.Boolean('Sale line count')

    @api.onchange('sale_line_id')
    def onchange_sale_line_id(self):
        if self.product_id and self.sale_line_id:
            so_line_id = self.wizard_id.sale_order_id.order_line.filtered(
                lambda l: l.product_template_id.id == self.product_id.product_tmpl_id.id and l.id == self.sale_line_id.id)
            if so_line_id:
                self.qty_ordered = so_line_id.product_uom_qty or 0
                self.product_uom_id = so_line_id.product_uom.id
                self.price_unit = so_line_id.price_unit
                self.customise = so_line_id.customise
                self.customisation_details = so_line_id.customisation_details
                self.customisation_type_ids = so_line_id.customisation_type_ids.ids if so_line_id.customisation_type_ids else False
                self.art_work_image = so_line_id.art_work_image

    @api.onchange('product_id')
    def onchange_products_id(self):
        if self.product_id:
            so_line_ids = self.wizard_id.sale_order_id.order_line.filtered(
                lambda l: l.product_template_id.id == self.product_id.product_tmpl_id.id)
            if len(so_line_ids) > 1:
                self.sale_line_count = True
            else:
                self.sale_line_count = False
            domain = {'domain': {'sale_line_id': [('id', 'in', so_line_ids.ids)]}}
            return domain

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            so_line_id = self.wizard_id.sale_order_id.order_line.filtered(
                lambda l: l.product_template_id.id == self.product_id.product_tmpl_id.id)
            if so_line_id and len(so_line_id) == 1:
                # for so_line_id in so_line_ids:
                # self.qty_ordered = sum(so_line_id.mapped('product_uom_qty')) or 0
                self.qty_ordered = so_line_id.product_uom_qty or 0
                self.product_uom_id = so_line_id.product_uom.id
                self.price_unit = so_line_id.price_unit
                self.customise = so_line_id.customise
                self.customisation_details = so_line_id.customisation_details
                self.customisation_type_ids = so_line_id.customisation_type_ids.ids if so_line_id.customisation_type_ids else False
                self.art_work_image = so_line_id.art_work_image

        product_list = []
        if self.wizard_id.sale_order_id:
            for line in self.wizard_id.sale_order_id.order_line:
                if line.product_template_id and line.product_template_id.product_variant_ids:
                    for product in line.product_template_id.product_variant_ids:
                        product_list.append(product.id)

        domain = {'domain': {'product_id': [('id', 'in', product_list)]}}
        return domain

