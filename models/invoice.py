# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models, api, _
from openerp.exceptions import Warning as UserError
from datetime import datetime, timedelta
import logging, re, json, os
from lxml import etree
from lxml.etree import Element, SubElement
import pytz
import collections
import urllib3
import xmltodict
import dicttoxml
from elaphe import barcode
import M2Crypto
import base64
import hashlib
import cchardet
import ssl
from SOAPpy import SOAPProxy
# from signxml import xmldsig, methods
import textwrap
from signxml import *
from lxml import objectify
from lxml.etree import XMLSyntaxError
import requests

from xml.dom.minidom import parseString

_logger = logging.getLogger(__name__)
"""
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import OpenSSL
from OpenSSL.crypto import *"""


pool = urllib3.PoolManager()
xsdpath = os.path.dirname(os.path.realpath(__file__)).replace(
    '/models', '/static/xsd/')
host = 'https://libredte.cl/api'
api_emitir = host + '/dte/documentos/emitir'
api_generar = host + '/dte/documentos/generar'
api_gen_pdf = host + '/dte/documentos/generar_pdf'
api_get_doc = host + '/dte/dte_emitidos/{0}/{1}/{2}/{3}'
api_get_xml = host + '/dte/dte_emitidos/xml/{0}/{1}/{2}'
api_upd_satus = host + '/dte/dte_emitidos/actualizar_estado/'
no_product = False
special_chars = [
    [u'á', 'a'],
    [u'é', 'e'],
    [u'í', 'i'],
    [u'ó', 'o'],
    [u'ú', 'u'],
    [u'ñ', 'n'],
    [u'Á', 'A'],
    [u'É', 'E'],
    [u'Í', 'I'],
    [u'Ó', 'O'],
    [u'Ú', 'U'],
    [u'Ñ', 'N']]

"""
Diccionario para normalizar datos y emplear en diversos tipos de documentos
a Futuro.
La idea es cambiar la manera en que se rellenan, normalizan, y validan los
tags, mediante una forma unificada y tendiendo a usar decoradores y funciones
para todas las finalidades.
Además esta parte de la implementación, para mejor efectividad se deberá migrar
a una biblioteca separada, de manera que se pueda acceder desde diferentes
addons: permitiendo así seguir el principio "DRY" de Python.
el value[0] de la lista representa la longitud admitida
Propuesta:
todo: el value[1] si es obligatorio o no
todo: el value[2] puede ser la llamada a funcion para validar
todo: el value[3] el nombre de campo mapeado en Odoo
@author: Daniel Blanco Martín daniel[at]blancomartin.cl
@version: 2017-02-11
"""
normalize_tags = collections.OrderedDict()
normalize_tags['Encabezado'] = collections.OrderedDict()
normalize_tags['Encabezado']['Emisor'] = collections.OrderedDict()
normalize_tags['Encabezado']['Emisor']['RutEmisor'] = [10]
normalize_tags['Encabezado']['Emisor']['RznSoc'] = [100]
normalize_tags['Encabezado']['Emisor']['GiroEmis'] = [80]
normalize_tags['Encabezado']['Emisor']['Telefono'] = [20]
normalize_tags['Encabezado']['Emisor']['CorreoEmisor'] = [80]
normalize_tags['Encabezado']['Emisor']['Acteco'] = [6]
normalize_tags['Encabezado']['Emisor']['CdgTraslado'] = [1]
normalize_tags['Encabezado']['Emisor']['FolioAut'] = [5]
normalize_tags['Encabezado']['Emisor']['FchAut'] = [10]
normalize_tags['Encabezado']['Emisor']['Sucursal'] = [20]
normalize_tags['Encabezado']['Emisor']['CdgSIISucur'] = [9]
normalize_tags['Encabezado']['Emisor']['CodAdicSucur'] = [20]
normalize_tags['Encabezado']['Emisor']['DirOrigen'] = [60]
normalize_tags['Encabezado']['Emisor']['CmnaOrigen'] = [20]
normalize_tags['Encabezado']['Emisor']['CiudadOrigen'] = [20]
normalize_tags['Encabezado']['Emisor']['CdgVendedor'] = [60]
normalize_tags['Encabezado']['Emisor']['IdAdicEmisor'] = [20]
normalize_tags['Encabezado']['Emisor']['IdAdicEmisor'] = [20]
normalize_tags['Encabezado']['Receptor'] = collections.OrderedDict()
normalize_tags['Encabezado']['Receptor']['RUTRecep'] = [10]
normalize_tags['Encabezado']['Receptor']['CdgIntRecep'] = [20]
normalize_tags['Encabezado']['Receptor']['RznSocRecep'] = [100]
normalize_tags['Encabezado']['Receptor']['NumId'] = [20]
normalize_tags['Encabezado']['Receptor']['Nacionalidad'] = [3]
normalize_tags['Encabezado']['Receptor']['IdAdicRecep'] = [20]
normalize_tags['Encabezado']['Receptor']['GiroRecep'] = [40]
normalize_tags['Encabezado']['Receptor']['Contacto'] = [80]
normalize_tags['Encabezado']['Receptor']['CorreoRecep'] = [80]
normalize_tags['Encabezado']['Receptor']['DirRecep'] = [70]
normalize_tags['Encabezado']['Receptor']['CmnaRecep'] = [20]
normalize_tags['Encabezado']['Receptor']['CiudadRecep'] = [20]
normalize_tags['Encabezado']['Receptor']['DirPostal'] = [70]
normalize_tags['Encabezado']['Receptor']['CmnaPostal'] = [20]
normalize_tags['Encabezado']['Receptor']['CiudadPostal'] = [20]
normalize_tags['Encabezado']['Transporte'] = collections.OrderedDict()
normalize_tags['Encabezado']['Transporte']['Patente'] = [8]
normalize_tags['Encabezado']['Transporte']['RUTTrans'] = [10]
normalize_tags['Encabezado']['Transporte']['RUTChofer'] = [10]
normalize_tags['Encabezado']['Transporte']['NombreChofer'] = [30]
normalize_tags['Encabezado']['Transporte']['DirDest'] = [70]
normalize_tags['Encabezado']['Transporte']['CmnaDest'] = [20]
normalize_tags['Encabezado']['Transporte']['CiudadDest'] = [20]
normalize_tags['Encabezado']['Transporte']['CiudadDest'] = [20]
normalize_tags['Encabezado']['Totales'] = collections.OrderedDict()
normalize_tags['Encabezado']['Totales']['MntNeto'] = [18]
normalize_tags['Encabezado']['Totales']['MntExe'] = [18]
normalize_tags['Encabezado']['Totales']['MntBase'] = [18]
normalize_tags['Encabezado']['Totales']['MntMargenCom'] = [18]
normalize_tags['Encabezado']['Totales']['TasaIVA'] = [5]
normalize_tags['Encabezado']['Totales']['IVA'] = [18]
normalize_tags['Encabezado']['Totales']['IVAProp'] = [18]
normalize_tags['Encabezado']['Totales']['IVATerc'] = [18]
# pluralizado deliberadamente 'ImptoRetens' en lugar de ImptoReten
normalize_tags[
    'Encabezado']['Totales']['ImptoRetens'] = collections.OrderedDict()
normalize_tags[
    'Encabezado']['Totales']['ImptoRetens'][
    'ImptoReten'] = collections.OrderedDict()
normalize_tags['Encabezado']['Totales']['ImptoRetens']['ImptoReten'][
    'TipoImp'] = [3]
normalize_tags['Encabezado']['Totales']['ImptoRetens']['ImptoReten'][
    'TasaImp'] = [5]
normalize_tags['Encabezado']['Totales']['ImptoRetens']['ImptoReten'][
    'MontoImp'] = [18]
