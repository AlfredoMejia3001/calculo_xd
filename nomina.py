
from datetime import datetime, timedelta
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style
import math
import requests
from decimal import ROUND_HALF_UP



# Cargar el archivo XML
xml_string = open(
    "prueba.xml", "rb").read()
xml_etree = etree.fromstring(xml_string)
namespaces = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20',
    'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
    'nomina12': 'http://www.sat.gob.mx/nomina12',
    's0': 'apps.services.soap.core.views'
}
fecha = datetime.now()
fecha = fecha.strftime('%Y-%m-%dT%H:%M:%S')
rfc="EKU9003173C9"
name="ESCUELA KEMPER URGATE"
regi="601"
xml_etree.set("Fecha", fecha)
xml_etree.set("NoCertificado", '30001000000500003416')
nodo = xml_etree.xpath(".//cfdi:Emisor", namespaces=namespaces)
if nodo:  # Check if the list is not empty
    emisor = nodo[0]  # Get the first matching node
    emisor.set('Rfc', str(rfc))
    emisor.set('Nombre', str(name))
    emisor.set('RegimenFiscal', str(regi))



def redondeo(valor):
    # Convertir el valor a cadena con dos decimales
    valor_str = f"{valor:.5f}"
    parte_entera, parte_decimal = valor_str.split('.')

    # Aplicar la Regla 1 y 2
    ultima_cifra = int(parte_decimal[2])  # Obtener la tercera cifra decimal
    penultima_cifra = int(parte_decimal[1])  # Obtener la segunda cifra decimal

    if ultima_cifra < 5:
        # Regla 1: Si la última cifra es menor que 5, no modificar
        return Decimal(parte_entera + '.' + parte_decimal[:2])

    if ultima_cifra > 5:
        # Regla 2: Si la última cifra es mayor que 5, redondear al alza
        return Decimal(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    # Reglas 3 y 4: Si la última cifra es 5
    if penultima_cifra % 2 == 0:
        # Regla 3: Si el penúltimo número es par, truncar
        return Decimal(parte_entera + '.' + parte_decimal[:2])
    else:
        # Regla 4: Si el penúltimo número es impar, redondear al alza
        return Decimal(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))



def valor_unitario():
    valor_unitario = xml_etree.xpath("//cfdi:Conceptos/cfdi:Concepto/@ValorUnitario", namespaces=namespaces)
    total_otros_pagos = xml_etree.xpath("//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    total_persepciones = xml_etree.xpath("//nomina12:Nomina/@TotalPercepciones", namespaces=namespaces)
    
    tot_pag = float(total_otros_pagos[0])
    tot_per = float(total_persepciones[0])

    suma= tot_pag + tot_per

    if suma != float(valor_unitario[0]):
        print("no son iguales val uni")
    else:
        print("si son iguales val uni")
        
    print("suma:",suma)


def importe():
    imp = xml_etree.xpath("//cfdi:Conceptos/cfdi:Concepto/@Importe", namespaces=namespaces)
    total_otros_pagos = xml_etree.xpath("//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    total_persepciones = xml_etree.xpath("//nomina12:Nomina/@TotalPercepciones", namespaces=namespaces)
    
    tot_pag = float(total_otros_pagos[0])
    tot_per = float(total_persepciones[0])

    suma= tot_pag + tot_per

    if suma != float(imp[0]):
        print("no son iguales")
    else:
        print("si son iguales")
        
    print("suma:",suma)


def descuento ():
    desc = xml_etree.xpath("//cfdi:Conceptos/cfdi:Concepto/@Descuento", namespaces=namespaces)
    total_deduciones = xml_etree.xpath("//nomina12:Nomina/@TotalDeducciones", namespaces=namespaces)
    des = str(desc[0])
    total_deducione = str(total_deduciones[0])
    if des != total_deducione:
        print("El descuento no coincide")
    else:
        print("Todo esta correcto")


def total_percepciones():
    total_sueldos = 0
    total_separacion_indemnizacion = 0
    total_jubilacion_pension_retiro=0
    if total_sueldos and total_jubilacion_pension_retiro and total_separacion_indemnizacion :

        suma=total_separacion_indemnizacion + total_sueldos + total_jubilacion_pension_retiro
    
    elif total_sueldos and total_separacion_indemnizacion:

        suma=total_sueldos + total_separacion_indemnizacion
        