# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class SONextAction(models.Model):
    _name = "so.next.action"
    _description = "Sale Order Next Action Plans"
    _order = 'id desc'

    name = fields.Char('Name', copy=False, readonly=True, default=lambda x: _('New'))
    sale_order_id = fields.Many2one('sale.order', readonly=True, string="Sale Order")
    next_action_line_ids = fields.One2many('so.next.action.line', 'so_next_action_id', string="SO Next Action Line",
                                           states={'so_created': [('readonly', True)]})
    state = fields.Selection([('draft', 'Draft'), ('partially_created', 'Partially Created'), ('so_created', 'SO Created')], default='draft', readonly=True,
                             string='State')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('next.action.plan') or _('New')
        return super(SONextAction, self).create(vals)

    def write(self, vals):
        res = super(SONextAction, self).write(vals)
        for line in self.next_action_line_ids:
            sale_order_line_id = self.sale_order_id.order_line.filtered(lambda l: l.product_id.id == line.product_id.id)
            next_action_line_id = self.next_action_line_ids.filtered(
                lambda l: l.product_id.id == line.product_id.id)
            if next_action_line_id:
                sum_of_next_action_line_qty = sum(next_action_line_id.mapped('qty_to_next_action'))
                sum_of_so_line_qty = sum(sale_order_line_id.mapped('product_uom_qty'))
                if sum_of_next_action_line_qty > sum_of_so_line_qty:
                    raise ValidationError(
                        _("Quantity to next action (%s) should not be greater than quantity to do (%s) for %s") % (
                            sum_of_next_action_line_qty, sum_of_so_line_qty, line.product_id.display_name))
        return res

    @api.onchange('next_action_line_ids')
    def onchange_next_action_line_ids(self):
        if self.next_action_line_ids:
            data = {}
            for line in self.next_action_line_ids:
                sale_order_line_id = self.sale_order_id.order_line.filtered(lambda l: l.product_id.id == line.product_id.id)
                if line.product_id not in data:
                    data[line.product_id] = [line.qty_to_next_action]
                else:
                    data[line.product_id].append(line.qty_to_next_action)

                for product, qty_to_next_action in data.items():
                    if product == line.product_id:
                        next_action_line_id = self.next_action_line_ids.filtered(
                            lambda l: l.product_id.id == product.id)
                        if next_action_line_id[0].qty_to_do:
                            # line.qty_remaining = next_action_line_id[0].qty_to_do - sum(qty_to_next_action)
                            line.qty_remaining = sum(sale_order_line_id.mapped('product_uom_qty')) - sum(qty_to_next_action)

    def confirm_sale_order(self):
        if self.sale_order_id and self.next_action_line_ids:
            # create picking if next action is false and customize is not required
            normal_line_ids = self.next_action_line_ids.filtered(
                lambda x: not x.next_action and x.customise == 'not_required' and not x.next_action_done)
            filter_normal_line_ids = normal_line_ids.filtered(lambda x: x.qty_to_next_action > 0)
            if filter_normal_line_ids:
                ready_goods_location = self.env['stock.location'].search(
                    [('name', 'ilike', 'Ready Goods Store'), ('usage', '=', 'internal'), ('company_id', '=', self.env.company.id)], limit=1)
                ready_good_location = self.env['stock.location'].search(
                    [('name', 'ilike', 'Ready Goods Stock'), ('usage', '=', 'internal'), ('company_id', '=', self.env.company.id)], limit=1)
                lines = [(5, 0, 0)]
                for filter_normal_line_id in filter_normal_line_ids:
                    line = (0, 0, {
                        'name': '/',
                        'product_id': filter_normal_line_id.product_id.id,
                        'product_uom': filter_normal_line_id.product_id.uom_id.id,
                        'product_uom_qty': filter_normal_line_id.qty_to_next_action,
                        'location_id': ready_goods_location.id or ready_good_location.id,
                        'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    })
                    lines.append(line)

                pick_output = self.env['stock.picking'].create({
                    'name': '/',
                    'partner_id': self.sale_order_id.partner_id.id or False,
                    'scheduled_date': datetime.now(),
                    'sale_id': self.sale_order_id.id,
                    'picking_type_id': self.env.ref('stock.picking_type_out').id,
                    'location_id': ready_goods_location.id or ready_good_location.id,
                    'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                    'origin': self.sale_order_id.name,
                    'move_lines': lines,
                })
                pick_output.action_confirm()
                filter_normal_line_ids.picking_id = pick_output.id
                filter_normal_line_ids.next_action_done = True
            # End create picking if next action is false and customize is not required

            attachment_obj = self.env['ir.attachment'].sudo()
            # Code for generate PO Start
            buy_line_ids = self.next_action_line_ids.filtered(
                lambda x: x.next_action == 'buy' and not x.next_action_done)
            partner_ids = buy_line_ids.mapped('partner_id')
            for partner in partner_ids:
                filter_buy_line_ids = buy_line_ids.filtered(lambda x: x.partner_id.id == partner.id and x.qty_to_do > 0)
                po_attachment_ids = []
                if filter_buy_line_ids:
                    line_vals = []
                    vals = {
                        'partner_id': partner.id,
                        'date_planned': datetime.now(),
                        'so_origin': self.sale_order_id.id,
                        'origin': self.sale_order_id.name,
                    }
                    for po_line in filter_buy_line_ids:
                        # product_to_link_in_po = self.env['product.product'].sudo().search(
                        #     [('po_link_product_id', '=', po_line.product_id.id), ('vendor_id', '=', partner.id)])
                        product_to_link_in_po = self.env['product.product'].sudo().search(
                            [('po_link_product_id', '=', po_line.product_id.id)])
                        if not product_to_link_in_po:
                            raise ValidationError(_("Please Check the product is exist on po linked product."))
                        so_line_to_link_in_po = self.sale_order_id.order_line.filtered(
                            lambda l: l.product_id.id == po_line.product_id.id)
                        po_attachment_id = attachment_obj.create({
                            'name': po_line.product_id.name,
                            'res_model': po_line._name,
                            'res_id': po_line.id,
                            'datas': po_line.art_work_image,
                            'mimetype': 'image/gif',
                        })
                        po_attachment_ids.append(po_attachment_id.id)
                        if po_line.qty_to_next_action > 0:
                            line_vals.append((0, 0, {
                                'product_id': po_line.linked_product_id.id or product_to_link_in_po[0].id,
                                'name': po_line.linked_product_id.name or product_to_link_in_po[0].name,
                                'product_qty': po_line.qty_to_next_action,
                                'price_unit': 0,
                                'product_uom': po_line.linked_product_id.uom_po_id.id or product_to_link_in_po[0].uom_po_id.id,
                                'date_planned': datetime.now(),
                                'sale_line_id': so_line_to_link_in_po[0].id if so_line_to_link_in_po else False
                            }))
                        if not po_line.customise == 'required':
                            po_line.next_action_done = True
                    vals.update({'order_line': line_vals})
                    purchase_order = self.env['purchase.order'].create(vals)
                    purchase_order.message_post(body='Art Work', attachment_ids=po_attachment_ids)
                    filter_buy_line_ids.purchase_order_id = purchase_order.id
            # Code for generate PO End

            # Code for generate MO Start
            mrp_picking_type_id = self.env['stock.picking.type'].search(
                [('code', '=', 'mrp_operation'), ('warehouse_id.company_id', '=', self.env.company.id)], limit=1)
            post_production_location_id = self.env['stock.location'].search([('name', '=', 'Post-Production'),
                                                             ('company_id', '=', self.env.company.id)], limit=1)

            ready_goods_location = self.env['stock.location'].search([('name', 'ilike', 'Ready Goods Stock'), ('usage', '=', 'internal'), ('company_id', '=', self.env.company.id)], limit=1)

            manufacture_line_ids = self.next_action_line_ids.filtered(
                lambda x: x.next_action == 'manufacture' and not x.next_action_done)
            for mo_line in manufacture_line_ids:
                if mo_line.qty_to_do > 0:
                    product_to_link_in_mo = self.env['product.product'].sudo().search(
                        [('mo_link_product_id', '=', mo_line.product_id.id)], limit=1)
                    mo_attachment_id = attachment_obj.create({
                        'name': mo_line.product_id.name,
                        'res_model': mo_line._name,
                        'res_id': mo_line.id,
                        'datas': mo_line.art_work_image,
                        'mimetype': 'image/gif',
                    })
                    production_id = self.env['mrp.production'].create({
                        'product_id': mo_line.linked_product_id.id or mo_line.product_id.id,
                        'product_qty': mo_line.qty_to_next_action,
                        'product_uom_id': mo_line.product_id.uom_id and mo_line.product_id.uom_id.id or False,
                        'bom_id': mo_line.product_id.bom_ids[0].id if mo_line.product_id.bom_ids else False,
                        'origin': self.sale_order_id.name,
                        'partner_id': self.sale_order_id.partner_id.id,
                        'sale_order_id': self.sale_order_id.id,
                        'customisation_details': mo_line.customisation_details,
                        'picking_type_id': mrp_picking_type_id.id,
                        'location_src_id': mrp_picking_type_id.default_location_src_id.id,
                        'location_dest_id': mrp_picking_type_id.default_location_dest_id.id,
                        # 'location_dest_id': ready_goods_location.id or mrp_picking_type_id.default_location_dest_id.id,
                    })
                    production_id._onchange_bom_id()
                    production_id.product_qty = mo_line.qty_to_next_action
                    production_id._onchange_move_raw()
                    pro = production_id._onchange_move_finished_product()
                    if not pro:
                        production_id.update({
                            'move_finished_ids': [(5, 0, 0), (0, 0, {
                                'product_id': mo_line.linked_product_id.id or mo_line.product_id.id,
                                'name': mo_line.linked_product_id.display_name or mo_line.product_id.display_name,
                                'location_id': post_production_location_id.id,
                                'product_uom_qty': 1,
                                'product_uom': mo_line.linked_product_id.uom_id.id or mo_line.product_id.uom_id.id,
                                'location_dest_id': ready_goods_location.id
                            })]
                        })
                    production_id.message_post(body='Art Work', attachment_ids=mo_attachment_id.ids)
                    mo_line.update({
                        'mrp_id': [(4, production_id.id)]
                    })
                    if not mo_line.customise == 'required':
                        mo_line.next_action_done = True
            # Code for generate MO Stop

            # Code for creating MO If the Customisation is Required
            for cust_mo_line in self.next_action_line_ids:
                if not cust_mo_line.next_action_done:
                    if cust_mo_line.customise == 'required' and cust_mo_line.qty_to_next_action > 0:
                        component_lines = [(5, 0, 0)]
                        location_id = self.env['stock.location'].search([('name', '=', 'Pre-Production'),
                                                                         ('company_id', '=', self.env.company.id)], limit=1)
                        location_dest = self.env['stock.location'].search([('usage', '=', 'production'),
                                                                           ('company_id', '=', self.env.company.id)], limit=1)
                        if cust_mo_line.purchase_order_id:
                            product_ids = cust_mo_line.purchase_order_id.order_line.mapped('product_id')
                            # product_id = cust_mo_line.purchase_order_id.product_id
                            for product_id in product_ids:
                                component_line = (0, 0, {
                                    'product_id': product_id.id,
                                    'name': product_id.display_name,
                                    'location_id': location_id.id,
                                    'product_uom_qty': 1,
                                    'product_uom': product_id.uom_id.id,
                                    'location_dest_id': location_dest.id
                                })
                                component_lines.append(component_line)
                        elif cust_mo_line.mrp_id:
                            product_id = cust_mo_line.mrp_id[0].product_id
                            component_line = (0, 0, {
                                'product_id': product_id.id,
                                'name': product_id.display_name,
                                'location_id': location_id.id,
                                'product_uom_qty': 1,
                                'product_uom': product_id.uom_id.id,
                                'location_dest_id': location_dest.id
                            })
                            component_lines.append(component_line)
                        else:
                            if cust_mo_line.linked_product_id:
                                product_id = cust_mo_line.linked_product_id
                                component_line = (0, 0, {
                                    'product_id': product_id.id,
                                    'name': product_id.display_name,
                                    'location_id': location_id.id,
                                    'product_uom_qty': 1,
                                    'product_uom': product_id.uom_id.id,
                                    'location_dest_id': location_dest.id
                                })
                                component_lines.append(component_line)

                        product_to_link_in_cust_mo = self.env['product.product'].sudo().search(
                            [('mo_link_product_id', '=', cust_mo_line.product_id.id)], limit=1)
                        cust_mo_attachment_id = attachment_obj.create({
                            'name': cust_mo_line.product_id.name,
                            'res_model': cust_mo_line._name,
                            'res_id': cust_mo_line.id,
                            'datas': cust_mo_line.art_work_image,
                            'mimetype': 'image/gif',
                        })
                        customise_production_id = self.env['mrp.production'].with_context(
                            customisation_required=True).create({
                            'product_id': cust_mo_line.product_id.id,
                            'product_qty': cust_mo_line.qty_to_next_action,
                            'product_uom_id': cust_mo_line.product_id.uom_id and cust_mo_line.product_id.uom_id.id or False,
                            'bom_id': cust_mo_line.product_id.bom_ids[
                                0].id if cust_mo_line.product_id.bom_ids else False,
                            'origin': self.sale_order_id.name,
                            'partner_id': self.sale_order_id.partner_id.id,
                            'sale_order_id': self.sale_order_id.id,
                            'customisation_details': cust_mo_line.customisation_details,
                            'picking_type_id': mrp_picking_type_id.id,
                            'location_src_id': mrp_picking_type_id.default_location_src_id.id,
                            'location_dest_id': mrp_picking_type_id.default_location_dest_id.id,
                            # 'location_dest_id': finished_goods_location.id or mrp_picking_type_id.default_location_dest_id.id,
                            'branding_mo': True,
                            'move_raw_ids': component_lines
                            })
                        customise_production_id._onchange_bom_id()
                        customise_production_id.product_qty = cust_mo_line.qty_to_next_action
                        customise_production_id._onchange_move_raw()
                        customise_production_id._onchange_move_finished_product()
                        customise_production_id.message_post(body='Art Work', attachment_ids=cust_mo_attachment_id.ids)
                        cust_mo_line.update({
                            'mrp_id': [(4, customise_production_id.id)]
                        })
                        cust_mo_line.next_action_done = True

            if sum(self.next_action_line_ids.mapped('next_action_done')) == len(self.next_action_line_ids) and sum(
                    self.next_action_line_ids.mapped('qty_to_next_action')) == sum(self.sale_order_id.order_line.mapped('product_uom_qty')):
                self.state = 'so_created'
            else:
                self.state = 'partially_created'
            if self.state == 'so_created':
                # self.sale_order_id.action_confirm()
                self.sale_order_id.state = 'done'
                all_picking_ids = self.sale_order_id.picking_ids
                main_picking_id = max(all_picking_ids)
                sale_picking_ids = all_picking_ids.filtered(lambda pic: pic != main_picking_id)
                product_qty = {}
                for pic_id in sale_picking_ids.mapped('move_ids_without_package'):
                    if pic_id.product_id in product_qty:
                        new_qty = product_qty.get(pic_id.product_id) + pic_id.product_uom_qty
                        product_qty.update({
                            pic_id.product_id: new_qty
                        })
                    else:
                        product_qty.update({
                            pic_id.product_id: pic_id.product_uom_qty
                        })
                for move_line in main_picking_id.move_ids_without_package:
                    if move_line.product_id in product_qty:
                        if move_line.product_uom_qty > product_qty.get(move_line.product_id):
                            move_line.product_uom_qty -= product_qty.get(move_line.product_id)
                            new_quantity = product_qty.get(move_line.product_id) - move_line.product_uom_qty
                            product_qty.update({
                                move_line.product_id: new_quantity
                            })
                        else:
                            new_quantity = product_qty.get(move_line.product_id) - move_line.product_uom_qty
                            product_qty.update({
                                move_line.product_id: new_quantity
                            })
                            move_line.state = 'draft'
                            move_line.unlink()
        else:
            raise ValidationError(_("Please select products or quantity"))


class SONextActionLine(models.Model):
    _name = 'so.next.action.line'
    _description = 'Sale Order Next Action Plan Line'

    product_id = fields.Many2one('product.product', string="Product")
    qty_ordered = fields.Float(string='Quantity Ordered', digits='Product Unit of Measure')
    qty_to_do = fields.Float(string='Quantity To Do', digits='Product Unit of Measure')
    qty_to_next_action = fields.Float(string='Quantity To Next Action', digits='Product Unit of Measure')
    qty_remaining = fields.Float(string='Quantity Remaining', digits='Product Unit of Measure')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    price_unit = fields.Float(string='Price Unit')
    next_action = fields.Selection([
        ('manufacture', 'Manufacture'),
        ('buy', 'Buy')], string="Next Action")
    customise = fields.Selection([
        ('required', 'Required'),
        ('not_required', 'Not Required')], string="Customisation")
    customisation_details = fields.Char(string="Customisation Details")
    partner_id = fields.Many2one('res.partner', 'Vendor')
    customisation_type_ids = fields.Many2many('customisation.type', 'next_action_cust_type_rel', 'next_action_line_id',
                                              'cust_type_id', 'Customisation Type')
    so_next_action_id = fields.Many2one('so.next.action', 'Sale Order Next Action')
    next_action_done = fields.Boolean(string='Next Action Done')
    art_work_image = fields.Binary(string="Art Work")
    picking_id = fields.Many2one('stock.picking', string="Picking")
    mrp_id = fields.Many2many('mrp.production', string="MRP Order")
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    linked_product_id = fields.Many2one('product.product', string="Linked Products")

    @api.onchange('next_action')
    def onchange_next_action(self):
        product_list = False
        if self.next_action:
            if self.next_action == 'manufacture':
                product_to_link_in_mo = self.env['product.product'].sudo().search(
                    [('mo_link_product_id', '=', self.product_id.id)])
                product_list = product_to_link_in_mo.ids or False
            elif self.next_action == 'buy':
                product_to_link_in_po = self.env['product.product'].sudo().search(
                    [('po_link_product_id', '=', self.product_id.id)])
                product_list = product_to_link_in_po.ids or False
        else:
            product_list = self.env['product.product'].search([]).ids
        domain = {'domain': {'linked_product_id': [('id', 'in', product_list)]}}
        return domain

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            parent_so_line_id = self.so_next_action_id.sale_order_id.parent_so_id.order_line.filtered(lambda pa_so_line: pa_so_line.product_template_id.id == self.product_id.product_tmpl_id.id)
            so_line_id = self.so_next_action_id.sale_order_id.order_line.filtered(
                lambda so_line: so_line.product_id.id == self.product_id.id)
            if so_line_id:
                self.product_uom_id = so_line_id[0].product_uom.id
                self.price_unit = so_line_id[0].price_unit

                existing_line = self.so_next_action_id.next_action_line_ids.filtered(
                    lambda l: l.product_id.id == self.product_id.id)
                if existing_line:
                    self.customise = existing_line[0].customise or so_line_id[0].customise
                    self.customisation_details = existing_line[0].customisation_details or so_line_id[0].customisation_details
                    self.customisation_type_ids = existing_line[0].customisation_type_ids or so_line_id[0].customisation_type_ids
                    self.qty_ordered = existing_line[0].qty_ordered or parent_so_line_id[0].product_uom_qty
                    self.qty_to_do = existing_line[0].qty_to_do or so_line_id[0].product_uom_qty
                    self.art_work_image = existing_line[0].art_work_image or so_line_id[0].art_work_image
                else:
                    self.customise = so_line_id[0].customise
                    self.customisation_details = so_line_id[0].customisation_details
                    self.customisation_type_ids = so_line_id[0].customisation_type_ids
                    self.qty_ordered = parent_so_line_id[0].product_uom_qty
                    self.qty_to_do = so_line_id[0].product_uom_qty
                    self.art_work_image = so_line_id[0].art_work_image

        else:
            self.customise = False
            self.customisation_details = False
            self.customisation_type_ids = False
            self.qty_ordered = 0
            self.qty_to_do = 0
            self.product_uom_id = False
            self.price_unit = False
            self.art_work_image = False

        if self.so_next_action_id and self.so_next_action_id.sale_order_id:
            sale_order_product_ids = self.so_next_action_id.sale_order_id.order_line.mapped('product_id.id')
            return {'domain': {'product_id': [('id', 'in', sale_order_product_ids)]}}

    def unlink(self):
        sale_id = self.picking_id.sale_id
        if self.picking_id:
            if self.picking_id.state == 'done':
                raise ValidationError(_("The transfer is already completed"))
            else:
                if self.picking_id.state == 'assigned':
                    self.picking_id.do_unreserve()
                self.picking_id.state = 'draft'
                for picking in self.picking_id.move_ids_without_package:
                    if picking.product_id == self.product_id:
                        if picking.product_uom_qty > self.qty_to_next_action:
                            picking.product_uom_qty -= self.qty_to_next_action
                        else:
                            picking.state = 'draft'
                            picking.unlink()
                if self.picking_id.move_ids_without_package:
                    self.picking_id.action_confirm()
                    self.picking_id.action_assign()
                else:
                    self.picking_id.unlink()
                self.picking_id.sale_id = sale_id.id

        if self.mrp_id:
            for mrp in self.mrp_id:
                sale_order = mrp.sale_order_id
                if mrp.state == 'done':
                    raise ValidationError(_("The Manufacturing order is already completed"))
                else:
                    mrp.sudo().action_cancel()
                mrp.sale_order_id = sale_order.id

        if self.purchase_order_id:
            if self.purchase_order_id.state in ['purchase', 'done']:
                self.purchase_order_id.button_cancel()
                self.purchase_order_id.button_draft()
            for line in self.purchase_order_id.order_line:
                if line.product_id == self.product_id:
                    if line.product_qty > self.qty_to_next_action:
                        line.product_qty -= self.qty_to_next_action
                    else:
                        line.unlink()
            if not self.purchase_order_id.order_line:
                self.purchase_order_id.button_cancel()
        return super(SONextActionLine, self).unlink()