normalize_tags['Encabezado']['Totales']['IVANoRet'] = [18]
normalize_tags['Encabezado']['Totales']['CredEC'] = [18]
normalize_tags['Encabezado']['Totales']['GmtDep'] = [18]
normalize_tags['Encabezado']['Totales']['ValComNeto'] = [18]
normalize_tags['Encabezado']['Totales']['ValComExe'] = [18]
normalize_tags['Encabezado']['Totales']['ValComIVA'] = [18]
normalize_tags['Encabezado']['Totales']['MntTotal'] = [18]
normalize_tags['Encabezado']['Totales']['MontoNF'] = [18]
normalize_tags['Encabezado']['Totales']['MontoPeriodo'] = [18]
normalize_tags['Encabezado']['Totales']['SaldoAnterior'] = [18]
normalize_tags['Encabezado']['Totales']['VlrPagar'] = [18]
normalize_tags['Encabezado']['OtraMoneda'] = collections.OrderedDict()
normalize_tags['Encabezado']['OtraMoneda']['TpoMoneda'] = [15]
normalize_tags['Encabezado']['OtraMoneda']['TpoCambio'] = [10]
normalize_tags['Encabezado']['OtraMoneda']['MntNetoOtrMnda'] = [18]
normalize_tags['Encabezado']['OtraMoneda']['MntExeOtrMnda'] = [18]
normalize_tags['Encabezado']['OtraMoneda']['MntFaeCarneOtrMnda'] = [18]
normalize_tags['Encabezado']['OtraMoneda']['MntMargComOtrMnda'] = [18]
normalize_tags['Encabezado']['OtraMoneda']['IVAOtrMnda'] = [18]
# pluralizado deliberadamente 'Detalles' en lugar de ImptoReten
# se usó 'Detalles' (plural) para diferenciar del tag real 'Detalle'
# el cual va aplicado a cada elemento de la lista o tabla.
# según el tipo de comunicación, se elimina el tag Detalles o se le quita el
# plural en la conversion a xml
normalize_tags['Detalles'] = collections.OrderedDict()
normalize_tags['Detalles']['Detalle'] = collections.OrderedDict()
normalize_tags['Detalles']['Detalle']['NroLinDet'] = [4]
# ojo qu este que sigue es tabla tambien
normalize_tags['Detalles']['Detalle']['TpoCodigo'] = [10]
normalize_tags['Detalles']['Detalle']['VlrCodigo'] = [35]
normalize_tags['Detalles']['Detalle']['TpoDocLiq'] = [3]
normalize_tags['Detalles']['Detalle']['IndExe'] = [3]
# todo: falta retenedor
normalize_tags['Detalles']['Detalle']['NmbItem'] = [80]
normalize_tags['Detalles']['Detalle']['DscItem'] = [1000]
normalize_tags['Detalles']['Detalle']['QtyRef'] = [18]
normalize_tags['Detalles']['Detalle']['UnmdRef'] = [4]
normalize_tags['Detalles']['Detalle']['PrcRef'] = [18]
normalize_tags['Detalles']['Detalle']['QtyItem'] = [18]
# todo: falta tabla subcantidad
normalize_tags['Detalles']['Detalle']['FchElabor'] = [10]
normalize_tags['Detalles']['Detalle']['FchVencim'] = [10]
normalize_tags['Detalles']['Detalle']['UnmdItem'] = [10]
normalize_tags['Detalles']['Detalle']['PrcItem'] = [18]
# todo: falta tabla OtrMnda
normalize_tags['Detalles']['Detalle']['DescuentoOct'] = [5]
normalize_tags['Detalles']['Detalle']['DescuentoMonto'] = [18]
# todo: falta tabla distrib dcto
# todo: falta tabla distrib recargo
# todo: falta tabla cod imp adicional y retenciones
normalize_tags['Detalles']['Detalle']['MontoItem'] = [18]
# todo: falta subtotales informativos
# ojo que estos descuentos podrían ser globales más de uno,
# pero la implementación soporta uno solo
normalize_tags['DscRcgGlobal'] = collections.OrderedDict()
normalize_tags['DscRcgGlobal']['NroLinDR'] = [2]
normalize_tags['DscRcgGlobal']['TpoMov'] = [1]
normalize_tags['DscRcgGlobal']['GlosaDR'] = [45]
normalize_tags['DscRcgGlobal']['TpoValor'] = [1]
normalize_tags['DscRcgGlobal']['ValorDR'] = [18]
normalize_tags['DscRcgGlobal']['ValorDROtrMnda'] = [18]
normalize_tags['DscRcgGlobal']['IndExeDR'] = [1]
# pluralizado deliberadamente
normalize_tags['Referencias'] = collections.OrderedDict()
normalize_tags['Referencias']['Referencia'] = collections.OrderedDict()
normalize_tags['Referencias']['Referencia']['NroLinRef'] = [2]
normalize_tags['Referencias']['Referencia']['TpoDocRef'] = [3]
normalize_tags['Referencias']['Referencia']['IndGlobal'] = [3]
normalize_tags['Referencias']['Referencia']['FolioRef'] = [18]
normalize_tags['Referencias']['Referencia']['RUTOtr'] = [10]
normalize_tags['Referencias']['Referencia']['IdAdicOtr'] = [20]
normalize_tags['Referencias']['Referencia']['FchRef'] = [10]
normalize_tags['Referencias']['Referencia']['CodRef'] = [1]
normalize_tags['Referencias']['Referencia']['RazonRef'] = [1]
# todo: faltan comisiones y otros cargos

