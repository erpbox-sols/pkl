# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _check_is_product_admin(self):
        """For checking user right for Sale admin"""
        user_ids = self.env['res.users'].search([])
        product_admin_ids = user_ids.filtered(lambda l: l.has_group('promokings_customisation.group_product_creation_officer')).ids
        self.is_product_admin = True if self.env.user.id in product_admin_ids else False

    is_product_admin = fields.Boolean(compute=_check_is_product_admin, readonly=True)
    po_link_product_id = fields.Many2one("product.product", string="Product to Link in PO")
    vendor_id = fields.Many2one("res.partner", string="Vendor")
    mo_link_product_id = fields.Many2one("product.product", string="Product to Link in MO")
    ext_id_map = fields.Integer("Ext ID")

    @api.onchange('vendor_id')
    def _onchange_vendor_id(self):
        """Onchange function for adding supplier details based on the vendor details"""
        if self.vendor_id:
            supplier_lines = [(5, 0, 0)]
            for line in self.vendor_id:
                supplier_line = (0, 0, {
                    'name': line.id,
                    'min_qty': 1,
                    'price': self.standard_price
                })
                supplier_lines.append(supplier_line)
            self.seller_ids = supplier_lines

    @api.model
    def default_get(self, fields):
        if self:
            for record in self:
                if not record.is_product_admin:
                    raise UserError(_("You are not allow to create Products. Please contact Administrator"))
        return super(ProductProduct, self).default_get(fields)

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)
        if record:
            for rec in record:
                if not rec.is_product_admin:
                    raise UserError(_("You are not allow to create Products. Please contact Administrator"))
        return record


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _check_is_template_admin(self):
        """For checking user right for Sale admin"""
        user_ids = self.env['res.users'].search([])
        product_admin_ids = user_ids.filtered(lambda l: l.has_group('promokings_customisation.group_product_creation_officer')).ids
        self.is_template_admin = True if self.env.user.id in product_admin_ids else False

    is_template_admin = fields.Boolean(compute=_check_is_template_admin, readonly=True)
    ext_tmpl_id_map = fields.Integer("Prod TMPL ID")

    @api.model
    def default_get(self, fields):
        if self:
            for record in self:
                if not record.is_template_admin:
                    raise UserError(_("You are not allow to create Products. Please contact Administrator"))
        return super(ProductTemplate, self).default_get(fields)

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)
        if record:
            for rec in record:
                if not rec.is_template_admin:
                    raise UserError(_("You are not allow to create Products. Please contact Administrator"))
        return record
