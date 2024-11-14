#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = ['Manuel Hurtado', 'Alfredo Mejia', 'Armando Jimenez']
__copyright__ = 'Copyright (c) 2024 FINKOK S.A. de C.V., Calculadora_Soporte'
__credits__ = ['Manuel Hurtado', 'Alfredo Mejia', 'Armando Jimenez']
__licence__ = 'Privativo'
__version__ = '2.1'
__maintainer__ = ['Manuel Hurtado', 'Alfredo Mejia', 'Armando Jimenez']
__email__ = ['ljimenez@finkok.com', 'soporte@finkok.com']
__status__ = 'Development'

from datetime import datetime, timedelta
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style
import math
import requests
from decimal import ROUND_HALF_UP
from sig import timbrar
from cce import realizar_calculos_comercio_exterior
from cfdi import realizar_calculos_generales
from pagos import realizar_calculos_pago
from retencionesP import calcular_retenciones
from nomina import condicion_nomina
# Cargar el archivo XML
xml_string = open(
    "prueba.xml", "rb").read()
xml_etree = etree.fromstring(xml_string)
namespaces = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20',
    'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
    'nomina': 'http://www.sat.gob.mx/nomina12',
    'cartaporte31': 'http://www.sat.gob.mx/CartaPorte31',
    's0': 'apps.services.soap.core.views'
}

tipo_comprobante = xml_etree.get("TipoDeComprobante")
if tipo_comprobante:
    tipo = tipo_comprobante[0].upper()
    print(Fore.CYAN +
          f"Detectado comprobante de tipo {tipo}." + Style.RESET_ALL)

    if tipo == "T":
        if xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces):
            realizar_calculos_comercio_exterior()
        else:
            print(
                Fore.RED + "Comprobante de tipo T sin complemento de comercio exterior." + Style.RESET_ALL)

    elif tipo in ["I", "E"]:
        if xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces) and xml_etree.xpath(".//cartaporte31:CartaPorte", namespaces=namespaces):
            realizar_calculos_generales()
            realizar_calculos_comercio_exterior()
        elif xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces):
            realizar_calculos_comercio_exterior()
            realizar_calculos_generales()
        else:
            realizar_calculos_generales()
    elif tipo == 'P':
        realizar_calculos_pago()
        calcular_retenciones()
    elif tipo == 'N':
        condicion_nomina(namespaces)
        
        print
    else:
        print(Fore.RED + "Tipo de comprobante no identificado." + Style.RESET_ALL)
else:
    print(Fore.RED + "No se encontró el tipo de comprobante en el XML." + Style.RESET_ALL)