class Invoice(models.Model):
    """
    Extension of data model to contain global parameters needed
    for all electronic invoice integration.
    @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
    @version: 2016-06-11
    """
    _inherit = "account.invoice"

    def objectpicking(self, function):
        def inner(*args, **kwargs):
            try:
                if self._context['active_model'] == 'stock.picking':
                    inv = self.env['stock.picking'].browse(
                        self._context['active_id'])
                    sii_code = 52
            except:
                try:
                    if self._context['params']['model'] == 'stock.picking':
                        inv = self.env['stock.picking'].browse(
                            self._context['params']['id'])
                        sii_code = 52
                except:
                    self.ensure_one()
                    inv = self
                    sii_code = inv.sii_document_class_id.sii_code
                    folio = self.get_folio_current()
            finally:
                self.ensure_one()
                inv = self
                sii_code = inv.sii_document_class_id.sii_code
                folio = self.get_folio_current()

            function(args, kwargs)
        return inner

    def pastelogo(function):
        """
        Función decoradora para agregar
        el Logo de la empresa
        """
        def inner(*args, **kwargs):
            image1 = function(args[0])
            img = Image.open('./danlogoverth.jpg', 'r')
            img_w, img_h = img.size
            background = Image.new('RGBA', (744, 236), (255, 255, 255, 255))
            bg_w, bg_h = background.size
            background.paste(img, (28, 5))
            background.paste(image1, (100, 0))
            return background

        return inner

    def _calc_discount_vat(self, discount, sii_code):
        """
        Función provisoria para calcular el descuento:
        TODO
        @author: Daniel Blanco
        @version: 2016-12-30
        :param headers:
        :param dte:
        :return:
        """
        return discount

    def enviar_ldte(self, inv, dte, headers):
        """
        Función para enviar el dte a libreDTE
        @author: Daniel Blanco
        @version: 2016-10-03
        :param headers:
        :param dte:
        :return:
        """
        _logger.info(json.dumps(dte))
        # raise UserError('----ver ------')
        response_emitir = pool.urlopen(
            'POST', api_emitir, headers=headers, body=json.dumps(
                dte))
        if response_emitir.status != 200:
            raise UserError(
                '- Error en conexión al emitir: {}, {}'.format(
                    response_emitir.status, response_emitir.data))
        _logger.info('response_emitir: {}'.format(
            response_emitir.data))
        _logger.info('response_emitir respuesta satisfactoria')
        try:
            inv.sii_xml_response1 = response_emitir.data
            _logger.info('response_xml: {}'.format(
                response_emitir.data))
            _logger.info('try positivo')
        except:
            _logger.warning(
                'no pudo guardar la respuesta al ws de emision')
            _logger.info('try negativo')
        '''
        {"emisor": ----, "receptor": -, "dte": --,
         "codigo": "-----"}
        '''
        response_emitir_data = response_emitir.data
        response_j = self.bring_xml_ldte(
            inv, response_emitir_data, headers=headers)
        _logger.info('vino de bring_xml_dte')
        _logger.info('response_j')
        _logger.info(response_j)
        return response_j

    @staticmethod
    def char_replace(text):
        """
        Funcion para reemplazar caracteres especiales
        Esta funcion sirve para salvar bug en libreDTE con los recortes de
        giros que están codificados en utf8 (cuando trunca, trunca la
        codificacion)
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-07-31
        """
        for char in special_chars:
            try:
                text = text.replace(char[0], char[1])
            except:
                pass
        print(text)
        return text

    @staticmethod
    def create_template_doc(doc):
        """
        Creacion de plantilla xml para envolver el DTE
        Previo a realizar su firma (1)
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-01
        """
        xml = '''<DTE xmlns="http://www.sii.cl/SiiDte" version="1.0">
<!-- Odoo Implementation Blanco Martin -->
{}</DTE>'''.format(doc)
        return xml

    @staticmethod
    def get_object_record_id(inv, call_model):
        if call_model == 'stock.picking':
            # raise UserError(inv._context)
            try:
                return inv._context['params']['id']
            except:
                return inv._context['active_id']
        else:
            return inv.id

    @staticmethod
    def get_folio(inv):
        """
        Funcion para descargar el folio tomando el valor desde la secuencia
        correspondiente al tipo de documento.
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-05-01
        """
        # saca el folio directamente de la secuencia
        return inv.journal_document_class_id.sequence_id.number_next_actual

    @staticmethod
    def set_folio(inv, folio):
        """
        Funcion para actualizar el folio tomando el valor devuelto por el
        tercera parte integrador.
        Esta funcion se usa cuando un tercero comanda los folios
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-23
        """
        # if dte in [52]:
        #     inv.voucher_ids[0].book_id.sequence_id.number_next_actual = folio
        # else:
        inv.journal_document_class_id.sequence_id.number_next_actual = folio

    @staticmethod
    def remove_indents(xml):
        """
        Funcion para remover los indents del documento previo a enviar el xml
        a firmaar. Realizada para probar si el problema de
        error de firma proviene de los indents.
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-01
        """
        return xml.replace(
            '        <', '<').replace(
            '      <', '<').replace(
            '    <', '<').replace(
            '  <', '<')

    @staticmethod
    def convert_encoding(data, new_coding='UTF-8'):
        """
        Funcion auxiliar para conversion de codificacion de strings
        proyecto experimentos_dte
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2014-12-01
        """
        encoding = cchardet.detect(data)['encoding']
        if new_coding.upper() != encoding.upper():
            data = data.decode(encoding, data).encode(new_coding)
        return data

    @staticmethod
    def xml_validator(some_xml_string, validation='doc'):
        """
        Funcion para validar los xml generados contra el esquema que le
        corresponda segun el tipo de documento.
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-01
        """
        if True:
            validation_type = {
                'doc': 'DTE_v10.xsd',
                'env': 'EnvioDTE_v10.xsd',
                'sig': 'xmldsignature_v10.xsd'}
            xsd_file = xsdpath + validation_type[validation]
            try:
                schema = etree.XMLSchema(file=xsd_file)
                parser = objectify.makeparser(schema=schema)
                objectify.fromstring(some_xml_string, parser)
                _logger.info(_(
                    "The Document XML file validated correctly: {}".format(
                        validation)))
                return True
            except XMLSyntaxError as e:
                _logger.info(
                    _("The Document XML file has error: {}".format(e.args)))
                raise UserError(_('XML Malformed Error {}'.format(e.args)))
        else:
            # manejo de otras acciones futuras
            pass

    def record_reference(self, inv, model='invoice.reference'):
        """
        Función para guardar como referencia la nota de pedido en el picking
        @author: Daniel Blanco daniel[at]blancomartin.cl
        @version: 2016-09-29
        @version: 2016-11-12 los cambios son que puede referir automáticamente
        a un picking o guia de despacho.
        :return:
        """
        # other model option='stock.picking.reference'
        # other order_id = order_id, picking id
        # order_mode = {'order_id': order_id_object,
        # 'model_object_id': picking/invoice}

        #### primero picking
        ref_obj = self.env[model]
        picking_obj = self.env['stock.picking']
        picking_id = picking_obj.search([('name', '=', inv.origin)])
        sale_order = inv.origin
        if picking_id:
            sale_order = picking_id[0].origin
            for picking_voucher in picking_id[0].voucher_ids:
                # raise UserError(
                # picking_voucher.book_id.sii_document_class_id.doc_code_prefix)
                try:
                    vals = {
                        'invoice_id': inv.id,
                        'parent_type': model,
                        'name': int(
                            re.sub(
                                '[^1234567890]', '', picking_voucher.number)),
                        'sii_document_class_id':
                            picking_voucher.book_id.sii_document_class_id.id,
                        'reference_date':
                            picking_voucher.create_date,
                        'prefix':
                            picking_voucher.book_id.
                            sii_document_class_id.doc_code_prefix,
                        'reason': 'Mercadería enviada'}
                    _logger.info('grabando la referencia: {}'.format(vals))
                    ref_obj.create(vals)
                except:
                    pass
                    _logger.info(
                        'Automatic reference to stock voucher does not exist')

        order_obj = self.env['sale.order']
        order_id = order_obj.search([('name', '=', sale_order)])
        sii_ref = self.env.ref('l10n_cl_invoice.dc_ndp')
        try:
            vals = {
                    'invoice_id': inv.id,
                    'parent_type': model,
                    'name': int(re.sub('[^1234567890]', '', order_id[0].name)),
                    'sii_document_class_id': sii_ref.id,
                    'reference_date': order_id[0].date_confirm,
                    'prefix': sii_ref.doc_code_prefix,
                    'reason': 'Venta Confirmada'}
            _logger.info(_('Saving the reference: {}'.format(vals)))
            ref_obj.create(vals)
        except:
            pass
            _logger.info(_('Automatic reference to sale order does not exist'))

    def clean_relationships(self, model='invoice.reference'):
        """
        Limpia relaciones
        @author: Daniel Blanco daniel[at]blancomartin.cl
        @version: 2016-09-29
        :return:
        """
        invoice_id = self.id
        ref_obj = self.env[model]
        ref_obj.search([('invoice_id', '=', invoice_id)]).unlink()

    def clean_xml(self):
        """
        Limpia xml
        @author: Daniel Blanco daniel[at]blancomartin.cl
        @version: 2016-09-29
        :return:
        """
        invoice_id = self.invoice_id
        invoice_id.sii_xml_request = False

    def create_template_envio(self, RutEmisor, RutReceptor, FchResol, NroResol,
                              TmstFirmaEnv, TpoDTE, EnvioDTE):
        """
        Funcion que permite crear una plantilla para el EnvioDTE
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-01
        """
        signature_d = self.get_digital_signature_pem(self.company_id)

        xml = '''<SetDTE ID="OdooBMyA">
<Caratula version="1.0">
<RutEmisor>{0}</RutEmisor>
<RutEnvia>{1}</RutEnvia>
<RutReceptor>{2}</RutReceptor>
<FchResol>{3}</FchResol>
<NroResol>{4}</NroResol>
<TmstFirmaEnv>{5}</TmstFirmaEnv>
<SubTotDTE>
<TpoDTE>{6}</TpoDTE>
<NroDTE>1</NroDTE>
</SubTotDTE>
</Caratula>
{7}
</SetDTE>
'''.format(RutEmisor, signature_d['subject_serial_number'], RutReceptor,
           FchResol, NroResol, TmstFirmaEnv, TpoDTE, EnvioDTE)
        return xml

    def create_headers_ldte(self, comp_id=False):
        """
        Función para crear los headers necesarios por LibreDTE
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-23
        """
        if comp_id:
            dte_username = comp_id.dte_username
            dte_password = comp_id.dte_password
        else:
            dte_username = self.company_id.dte_username
            dte_password = self.company_id.dte_password
        headers = {}
        headers['Authorization'] = 'Basic {}'.format(
            base64.b64encode('{}:{}'.format(
                dte_password, dte_username)))
        # control del header
        # raise UserError(headers['Authorization'])
        headers['Accept-Encoding'] = 'gzip, deflate, identity'
        headers['Accept'] = '*/*'
        headers['User-Agent'] = 'python-requests/2.6.0 CPython/2.7.6 \
Linux/3.13.0-88-generic'
        headers['Connection'] = 'keep-alive'
        headers['Content-Type'] = 'application/json'
        return headers

    @api.multi
    def check_dte_status(self, inv='', foliop='', headers=''):
        """
        obtener estado de DTE.
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-16
        """
        try:
            if str(inv._model) == 'stock.picking':
                company_id_vat = inv.company_id.vat
                sii_code = 52
                pass
            else:
                self.ensure_one()
                # raise UserError('else: {}'.format(self.company_id.vat))
                sii_code = inv.sii_document_class_id.sii_code
                inv = self
                folio = self.get_folio_current()
        except:
            self.ensure_one()
            company_id_vat = self.company_id.vat
            inv = self
        try:
            if not folio:
                folio = foliop
        except:
            folio = foliop
        if inv.dte_service_provider in [
            'EFACTURADELSUR', 'EFACTURADELSUR_TEST']:
            # reobtener el folio
            folio = self.get_folio_current(self.document_number)
            dte_username = self.company_id.dte_username
            dte_password = self.company_id.dte_password
            envio_check = '''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <ObtenerEstadoDTE xmlns="https://www.efacturadelsur.cl">
      <usuario>{0}</usuario>
      <contrasena>{1}</contrasena>
      <rutEmisor>{2}</rutEmisor>
      <tipoDte>{3}</tipoDte>
      <folio>{4}</folio>
    </ObtenerEstadoDTE>
  </soap12:Body>
</soap12:Envelope>'''.format(
            dte_username,
            dte_password,
            self.format_vat(company_id_vat),
            self.sii_document_class_id.sii_code,
            folio)
            _logger.info("envio: {}".format(envio_check))
            host = 'https://www.efacturadelsur.cl'
            post = '/ws/DTE.asmx'  # HTTP/1.1
            url = host + post
            _logger.info('URL to be used {}'.format(url))
            response = pool.urlopen('POST', url, headers={
                'Content-Type': 'application/soap+xml',
                'charset': 'utf-8',
                'Content-Length': len(
                    envio_check)}, body=envio_check)
            _logger.info(response.status)
            _logger.info(response.data)
            if response.status != 200:
                pass
                raise UserError(
                    'The Transmission Has Failed. Error: {}'.format(
                        response.status))

            setenvio = {
                # 'sii_result': 'Enviado' if self.dte_service_provider ==
                # 'EFACTURADELSUR' else self.sii_result,
                'sii_xml_response1': response.data}
            self.write(setenvio)
            x = xmltodict.parse(response.data)
            raise UserError(x['soap:Envelope']['soap:Body'][
                              'ObtenerEstadoDTEResponse'][
                              'ObtenerEstadoDTEResult'])
            root = etree.fromstring(response.data)
            raise UserError(root.ObtenerEstadoDTEResult)

        elif inv.dte_service_provider in ['LIBREDTE', 'LIBREDTE_TEST']:
            '''
            {
                "track_id": ---,
                "revision_estado": "EPR - Envio Procesado",
                "revision_detalle": "DTE aceptado"
            }
            '''
            if headers == '':
                headers = self.create_headers_ldte(comp_id=self.company_id)
            metodo = 1  # =1 servicio web, =0 correo
            # consultar estado de dte emitido
            # raise UserError('headers:{}, sii_code:{}, folio:{}, vat:{}, metodo:{}'.format(
            #    headers, sii_code, folio, str(self.format_vat(company_id_vat)),
            #    metodo))
            response_status = pool.urlopen(
                'GET',
                api_upd_satus + str(sii_code) + '/' + str(
                    folio) + '/' + str(self.format_vat(
                        company_id_vat)) + '/' + str(metodo), headers=headers)

            if response_status.status != 200:
                raise UserError(
                    'Error al obtener el estado del DTE emitido: {}'.format(
                        response_status.data))
            _logger.info('Se recibió una respuesta:')
            _logger.info(response_status.data)
            response_status_j = json.loads(response_status.data)
            _logger.info(response_status_j['track_id'])
            _logger.info(response_status_j['revision_estado'])
            _logger.info(response_status_j['revision_detalle'])
            if response_status_j['revision_estado'] in [
                'DTE aceptado'] or \
                    response_status_j['revision_detalle'] == 'DTE aceptado':
                resultado_status = 'Aceptado'
            elif response_status_j['revision_estado'] in \
                    ['RLV - DTE Aceptado con Reparos Leves']:
                resultado_status = 'Reparo'
            elif response_status_j['revision_estado'][:3] in \
                    ['SOK', 'CRT', 'PDR', 'FOK', '-11']:
                resultado_status = 'Proceso'
                _logger.info('Atención: Revisión en Proceso')
            elif response_status_j['revision_estado'] in \
                    ['RCH - DTE Rechazado',
                     'RFR - Rechazado por Error en Firma',
                     'RSC - Rechazado por Error en Schema',
                     'RCT - Rechazado por Error en Carátula']:
                resultado_status = 'Rechazado'
            else:
                resultado_status = inv.sii_result
            _logger.info('a grabar resultado_status: {}'.format(
                resultado_status))
            setenvio = {
                'sii_xml_response2': response_status.data,
                'sii_result': resultado_status,
                'invoice_printed': 'printed'}
            inv.write(setenvio)
            _logger.info(
                'resultado_status grabado: {}'.format(self.sii_result))
            _logger.info(response_status_j['revision_estado'])

    @api.multi
    def send_dte(self):
        """
        Realización del envío de DTE.
        nota: se cambia el nombre de la función de "send xml file"
        a "send_dte" para ser mas abarcativa en cuanto a que algunos
        service provider no trabajan con xml sino con un diccionario
        (caso de libre dte por ejemplo). Como la funcion se invoca desde un
        boton, pero trambién se podría cambiar aejecutar automaticamente,
        pienso que es más conveniente tratar todas las opciones de provider
        en la misma funcion.
        La funcion selecciona el proveedor de servicio de DTE y efectua el
        envio de acuerdo a la integracion del proveedor.
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-01
        """
        self.ensure_one()

        _logger.info('Entering Send XML Function')
        _logger.info(
            'Service provider is: %s' % self.dte_service_provider)

        if self.dte_service_provider in [
            'EFACTURADELSUR', 'EFACTURADELSUR_TEST']:
            host = 'https://www.efacturadelsur.cl'
            post = '/ws/DTE.asmx' # HTTP/1.1
            url = host + post
            _logger.info('URL to be used {}'.format(url))
            _logger.info('Lenght used for forming envelope: {}'.format(len(
                self.sii_xml_request)))
            response = pool.urlopen('POST', url, headers={
                'Content-Type': 'application/soap+xml',
                'charset': 'utf-8',
                'Content-Length': len(
                    self.sii_xml_request)}, body=self.sii_xml_request)
            _logger.info(response.status)
            _logger.info(response.data)
            if response.status != 200:
                raise UserError(
                    'The Transmission Has Failed. Error: {}'.format(
                        response.status))
            setenvio = {
                'sii_result': 'Enviado'
                    if self.dte_service_provider == 'EFACTURADELSUR'
                    else self.sii_result,
                'sii_xml_response1': response.data}
            self.write(setenvio)

        elif self.dte_service_provider in ['LIBREDTE', 'LIBREDTE_TEST']:
            '''
            LibreDTE no necesita enviar el DTE desde nuestra app. envia solo
            el diccionario.
            '''
            pass
        else:
            pass

    @api.multi
    def get_xml_file(self):
        """
        Funcion para descargar el xml en el sistema local del usuario
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-05-01
        """
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_document?model=account.invoice\
&field=sii_xml_request&id={}&filename=demoxml.xml'.format(self.id),
            'target': 'self'}

    def get_company_dte_service_provider(self):
        """
        Funcion que devuelve el service provider desde la compañia
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-05-01
        """
        return self.company_id.dte_service_provider

    def get_folio_current(self):
        """
        Funcion para obtener el folio ya registrado en el dato
        correspondiente al tipo de documento.
        (remoción del prefijo almacenado)
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-05-01
        """
        prefix = self.journal_document_class_id.sequence_id.prefix
        try:
            folio = self.sii_document_number.replace(prefix, '', 1)
        except:
            folio = self.sii_document_number
        return int(folio)

    @staticmethod
    def format_vat(value):
        """
        Reformateo de RUT desde el formato de Odoo a DV separado por guion
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-05-01
        """
        return value[2:10] + '-' + value[10:]

    @staticmethod
    def get_attachment_name(inv, call_model=''):
        if call_model == 'stock.picking':
            return 'guia-despacho'
        else:
            return inv.sii_document_class_id.name

    """
    Definicion de extension de modelo de datos para account.invoice
    @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
    @version: 2015-02-01
    """
    sii_batch_number = fields.Integer(
        copy=False,
        string='Batch Number',
        readonly=True,
        help='Batch number for processing multiple invoices together')
    sii_barcode = fields.Char(
        copy=False,
        string=_('SII Barcode'),
        readonly=True,
        help='SII Barcode Name')
    sii_barcode_img = fields.Binary(
        copy=False,
        string=_('SII Barcode Image'),
        readonly=True,
        help='SII Barcode Image in PDF417 format')
    sii_message = fields.Text(
        string='SII Message',
        readonly=True,
        copy=False)
    sii_xml_request = fields.Text(
        string='XML Request',
        readonly=True,
        copy=False)
    sii_xml_response1 = fields.Text(
        string='XML Response 1',
        readonly=True,
        copy=False)
    sii_xml_response2 = fields.Text(
        string='XML Response 2',
        readonly=True,
        copy=False)
    sii_send_ident = fields.Text(
        string='SII Send Identification',
        readonly=False,
        copy=False)
    sii_result = fields.Selection([
        ('', 'n/a'),
        ('NoEnviado', 'No Enviado'),
        ('Enviado', 'Enviado'),
        ('Proceso', 'Proceso'),
        ('Reparo', 'Reparo'),
        ('Aceptado', 'Aceptado'),
        ('Rechazado', 'Rechazado'),
        ('Reenviar', 'Reenviar'),
        ('Anulado', 'Anulado')],
        'Resultado',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        help="SII request result",
        default='')
    dte_service_provider = fields.Selection(
        [('', 'None'),
         ('EFACTURADELSUR', 'efacturadelsur.cl'),
         ('EFACTURADELSUR_TEST', 'efacturadelsur.cl (test mode)'),
         ('ENTERNET', 'enternet.cl'),
         ('FACTURACION', 'facturacion.cl'),
         ('FACTURAENLINEA', 'facturaenlinea.cl'),
         ('LIBREDTE', 'LibreDTE'),
         ('LIBREDTE_TEST', 'LibreDTE (test mode)'),
         ('SIIHOMO', 'SII - Certification process'),
         ('SII', 'www.sii.cl'),
         ('SII MiPyme', 'SII - Portal MiPyme'),
         ], 'DTE Service Provider',
        related='company_id.dte_service_provider',
        readonly=True)
    contact_data = fields.Char('Contact Data')
    ref_document_ids = fields.One2many(
        'invoice.reference', 'invoice_id', string='Document References')

    dte_resolution_number = fields.Char('SII Exempt Resolution Number',
                                        help='''This value must be provided \
and must appear in your pdf or printed tribute document, under the electronic \
stamp to be legally valid.''')
    additional_lejend_ids = fields.One2many(
        'account.invoice.additional', 'invoice_id',
        string='Document Additional Lejends')

    # third_party_xml = fields.Binary('XML File', copy=False)
    filename_xml = fields.Char('File Name XML')

    @api.multi
    def get_related_invoices_data(self):
        """
        List related invoice information to fill CbtesAsoc.
        """
        self.ensure_one()
        rel_invoices = self.search([
            ('number', '=', self.origin),
            ('state', 'not in',
                ['draft', 'proforma', 'proforma2', 'cancel'])])
        return rel_invoices

    @api.multi
    def bring_generated_xml_ldte(
            self, foliop=0, headers='', call_model='', r_id=False):
        """
        Función para traer el XML que ya fué generado anteriormente, y sobre
        el cual existe un track id.
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-12-16
        :return:
        """
        ## manejo de excepciones para reusar esta función desde stock.picking
        # raise UserError('self_context: {}, call_model: {}'.format(
        #     self._context, call_model))
        try:
            if call_model == 'stock.picking' or \
                            self._context['active_model'] == 'stock.picking':
                inv = self.env['stock.picking'].browse(
                    self._context['active_id'])
                sii_code = 52
            else:
                self.ensure_one()
                inv = self
                sii_code = inv.sii_document_class_id.sii_code
                folio = self.get_folio_current()
        except:
            self.ensure_one()
            inv = self
            sii_code = inv.sii_document_class_id.sii_code
            folio = self.get_folio_current()
        try:
            if not folio:
                folio = foliop
        except:
            folio = foliop
        emisor = self.format_vat(inv.company_id.vat)
        _logger.info('entrada a bring_generated_xml_ldte. Folio: {}'.format(
            folio))
        if headers == '':
            headers = self.create_headers_ldte()
        _logger.info('headers: {}'.format(headers))
        _logger.info(api_get_doc.format('xml', sii_code, folio, emisor))
        response_xml = pool.urlopen(
            'GET', api_get_doc.format(
                'xml', sii_code, folio, emisor), headers=headers)
        if response_xml.status != 200:
            raise UserError('Error: {}'.format(response_xml.data))
        _logger.info('response_generar: {}'.format(
            base64.b64decode(response_xml.data)))
        inv.sii_xml_request = base64.b64decode(response_xml.data)
        attachment_obj = self.env['ir.attachment']
        _logger.info('Attachment')
        attachment_name = self.get_attachment_name(
            inv, call_model=str(inv._name))
        record_id = r_id or self.get_object_record_id(
            inv, call_model=str(inv._name))
        _logger.info(attachment_name)
        attachment_id = attachment_obj.create(
            {
                'name': 'DTE_'+attachment_name+'-'+str(
                    folio)+'.xml',
                'datas': response_xml.data,
                'datas_fname': 'DTE_'+attachment_name+'-'+str(
                    folio)+'.xml',
                'res_model': str(inv._name),
                'res_id': record_id,
                'type': 'binary'
            })
        _logger.info(
            'Se ha generado factura en XML con el id {} para el id {}'.format(
            attachment_id, record_id))

    @api.multi
    def bring_xml_ldte(self, inv, response_emitir_data, headers=''):
        """
        Función para tomar el XML generado en libreDTE y adjuntarlo al registro
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-23
        """
        _logger.info('entrada a bringxml function')
        if headers == '':
            headers = self.create_headers_ldte()
        _logger.info('api: {}, headers: {}, body: {}'.format(
            api_generar, headers, response_emitir_data))
        response_generar = pool.urlopen(
            'POST', api_generar, headers=headers,
            body=response_emitir_data)
        if response_generar.status != 200:
            raise UserError('Error en conexión al generar: {}, {}'.format(
                response_generar.status, response_generar.data))
        _logger.info('response_generar: {}'.format(response_generar.data))
        inv.sii_xml_response1 = response_emitir_data
        try:
            response_j = json.loads(response_generar.data)
        except:
            raise UserError('LibreDTE No pudo generar el XML.\n'
                'Reintente en un instante. \n{}'.format(
                response_generar.data))
        _logger.info('Folio desde response_j: {}, tipo dte: {}'.format(
            response_j['folio'], response_j['dte']))
        if not response_j['xml']:
            # no trajo el xml: hay que traerlo
            if True:
                if True:
                    _logger.info(
                        'intentando traer el xml. headers: {}, folio: {}'.
                        format(headers, int(response_j['folio'])))
                    response_j['xml'] = self.bring_generated_xml_ldte(
                        int(response_j['folio']), headers=headers)
                else:
                    raise UserError(
                        'No se pudo recibir el XML del documento. Sin embargo, \
este puede haber sido generado en LibreDTE. coloque el folio en el campo \
TRACKID antes de revalidar, reintente la validación.')
            else:
                raise UserError('bring_gen: no pudo traer el xml')
        else:
            attachment_obj = self.env['ir.attachment']
            _logger.info('Attachment')
            _logger.info(inv.sii_document_class_id.name)
            _logger.info(response_j['folio'])
            attachment_id = attachment_obj.create(
                {
                    'name': 'DTE_'+inv.sii_document_class_id.name+'-'+str(
                        response_j['folio'])+'.xml',
                    'datas': response_j['xml'],
                    'datas_fname': 'DTE_'+inv.sii_document_class_id.name+'-'+str(
                        response_j['folio'])+'.xml',
                    'res_model': inv._name,
                    'res_id': inv.id,
                    'type': 'binary'
                })
            _logger.info('Se ha generado factura en XML con el id {}'.format(
                attachment_id))
        return response_j

    @api.multi
    def get_xml_attachment(self, inv=''):
        """
        Función para leer el xml para libreDTE desde los attachments
        @author: Daniel Blanco Martín (daniel[at]blancomartin.cl)
        @version: 2016-07-01
        """
        # self.ensure_one()
        if inv == '':
            inv = self
        _logger.info('entrando a la funcion de toma de xml desde attachments')
        xml_attachment = ''
        attachment_id = self.env['ir.attachment'].search([
            ('res_model', '=', inv._name),
            ('res_id', '=', inv.id,),
            ('name', 'like', 'DTE_'),
            ('name', 'ilike', '.xml')])

        for att_id in attachment_id:
            _logger.info(att_id.id)
            xml_attachment = att_id.datas
            break
        return xml_attachment

    '''
    A partir de aca se realiza la toma del pdf con la factura impresa
    directamente desde libreDTE
    podria existir la posibilidad técnica de imprimir la factura
    desde odoo con otro módulo l10n_cl_dte_pdf
    o desde esta función
    obtener el PDF desde LibreDTE
    '''
    @api.multi
    def bring_pdf_ldte_new(self, foliop='', headers='', call_model=''):
        """
        Función para tomar el PDF generado en libreDTE y enviarlo a
        www.documentosonline.cl para obtener el pdf
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2017-04-09
        """
        _logger.info('bring_pdf_ldte_new.. call_model: {}'.format(call_model))
        attachment_obj = self.env['ir.attachment']
        if attachment_obj.search(
                [('res_model', '=', self._name), ('res_id', '=', self.id,),
                 ('name', 'like', 'DTE_'),
                 ('name', 'not like', 'cedible'), ('name', 'ilike', '.pdf')]):
            pass
        else:
            if call_model == 'stock.picking':
                _logger.info(
                    'contexto en bring_pdf_ldte: {}'.format(self._context))
                inv = self.env['stock.picking'].browse(
                    self._context['active_id'])
                sii_code = 52
            else:
                self.ensure_one()
                inv = self
                sii_code = inv.sii_document_class_id.sii_code
                folio = self.get_folio_current()
            try:
                if not folio:
                    folio = foliop
            except:
                folio = foliop
            _logger.info('entrada a bringpdf function')
            headers = {}
            headers['Accept'] = u'*/*'
            headers['Accept-Encoding'] = u'gzip, deflate, compress'
            headers['Connection'] = u'close'
            headers['Content-Type'] = u'multipart/form-data; boundary=33b4531\
a79be4b278de5f5688fab7701'
            # headers[
            #    'User-Agent'] = u'python-requests/2.2.1 CPython/2.7.6
            # Darwin/13.2.0'
            headers['User-Agent'] = u'python-requests/2.6.0 CPython/2.7.6 \
Linux/3.13.0-88-generic'
            headers['charset'] = u'utf-8'
            dte_xml = self.get_xml_attachment(inv)
            """
            dte_tributarias = self.company_id.dte_tributarias \
                if self.company_id.dte_tributarias else 1
            dte_cedibles = self.company_id.dte_cedibles \
                if self.company_id.dte_cedibles else 0
            """
            # print dte_xml
            # raise UserError('ver xml')
            r = requests.post('http://www.documentosonline.cl/dte/hgen/token',
                              files=dict(file_upload=base64.b64decode(dte_xml)))
            print r.json()
            # raise UserError('ver token')
            if r.status_code != 200:
                _logger.info(r.text)
                raise UserError('Error en conexión al enviar XML {}'.format(
                    r.status_code))
            # raise UserError('ver token')
            # to-do: guardar token
            headers['Connection'] = 'keep-alive'
            headers['Content-Type'] = 'application/json'
            data = {
                'params': json.loads(r.text)
            }
            r = requests.post(
                'http://www.documentosonline.cl/dte/jget', headers=headers,
                data=json.dumps(data))
            if r.status_code != 200:
                raise UserError(
                    'Error de conexión al recibir el PDF {} {}'.format(
                        r.status_code, r.text))
            print r.json()
            invoice_pdf = json.loads(r.json()['result'])['pdf']
            attachment_name = self.get_attachment_name(
                inv, call_model=str(inv._name))
            attachment_obj = self.env['ir.attachment']
            # raise UserError(inv._name, inv.id, inv._context)
            record_id = self.get_object_record_id(
                inv, call_model=str(inv._name))
            attachment_id = attachment_obj.create(
                {
                    'name': 'DTE_' + attachment_name +
                            '-' + str(folio) + '.pdf',
                    'datas': invoice_pdf,
                    'datas_fname': 'DTE_' + attachment_name +
                                   '-' + str(folio) + '.pdf',
                    'res_model': inv._name,
                    'res_id': record_id,
                    'type': 'binary'})
            _logger.info('attachment pdf')
            _logger.info(attachment_name)
            _logger.info(attachment_id)
            _logger.info(record_id)

    @api.multi
    def bring_pdf_ldte(self, foliop='', headers='', call_model='', r_id=False):
        """
        Función para tomar el PDF generado en libreDTE y adjuntarlo al registro
        @author: Daniel Blanco Martin (daniel[at]blancomartin.cl)
        @version: 2016-06-23
        Se corrige función para que no cree un nuevo PDF cada vez que se hace
        clic en botón
        y no tome PDF con cedible que se creará en botón imprimir.
        @review: Juan Plaza (jplaza@isos.cl)
        @version: 2016-09-28
        """
        _logger.info('bring_pdf_ldte NUEVA FUNCION.. call_model: {}'.format(
            call_model))
        attachment_obj = self.env['ir.attachment']
        if attachment_obj.search(
                [('res_model', '=', self._name), ('res_id', '=', self.id,),
                 ('name', 'like', 'DTE_'),
                 ('name', 'not like', 'cedible'), ('name', 'ilike', '.pdf')]):
            pass
        else:
            if call_model == 'stock.picking':
                _logger.info(
                    'contexto en bring_pdf_ldte: {}'.format(self._context))
                inv = self.env['stock.picking'].browse(r_id)
                # self._context['active_id'])
                sii_code = 52
            else:
                self.ensure_one()
                inv = self
                sii_code = inv.sii_document_class_id.sii_code
                folio = self.get_folio_current()
            try:
                if not folio:
                    folio = foliop
            except:
                folio = foliop
            emisor = self.format_vat(inv.company_id.vat)
            _logger.info('entrada a bringpdf function')
            if not headers:
                headers = self.create_headers_ldte(comp_id=self.company_id)
            # en lugar de third_party_xml, que ahora no va a existir más,
            # hay que tomar el xml del adjunto, o bien del texto
            # pero prefiero del adjunto
            # no hace falta el xml con la nueva funcion (DB: 2017-03-01)
            # dte_xml = self.get_xml_attachment(inv)
            copias_tributarias = self.company_id.dte_tributarias \
                if self.company_id.dte_tributarias else 1
            copias_cedibles = self.company_id.dte_cedibles \
                if self.company_id.dte_cedibles else 0
            # generar_pdf_request = json.dumps(
            #     {'dte': sii_code,
            #      'folio': folio,
            #      'emisor': emisor,
            #      'cedible': (copias_cedibles > 0),
            #      'compress': False,
            #      'copias_tributarias': copias_tributarias,
            #      'copias_cedibles': copias_cedibles})
            # _logger.info(generar_pdf_request)
            response_pdf = pool.urlopen(
                'GET', api_get_doc.format(
                    'pdf', sii_code, folio, emisor), headers=headers)
            # response_pdf = pool.urlopen(
            #     'GET', api_gen_pdf_new, headers=headers,
            #     body=generar_pdf_request)
            _logger.info('!!!!!_____________############# response{}'.format(
                response_pdf.data
            ))
            if response_pdf.status != 200:
                raise UserError('Error en conexión al generar: {}, {}'.format(
                    response_pdf.status, response_pdf.data))
            invoice_pdf = base64.b64encode(response_pdf.data)
            # raise UserError(inv._name)
            attachment_name = self.get_attachment_name(
                inv, call_model=str(inv._name))
            attachment_obj = self.env['ir.attachment']
            # raise UserError(inv._name, inv.id, inv._context)
            record_id = r_id or self.get_object_record_id(
                inv, call_model=str(inv._name))
            attachment_id = attachment_obj.create(
                {
                    'name': 'DTE_' + attachment_name +
                            '-' + str(folio) + '.pdf',
                    'datas': invoice_pdf,
                    'datas_fname': 'DTE_' + attachment_name +
                                   '-' + str(folio) + '.pdf',
                    'res_model': inv._name,
                    'res_id': record_id,
                    'type': 'binary'})
            _logger.info('attachment pdf')
            _logger.info(attachment_name)
            _logger.info(attachment_id)
            _logger.info(record_id)

    @staticmethod
    def remove_plurals(dte):
        dte = collections.OrderedDict(
            [('Detalle', v) if k == 'Detalles' else (k, v) for k, v in
             dte.items()])
        dte = collections.OrderedDict(
            [('Referencia', v) if k == 'Referencias' else (k, v) for k, v in
             dte.items()])
        return dte

    @staticmethod
    def product_is_exempt(line):
        """
        Función para determinar si el producto de la linea corriente es exento
        :param line:
        :return:
        """
        return line.product_id.is_exempt

    @api.multi
    def action_invoice_sent(self):
        """
        Funcion que envía el email por correo electrónico al cliente
        es la funcion original en la cual se ha modificado la plantilla
        para que en lugar de enviar un reporte envíe los attachment que cumplan
        la condición deseada. (empiezan con DTE_)
        autor de la modificacion: Daniel Blanco - daniel[at]blancomartin.cl
        @version: 2016-06-27
        (original de Odoo modificado)
        Open a window sentto compose an email, with the edi invoice template
        message loaded by default
        """
        _logger.info('controlo el proceso de envio con mi propia funcion...')
        if len(self) != 1:
            raise UserError('This option should only be used for a single id \
at a time.')
        attachment_id = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id,),
            ('name', 'like', 'DTE_')])

        atts_ids = []
        for att_id in attachment_id:
            _logger.info(att_id.id)
            atts_ids.append(att_id.id)
        _logger.info(atts_ids)

        ## hace este cambio: reemplaza el template (inicio)
        template = self.env.ref('l10n_cl_dte.email_template_edi_invoice', False)
        ## hace este cambio: reemplaza el template (fin)
        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            default_attachment_ids=atts_ids,
            mark_invoice_as_sent=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def invoice_print(self):
        """
        Funcion que reemplaza función de botón imprimir para generar PDF
        con cedible, función solo para LibreDTE.
        TODO: poner comprobación de existencia de PDF al principio
        autor: Juan Plaza - jplaza@isos.cl basado en función de Daniel Blanco
        @version: 2016-09-28
        log: Daniel Blanco: modificada para mejorar sintaxis (lint)
        """
        dte_tributarias = self.company_id.dte_tributarias \
            if self.company_id.dte_tributarias else 1
        dte_cedibles = self.company_id.dte_cedibles \
            if self.company_id.dte_cedibles else 0
        _logger.info('entrando a impresion de factura desde boton de arriba')
        self.ensure_one()
        _logger.info('entrada a invoice print function')
        headers = self.create_headers_ldte()
        dte_xml = self.get_xml_attachment()
        genera_pdf_request = json.dumps(
            {'xml': dte_xml,
             'cedible': 1 if dte_cedibles > 0 else 0,
             'copias_tributarias': dte_tributarias,
             'copias_cedibles': dte_cedibles,
             'compress': False})
        _logger.info(genera_pdf_request)
        response_pdf = pool.urlopen(
            'POST', api_gen_pdf, headers=headers,
            body=genera_pdf_request)
        if response_pdf.status != 200:
            raise UserError(_(
                'Connection error when generating: {}, {}'.format(
                    response_pdf.status, response_pdf.data)))
        invoice_pdf = base64.b64encode(response_pdf.data)
        attachment_obj = self.env['ir.attachment']
        if attachment_obj.search(
                [('res_model', '=', self._name),
                 ('res_id', '=', self.id,), ('name', 'like', 'cedible')]):
            new_attach = attachment_obj.search(
                [('res_model', '=', self._name), ('res_id', '=', self.id),
                 ('name', 'like', 'cedible')])
        else:
            new_attach = attachment_obj.create(
                {
                    'name': 'DTE_' + self.sii_document_class_id.name + '-' \
                            + self.sii_document_number + 'cedible.pdf',
                    'datas': invoice_pdf,
                    'datas_fname': 'DTE_' + self.sii_document_class_id.name \
                                   + '-' + self.sii_document_number \
                                   + 'cedible.pdf',
                    'res_model': self._name,
                    'res_id': self.id,
                    'type': 'binary'})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/saveas?model=ir.attachment&field=datas&\
