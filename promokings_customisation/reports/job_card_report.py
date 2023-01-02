# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class JobCardReport(models.AbstractModel):
    _name = 'report.sale.report_job_card'
    _description = 'Job Card Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
        }
