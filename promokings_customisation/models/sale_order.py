# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_is_sale_admin(self):
        """For checking user right for Sale admin"""
        user_ids = self.env['res.users'].search([])
        sale_admin_ids = user_ids.filtered(lambda l: l.has_group('promokings_customisation.group_sale_creation_officer')).ids
        self.is_sale_admin = True if self.env.user.id in sale_admin_ids else False

    state = fields.Selection(selection_add=[('quotation_confirmed', 'Quotation Confirmed'), ('sale',)])
    manufacturing_order_count = fields.Integer(string='Manufacturing Orders Count',
                                               compute='_compute_manufacturing_order_count')
    parent_so_id = fields.Many2one('sale.order', 'Parent Sale Order')
    child_so_count = fields.Integer(string='Child Sale Order Count', compute='_compute_child_so_count')
    child_ids = fields.Many2many('sale.order', 'sale_order_child_rel', 'child_so_id', 'so_parent_id',
                                 string="Child Sale Orders", copy=False)
    next_action_count = fields.Integer(string='"Next Action Plans Count', compute='_compute_next_action_plan_count')
    next_action_ids = fields.Many2many('so.next.action', 'so_next_action_rel', 'next_action_id', 'sale_order_id',
                                       string="Next Action Plans", copy=False)
    estimated_po = fields.Char(string='Estimated PO', copy=False)

    is_sale_admin = fields.Boolean(compute=_check_is_sale_admin, readonly=True)

    def button_quotation_confirm(self):
        self.state = 'quotation_confirmed'

    def _compute_manufacturing_order_count(self):
        for order in self:
            mo_count = self.env['mrp.production'].sudo().search_count([('origin', '=', order.name)])
            order.manufacturing_order_count = mo_count

    def action_view_manufacturing_orders(self):
        manufacturing_orders = self.env['mrp.production'].sudo().search([('origin', '=', self.name)])
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.mrp_production_action")
        if len(manufacturing_orders) > 1:
            action['domain'] = [('id', 'in', manufacturing_orders.ids)]
        elif len(manufacturing_orders) == 1:
            form_view = [(self.env.ref('mrp.mrp_production_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = manufacturing_orders.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def button_open_multiple_so_creation_wizard(self):
        art_works = self.order_line.mapped('art_work_image')
        customise = self.order_line.mapped('customise')
        customization_type_ids = self.order_line.mapped('customisation_type_ids').ids
        if False in art_works:
            raise UserError(_("Please fill the Art Work Images in Order line."))
        if False in customise:
            raise UserError(_("Please fill Customise in Order line."))
        if False in customization_type_ids:
            raise UserError(_("Please fill the Customisation type in Order line."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create SO'),
            'res_model': 'multiple.so.creation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            },
            'views': [[False, 'form']]
        }

    def _compute_child_so_count(self):
        for order in self:
            child_so_count = len(self.child_ids)
            order.child_so_count = child_so_count

    def action_view_child_so_orders(self):
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        if len(self.child_ids) > 1:
            action['domain'] = [('id', 'in', self.child_ids.ids)]
        elif len(self.child_ids) == 1:
            form_view = [(self.env.ref('sale.view_order_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.child_ids[0].id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _compute_next_action_plan_count(self):
        for order in self:
            next_action_count = len(self.next_action_ids)
            order.next_action_count = next_action_count

    def action_view_next_action_plans(self):
        action = self.env["ir.actions.actions"]._for_xml_id("promokings_customisation.action_so_next_action")
        if len(self.next_action_ids) > 1:
            action['domain'] = [('id', 'in', self.next_action_ids.ids)]
        elif len(self.next_action_ids) == 1:
            form_view = [(self.env.ref('promokings_customisation.view_so_next_action_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.next_action_ids[0].id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def _action_confirm(self):
        if self.parent_so_id:
            return super(SaleOrder, self)._action_confirm()

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.picking_ids:
            for picking in self.picking_ids:
                for move_line in picking.move_lines:
                    for line in self.order_line:
                        if move_line.product_id == line.product_id:
                            move_line.art_work_image = line.art_work_image
        return res

    @api.model
    def default_get(self, fields):
        if self:
            if not self.is_sale_admin:
                raise UserError(_("You are not allow to create Sale order. Please contact Administrator"))
        vals = super(SaleOrder, self).default_get(fields)
        terms_condition = self.env['ir.config_parameter'].sudo().get_param('promokings_customisation.sale_terms_condition')
        is_terms_condition = self.env['ir.config_parameter'].sudo().get_param('promokings_customisation.is_sale_terms_condition')
        if is_terms_condition:
            vals['note'] = terms_condition
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)
        if record:
            if not record.is_sale_admin:
                raise UserError(_("You are not allow to create Sale order. Please contact Administrator"))
        return record


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    customise = fields.Selection([
        ('required', 'Required'),
        ('not_required', 'Not Required')], string="Customisation")
    customisation_details = fields.Char(string="Customisation Details")
    customisation_type_ids = fields.Many2many('customisation.type', 'so_line_cust_type_rel', 'so_line_id',
                                              'cust_type_id', 'Customisation Type')
    qty_remaining = fields.Float(string='Quantity Remaining', digits='Product Unit of Measure', copy=False)
    art_work_image = fields.Binary(string="Art Work")
    delivery_timelines = fields.Selection([
        ('3_5_days', '3-5 Working Days'),
        ('7_10_days', '7-10 Working Days'),
        ('10_21_days', '10-21 Working Days'),
        ('3_5_weeks', '3-5 Weeks'),
        ('24_48_hours', '24-48 Hours')], string="Delivery Timelines")

    delivery_date = fields.Date('Delivery Date', copy=False)

    @api.onchange('product_template_id')
    def onchange_product_template_id(self):
        for line in self:
            if line.product_template_id and not line.product_id:
                line.product_id = line.product_template_id.product_variant_ids[0]

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        for line in self:
            if line.state in ['draft', 'sent']:
                line.name = line.product_template_id.name
        return res