filename_field=name&id={}'.format(new_attach.id), 'target': 'self'}

    @api.multi
    def action_number(self):
        self.button_reset_taxes()
        self.do_dte_send_invoice()
        res = super(Invoice, self).action_number()
        return res

    @api.multi
    def do_dte_send_invoice(self):
        cant_doc_batch = 0
        sii_code = 0
        for inv in self.with_context(lang='es_CL'):
            if inv.type[:2] == 'in':
                continue
            if inv.sii_send_ident:
                _logger.info(
                    'Track id existente. No se validará documento: {}'.format(
                        inv.sii_send_ident))
                if not inv.sii_xml_request:
                    inv.sii_result = 'NoEnviado'

                continue
            # control de DTE
            # raise UserError(inv.sii_document_class_id)
            # raise UserError(
            # inv.journal_document_class_id.sii_document_class_id.dte)
            if not inv.journal_document_class_id.sii_document_class_id.dte:
                continue
            # control de DTE
            cant_doc_batch += 1

            # aca se incorpora el grabar la referencia del pedido
            if inv.origin:
                self.record_reference(inv)
            if inv.dte_service_provider in ['EFACTURADELSUR',
                                            'EFACTURADELSUR_TEST',
                                            'LIBREDTE',
                                            'LIBREDTE_TEST']:
                # debe utilizar usuario y contraseña
                # todo: hardcodeado, pero pasar a webservices server
                dte_username = self.company_id.dte_username
                dte_password = self.company_id.dte_password

            elif inv.dte_service_provider in ['', 'NONE']:
                return

            line_number = 1
            invoice_lines = []
            global_discount = 0
            ind_exe_qty = 0
            sum_lines = 0
            MntExe = 0
            inv.sii_document_class_id = \
                inv.journal_document_class_id.sii_document_class_id
            _logger.info('doc class id: {} . sii doc class id: {}, \
sii_code:. {}'.format(
                inv.sii_document_class_id,
                inv.journal_document_class_id.sii_document_class_id,
                inv.journal_document_class_id.sii_document_class_id.sii_code))
            sii_code = inv.sii_document_class_id.sii_code
            for line in inv.invoice_line:
                try:
                    if line.product_id.is_discount:
                        global_discount += int(round(line.price_subtotal, 0))
                        global_discount = self._calc_discount_vat(
                            global_discount, sii_code)
                        sum_lines += line.price_subtotal
                        continue
                except:
                    if u'descuento' in line.product_id.name.lower() \
                            or u'discount' in line.product_id.name.lower():
                        global_discount += int(round(line.price_subtotal, 0))
                        global_discount = self._calc_discount_vat(
                            global_discount, sii_code)
                        sum_lines += line.price_subtotal
                        continue
                    else:
                        pass
                sum_lines += line.price_subtotal
                lines = collections.OrderedDict()
                lines['NroLinDet'] = line_number
                if line.product_id.default_code:
                    lines['CdgItem'] = collections.OrderedDict()
                    lines['CdgItem']['TpoCodigo'] = 'INT1'
                    lines['CdgItem']['VlrCodigo'] = line.product_id.default_code
                # todo: mejorar el cálculo de impuestos
                if self.product_is_exempt(line):
                    if sii_code in [34, 61]:
                        lines['IndExe'] = 1
                        ind_exe_qty += 1
                        MntExe += int(round(line.price_subtotal, 0))
                    elif sii_code == 33:
                        raise UserError(u'''Esta implementación no permite \
facturar items exentos en facturas afectas. Cambie el tipo de documento \
o elimine el producto exento de esta factura.
Producto que provocó el problema: {}'''.format(line.product_id.name))
                else:
                    if sii_code in [33, 61]:
                        pass
                    elif sii_code == 34:
                        raise UserError(u'''{} - El producto seleccionado no \
es exento. Deberá utilizar documento diferente a factura exenta para registrar \
la venta, o cambiar el tipo de documento de forma acorde. Producto que \
provocó el problema: {}'''.format(sii_code, line.product_id.name))
                # continua si está todo bien
                lines['NmbItem'] = self.char_replace(line.name)[:80]
                if False:
                    lines['DscItem'] = self.char_replace(line.name)[:80]
                if line.quantity == 0 and line.price_unit == 0 and \
                                sii_code in [61, 56]:
                    pass
                else:
                    lines['QtyItem'] = round(line.quantity, 2)
                    # todo: opcional lines['UnmdItem'] = line.uos_id.name[:4]
                    price_unit = (line.price_subtotal/line.quantity) / (
                        1-line.discount/100)
                    lines['PrcItem'] = round(price_unit, 0)

                if True:
                    if line.discount != 0:
                        lines['DescuentoPct'] = round(line.discount, 2)
                        lines['DescuentoMonto'] = int(
                            round((line.quantity * price_unit * line.discount)
                                  / 100, 0))
                lines['MontoItem'] = int(round(line.price_subtotal, 0))
                line_number = line_number + 1
                if inv.dte_service_provider not in [
                    'LIBREDTE', 'LIBREDTE_TEST']:
                    invoice_lines.extend([{'Detalle': lines}])
                else:
                    invoice_lines.extend([lines])
            if len(invoice_lines) == ind_exe_qty and sii_code not in [34, 61]:
                raise UserError(_('All items are VAT exempt. Type of document \
is {} does not match'.format(sii_code)))
            ref_lines = []
            adi_ref = 1
            adi_lines = []
            if len(inv.ref_document_ids) > 0:
                _logger.info(inv.ref_document_ids)
                ref_order = 1
                for ref_d in inv.ref_document_ids:
                    referencias = collections.OrderedDict()
                    referencias['NroLinRef'] = ref_order
                    referencias[
                        'TpoDocRef'] = ref_d.prefix
                    referencias['FolioRef'] = ref_d.name
                    referencias['FchRef'] = ref_d.reference_date
                    if ref_d.codref:
                        referencias['CodRef'] = ref_d.codref
                    if ref_d.reason:
                        referencias['RazonRef'] = inv.char_replace(ref_d.reason)
                    ref_order += 1
                    if inv.dte_service_provider not in [
                        'LIBREDTE', 'LIBREDTE_TEST']:
                        ref_lines.extend([{'Referencia': referencias}])
                    else:
                        ref_lines.extend([referencias])
            if inv.dte_service_provider in ['FACTURACION']:
                # leyendas adicionales
                if len(inv.additional_lejend_ids) > 0:
                    for addi in inv.additional_lejend_ids:
                        if addi.name:
                            adi_line = {}
                            adi_line['A{}'.format(adi_ref)] = addi.name
                            # adi_lines.extend([{'NodosA': adi_line}])
                            adi_lines.extend([adi_line])
                            adi_ref += 1

            folio = self.get_folio(inv)
            dte = collections.OrderedDict()
            dte1 = collections.OrderedDict()

            dte['Encabezado'] = collections.OrderedDict()
            dte['Encabezado']['IdDoc'] = collections.OrderedDict()
            dte['Encabezado']['IdDoc'][
                'TipoDTE'] = sii_code
            dte['Encabezado']['IdDoc']['Folio'] = folio
            dte['Encabezado']['IdDoc']['FchEmis'] = inv.date_invoice
            # todo: forma de pago y fecha de vencimiento - opcional
            dte['Encabezado']['IdDoc'][
                'FmaPago'] = inv.payment_term.dte_sii_code or 1
            if inv.date_due < inv.date_invoice:
                raise UserError('LA FECHA DE VENCIMIENTO'\
'NO PUEDE SER ANTERIOR A LA DE FACTURACION: Fecha de Facturación: {}, Fecha \
de Vencimiento {}'.format(inv.date_invoice, inv.date_due))
            dte['Encabezado']['IdDoc']['FchVenc'] = inv.date_due
            dte['Encabezado']['Emisor'] = collections.OrderedDict()
            dte['Encabezado']['Emisor']['RUTEmisor'] = self.format_vat(
                inv.company_id.vat)
            dte['Encabezado']['Emisor']['RznSoc'] = inv.company_id.name
            dte['Encabezado']['Emisor']['GiroEmis'] = self.char_replace(
                inv.turn_issuer.name)[:80]
            try:
                if inv.company_id.phone:
                    dte['Encabezado']['Emisor']['Telefono'] = inv.company_id.phone
            except:
                pass
            dte['Encabezado']['Emisor'][
                'CorreoEmisor'] = inv.company_id.dte_email
            dte['Encabezado']['Emisor']['Acteco'] = inv.char_replace(
                inv.turn_issuer.code)
            if inv.journal_id.point_of_sale_id.name not in ['', '---', True]:
                dte['Encabezado']['Emisor']['CdgSIISucur'] =\
                    inv.journal_id.point_of_sale_id.name
            dte['Encabezado']['Emisor']['DirOrigen'] = self.char_replace(
                inv.company_id.street)
            dte['Encabezado']['Emisor']['CmnaOrigen'] = self.char_replace(
                inv.company_id.state_id.name)
            dte['Encabezado']['Emisor']['CiudadOrigen'] = self.char_replace(
                inv.company_id.city)
            try:
                dte['Encabezado']['Emisor']['CdgVendedor'] = inv.char_replace(
                    inv.partner_id.user_id.name or 'Sin Vendedor')
            except:
                _logger.info('no se pudo leer el nombre del vendedor')
            dte['Encabezado']['Receptor'] = collections.OrderedDict()
            if not inv.partner_id.parent_id:
                dte['Encabezado']['Receptor']['RUTRecep'] = self.format_vat(
                    inv.partner_id.vat)
                dte['Encabezado']['Receptor'][
                    'RznSocRecep'] = inv.partner_id.name
                if not inv.invoice_turn.name:
                    raise UserError(_('There is no customer turn selected.'))
                dte['Encabezado']['Receptor']['GiroRecep'] = self.char_replace(
                    inv.invoice_turn.name)[:40]
                if inv.contact_data:
                    dte['Encabezado']['Receptor'][
                        'Contacto'] = self.char_replace(inv.contact_data)
            else:
                dte['Encabezado']['Receptor']['RUTRecep'] = self.format_vat(
                    inv.partner_id.parent_id.vat)
                dte['Encabezado']['Receptor'][
                    'RznSocRecep'] = inv.partner_id.parent_id.name
                if not inv.invoice_turn.name:
                    raise UserError(_('There is no customer turn selected.'))
                dte['Encabezado']['Receptor']['GiroRecep'] = self.char_replace(
                    inv.invoice_turn.name)[:40]
                if inv.contact_data:
                    dte['Encabezado']['Receptor'][
                        'Contacto'] = self.char_replace(inv.contact_data)
                else:
                    try:
                        dte['Encabezado']['Receptor']['Contacto'] = \
                            self.char_replace('At: {} Tel: {}'.format(
                                inv.partner_id.name or '',
                                inv.partner_id.phone or ''))[:80]
                    except:
                        _logger.info('No pudo leer información de contacto')
            dte['Encabezado']['Receptor']['DirRecep'] = self.char_replace(
                inv.partner_id.street)
            # todo: revisar comuna: "false"
            if inv.partner_id.state_id.name == False or \
                            inv.partner_id.city == False:
                raise UserError(
                    'No se puede continuar: Revisar comuna y ciudad')
            dte['Encabezado']['Receptor']['CmnaRecep'] = self.char_replace(
                inv.partner_id.state_id.name)
            dte['Encabezado']['Receptor']['CiudadRecep'] = self.char_replace(
                inv.partner_id.city)
            dte['Encabezado']['Totales'] = collections.OrderedDict()
            MntTotal = int(round(inv.amount_total, 0))
            if True:
                if sii_code in [34, 61] and MntExe > 0:
                    dte['Encabezado']['Totales']['MntExe'] = MntExe
                    # int(round(
                    #    inv.amount_total, 0))
                elif sii_code in [32, 61] and MntExe == 0:
                    dte['Encabezado']['Totales']['MntNeto'] = int(round(
                        inv.amount_untaxed, 0))
                    try:
                        dte['Encabezado']['Totales']['TasaIVA'] = int(round(
                            (inv.amount_total / inv.amount_untaxed - 1) * 100,
                            0))
                        # TODO: si este valor es distinto a 19%, hay un error
                    except:
                        _logger.info('calculo de iva total por excepcion')
                        dte['Encabezado']['Totales']['TasaIVA'] = 19

                    dte['Encabezado']['Totales']['IVA'] = MntTotal - dte[
                        'Encabezado']['Totales']['MntNeto']
                dte['Encabezado']['Totales']['MntTotal'] = MntTotal
                # dte['item'] = invoice_lines
                dte['Detalles'] = invoice_lines
                _logger.info(json.dumps(dte))
                if len(ref_lines) > 0:
                    # dte['Referencias'].extend(ref_lines)
                    dte['Referencias'] = ref_lines
            else:
                if sii_code == 34:
                    dte['Encabezado']['Totales']['MntExe'] = MntTotal
                dte['Detalles'] = invoice_lines
                if len(ref_lines) > 0:
                    dte['Referencias'] = ref_lines
            if global_discount != 0:
                dte['DscRcgGlobal'] = collections.OrderedDict()
                dte['DscRcgGlobal']['NroLinDR'] = 1
                dte['DscRcgGlobal'][
                    'TpoMov'] = 'D' if global_discount < 0 else 'Receptor'
                # dte['DscRcgGlobal']['GlosaDR'] =
                dte['DscRcgGlobal']['TpoValor'] = '$'
                dte['DscRcgGlobal']['ValorDR'] = round(abs(global_discount))
                if sii_code in [34, 61] and MntExe > 0:
                    dte['DscRcgGlobal']['IndExeDR'] = 1

            if inv.dte_service_provider in ['LIBREDTE', 'LIBREDTE_TEST']:
                dte = self.remove_plurals(dte)
                _logger.info(json.dumps(dte))
                # raise UserError('veadte antes de quitar totales')
                # ademas le quito los totales
                _logger.info('antes de quitar totales: {}'.format(
                    dte['Encabezado']['Totales']))
                del dte['Encabezado']['Totales']
            doc_id_number = "F{}T{}".format(
                folio, sii_code)
            doc_id = '<Documento ID="{}">'.format(doc_id_number)
            # TODO: si es sii, inserto el timbre

            dte1['Documento ID'] = dte
            xml = dicttoxml.dicttoxml(
                dte1, root=False, attr_type=False).replace(
                    '<item>', '').replace('</item>', '')
            # control dte
            _logger.info(dte)
            _logger.info(json.dumps(dte))
            # raise UserError('verdte.....')
            root = etree.XML(xml)

            xml_pret = etree.tostring(root, pretty_print=True).replace(
'<Documento_ID>', doc_id).replace('</Documento_ID>', '</Documento>')
            if len(adi_lines) > 0:
                item_function = lambda x: 'NodosA'
                xml_pret = xml_pret[:-1] + parseString(dicttoxml.dicttoxml({
                    'Adicional': adi_lines},
                    root=False,
                    attr_type=False,
                    item_func=item_function)).toprettyxml().replace(
                    '<?xml version="1.0" ?>', '')
            xml_pret = self.create_template_doc(xml_pret)
            if inv.dte_service_provider in [
                'EFACTURADELSUR', 'EFACTURADELSUR_TEST']:
                enviar = 'true' if self.dte_service_provider == \
                                   'EFACTURADELSUR' else 'false'
                envelope_efact = '''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
<soap12:Body>
<PonerDTE xmlns="https://www.efacturadelsur.cl">
<usuario>{0}</usuario>
<contrasena>{1}</contrasena>
<xml><![CDATA[{2}]]></xml>
<enviar>{3}</enviar>
</PonerDTE>
</soap12:Body>
</soap12:Envelope>'''.format(dte_username, dte_password, xml_pret, enviar)
                _logger.info(inv.sii_xml_request)
                inv.sii_xml_request = envelope_efact
                inv.sii_result = 'NoEnviado'
                _logger.info('OPCION DTE: ({})'.format(str(
                    inv.dte_service_provider)).lower())
            elif inv.dte_service_provider in [
                'LIBREDTE', 'LIBREDTE_TEST']:
                _logger.info('username: {}, password: {}'.format(
                    self.company_id.dte_username, self.company_id.dte_password))
                headers = self.create_headers_ldte()
                _logger.info('Headers:')
                _logger.info(headers)
                _logger.info('DTE enviado:')
                _logger.info(dte)
                _logger.info('DTE enviado (json)')
                _logger.info(json.dumps(dte))
                # corte para debug
                response_j = self.enviar_ldte(inv, dte, headers)
                inv.write(
                    {
                        'sii_result': 'Enviado',
                        'sii_send_ident': response_j['track_id']})
                _logger.info('se guardó xml con la factura')
                self.set_folio(inv, response_j['folio'])
            elif inv.dte_service_provider == 'FACTURACION':
                envelope_efact = '''<?xml version="1.0" encoding="ISO-8859-1"?>
{}'''.format(self.convert_encoding(xml_pret, 'ISO-8859-1'))
                inv.sii_xml_request = envelope_efact
            else:
                _logger.info('NO HUBO NINGUNA OPCION DTE VALIDA ({})'.format(
                    inv.dte_service_provider))
                raise UserError('None DTE Provider Option')


