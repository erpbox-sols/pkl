
from odoo import fields, models, api
from werkzeug.urls import url_join
import requests
from odoo.exceptions import UserError


class ResConfigSettingsInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_terms_condition = fields.Char(
        string='Sale Terms and Condition', config_parameter='promokings_customisation.sale_terms_condition',
        help="Sale order Terms and condition")
    is_sale_terms_condition = fields.Boolean(
        string='Is a Sale Terms and Condition', config_parameter='promokings_customisation.is_sale_terms_condition',
        help="Check this box to add Sale order Terms and condition")

    purchase_terms_condition = fields.Char(
        string='Purchase Terms and Condition', config_parameter='promokings_customisation.purchase_terms_condition',
        help="Purchase order Terms and condition")
    is_purchase_terms_condition = fields.Boolean(
        string='Is a Purchase Terms and Condition', config_parameter='promokings_customisation.is_purchase_terms_condition',
        help="Check this box to add Purchase order Terms and condition")

    invoice_terms_condition = fields.Char(
        string='Invoice Terms and Condition', config_parameter='promokings_customisation.invoice_terms_condition',
        help="Invoice order Terms and condition")
    is_invoice_terms_condition = fields.Boolean(
        string='Is an Invoice Terms and Condition', config_parameter='promokings_customisation.is_invoice_terms_condition',
        help="Check this box to add invoice order Terms and condition")
