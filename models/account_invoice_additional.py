# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class InvoiceAdditional(models.Model):
    _name = "account.invoice.additional"
    '''
    Ejemplo:
    <Adicional>
    <NodosA>
    <A1>
        Glosa de Pago : 30 Dias fecha factura
    </A1>
    [....]
    </NodosA>
    </Adicional>
    '''
    invoice_id = fields.Many2one(
        'account.invoice', 'Invoice',
        required=True, ondelete='cascade', select=True, readonly=True)
    name = fields.Char(
        'Additional Node', required=True, readonly=False,
        help='Additional description')