class InvoiceReference(models.Model):
    _name = "invoice.reference"
    invoice_id = fields.Many2one(
        'account.invoice', 'Invoice',
        required=True, ondelete='cascade', select=True, readonly=True)
    parent_type = fields.Char('Parent Type')
    name = fields.Char(
        'Number', required=True, readonly=False,
        help='Number (folio) of reference')
    sii_document_class_id = fields.Many2one(
        'sii.document_class', 'Ref Document',
        required=True, ondelete='cascade')
    reference_date = fields.Date(
        'Ref. Date', required=True, help="FchRef")
    prefix = fields.Char(
        'Prefix', compute='_compute_ref', readonly=True,
        help="<TipoDocRef>. Should be SII Code for docs, or this prefix if \
does not exist.")
    codref = fields.Char('Cod.Ref', readonly=True, help="<CodRef>, Only \
needed for credit notes and debit notes.")
    reason = fields.Char('Reason', help="Related to <RazonRef>.")

    @api.multi
    @api.depends('sii_document_class_id')
    def _compute_ref(self):
        for i in self:
            if not i.sii_document_class_id.sii_code \
                    and i.sii_document_class_id.doc_code_prefix:
                _logger.info('pasa por la funcion compute_ref: {}|{}|{}'.format(
                    i.id, i.name, i.sii_document_class_id.doc_code_prefix))
                i.prefix = i.sii_document_class_id.doc_code_prefix[:3]
            else:
                i.prefix = i.sii_document_class_id.sii_code
