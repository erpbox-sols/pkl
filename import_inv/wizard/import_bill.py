# -*- coding: utf-8 -*-


import time
import tempfile
import binascii
import xlrd
import io
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import datetime
from odoo.exceptions import Warning
from collections import Counter
from odoo import models, fields, exceptions, api, _


class DynamicField(models.TransientModel):
    _name = 'import.inv.new'
    _description = 'Import'

    file = fields.Binary('File')
    number = fields.Integer('Number')

    def import_inv(self):
        buffer = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        buffer.write(binascii.a2b_base64(self.file))
        buffer.seek(0)
        book = xlrd.open_workbook(buffer.name)
        sheet = book.sheet_by_index(0)
        invoice_name = 'new'
        count = 0
        product_template = False
        product_id = []
        product_id_3_list = []
        int_ref = False
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row: row.value.encode('utf-8'), sheet.row(row_no))
            else:
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))
                if line:
                    count += 1
                    print("Line", count)
                    if line[0]:
                        product_col = line[0]
                        pro_id = product_col.split('_')
                        product_int = int(pro_id[6])
                        product_id = self.env['product.product'].search([('ext_id_map', '=', product_int)])
                        print("PRODUCT ID", product_id)
                        if product_id and line[10]:
                            po_link_pro_id = line[10].split('_')
                            po_link_pro_int = int(po_link_pro_id[6])
                            if po_link_pro_int == 799:
                                po_link_product_ids = self.env['res.partner'].browse(12495)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 783:
                                po_link_product_ids = self.env['res.partner'].browse(12228)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 6092:
                                po_link_product_ids = self.env['res.partner'].browse(12530)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 6162:
                                po_link_product_ids = self.env['res.partner'].browse(13080)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 6129:
                                po_link_product_ids = self.env['res.partner'].browse(13039)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 861:
                                po_link_product_ids = self.env['res.partner'].browse(13201)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id

                            elif po_link_pro_int == 826:
                                po_link_product_ids = self.env['res.partner'].browse(12749)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 847:
                                po_link_product_ids = self.env['res.partner'].browse(13010)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id
                            elif po_link_pro_int == 857:
                                po_link_product_ids = self.env['res.partner'].browse(13120)
                                print("PRODUCT PO ID", po_link_product_ids)
                                if po_link_product_ids:
                                    product_id.vendor_id = po_link_product_ids.id

    def run_the_code(self):
        if self.number:
            self.env['ir.property'].sudo().search([('fields_id', '=', self.number)]).unlink()
