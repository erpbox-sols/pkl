
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    picking_quantity = fields.Selection(selection_add=[('package_label', 'Package Label'),
                                                       ], ondelete={'package_label': 'cascade'})

    def process(self):
        if self.picking_quantity == 'package_label':
            ctx = self.env.context
            # record = self.env['stock.picking'].browse(ctx.get('active_id'))
            stock_move_lines = self.env['stock.move.line'].browse(ctx.get('default_move_line_ids'))
            packages = stock_move_lines.mapped('result_package_id')
            data = packages
            xml_id = 'stock.action_report_quant_package_barcode'
            report_action = self.env.ref(xml_id).report_action(data)
            report_action.update({'close_on_report_download': True})
            return report_action
        return super(ProductLabelLayout, self).process()
