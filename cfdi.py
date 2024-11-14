from datetime import datetime, timedelta
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style
import math
import requests
from decimal import ROUND_HALF_UP
from sig import timbrar

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


fecha = datetime.now()
fecha = fecha.strftime('%Y-%m-%dT%H:%M:%S')
rfc="EKU9003173C9"
name="ESCUELA KEMPER URGATE"
regi="601"
xml_etree.set("Fecha", fecha)
xml_etree.set("NoCertificado", '30001000000500003416')
nodo = xml_etree.xpath(".//cfdi:Emisor", namespaces=namespaces)

if nodo:  
    emisor = nodo[0]  
    emisor.set('Rfc', str(rfc))
    emisor.set('Nombre', str(name))
    emisor.set('RegimenFiscal', str(regi))


def truncar(valor, decimales=2):
    factor = Decimal(10) ** decimales
    return math.trunc(Decimal(valor) * factor) / factor


def redondeo(valor):
    valor_str = f"{valor:.5f}"
    parte_entera, parte_decimal = valor_str.split('.')

    
    ultima_cifra = int(parte_decimal[2])  
    penultima_cifra = int(parte_decimal[1])  

    if ultima_cifra < 5:
        return Decimal(parte_entera + '.' + parte_decimal[:2])

    if ultima_cifra > 5:
        return Decimal(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    if penultima_cifra % 2 == 0:
        return Decimal(parte_entera + '.' + parte_decimal[:2])
    else:
        return Decimal(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def realizar_calculos_generales():
    print(Fore.GREEN + "-------------- Cálculos Generales --------------" + Style.RESET_ALL)

    claves_prod_serv = xml_etree.xpath(
        ".//cfdi:Concepto/@ClaveProdServ", namespaces=namespaces)
    ValorUnitario = [float(x) for x in xml_etree.xpath(
        ".//cfdi:Concepto/@ValorUnitario", namespaces=namespaces)]
    Cantidad = [float(x) for x in xml_etree.xpath(
        ".//cfdi:Concepto/@Cantidad", namespaces=namespaces)]
    Base = [round(x * y, 2) for x, y in zip(ValorUnitario, Cantidad)]

    BaseT = [float(x) for x in xml_etree.xpath(
        ".//cfdi:Concepto/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@Base", namespaces=namespaces)]
    TasaOCuota = [float(x) for x in xml_etree.xpath(
        ".//cfdi:Concepto/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@TasaOCuota", namespaces=namespaces)]
    importeT = [round(x * y, 2) for x, y in zip(BaseT, TasaOCuota)]
    xml_importes = [(float(imp)) for imp in xml_etree.xpath(
        ".//cfdi:Concepto/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@Importe", namespaces=namespaces)]
    for clave, base_calc, importe_calc, importe_xml, nodo in zip(claves_prod_serv, Base, importeT, xml_importes, xml_etree.xpath(".//cfdi:Concepto/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", namespaces=namespaces)):
        if importe_calc != importe_xml:
            print(
                Fore.CYAN + f"\nDiscrepancia detectada en el producto con ClaveProdServ: " +
                Fore.RED + f"{clave}" + Fore.BLUE +
                f"\nBase calculada: " + Fore.GREEN + f"{base_calc}" + Fore.BLUE +
                f", Importe calculado: " + Fore.GREEN + f"{importe_calc}" + Fore.BLUE +
                f", Importe en XML: " + Fore.RED +
                f"{importe_xml}" + Style.RESET_ALL
            )
            nodo.set('Importe', str(importe_calc))

    subtotal = round(sum(Base), 2)
    total_traslados = round(sum(importeT), 2)
    xml_subtotal = float(xml_etree.get("SubTotal"))
    xml_total = float(xml_etree.get("Total"))


    retenciones_exist = xml_etree.xpath(
        ".//cfdi:Concepto/cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion", namespaces=namespaces)

    if retenciones_exist:
        importe_retenciones = xml_etree.xpath(
            ".//cfdi:Concepto/cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion/@Importe", namespaces=namespaces)
        total_retenciones = round(
            sum([float(x) for x in importe_retenciones]), 2)
    else:
        total_retenciones = 0.0

    total_calculado = round(subtotal + total_traslados - total_retenciones, 2)

    if round(subtotal, 2) != round(xml_subtotal, 2):
        print(
            Fore.RED + f"Discrepancia en el subtotal: Calculado: {subtotal}, XML: {xml_subtotal}" + Style.RESET_ALL)
        xml_etree.set('SubTotal', str(subtotal))
    if round(total_calculado, 2) != round(xml_total, 2):
        print(
            Fore.RED + f"Discrepancia en el total: Calculado: {total_calculado}, XML: {xml_total}" + Style.RESET_ALL)
        xml_etree.set('Total', str(total_calculado))
    
    tras = xml_etree.xpath('.//cfdi:Impuestos/@TotalImpuestosTrasladados', namespaces=namespaces)
    tras1 = xml_etree.xpath('.//cfdi:Impuestos', namespaces=namespaces)

  
    trasla = str(total_traslados)

    if total_traslados != tras:
        print("Discrepancia en TotalImpuestosTrasladados", trasla)
        last_element = tras1[-1]
        last_element.set('TotalImpuestosTrasladados', trasla)
     
    print(Fore.GREEN +
          f"Suma total de impuestos trasladados: {total_traslados}" + Style.RESET_ALL)
    print(Fore.GREEN +
          f"Suma total de retenciones: {total_retenciones}" + Style.RESET_ALL)
    print(Fore.GREEN +
          f"Suma total de impuestos (traslados - retenciones): {total_calculado}" + Style.RESET_ALL)
    print(Fore.GREEN + "----------------------------------------------\n" + Style.RESET_ALL)

    with open("cfdi_modificado.xml", "wb") as f:
        f.write(etree.tostring(xml_etree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8'))
    print("El archivo XML modificado ha sido guardado como 'cfdi_modificado.xml'.")
    xml = "cfdi_modificado.xml"
    timbrar(xml)
    xml_response = open(
        "response.xml", "rb").read()
    xml_res = etree.fromstring(xml_response)
    try:
        print("Codigo de error:", xml_res.xpath(".//s0:CodigoError", namespaces=namespaces)[0].text)
    except IndexError:
        pass
    
    try:
        print("Mensaje de error:", xml_res.xpath(".//s0:MensajeIncidencia", namespaces=namespaces)[0].text)
    except IndexError:
        pass
    
    try:
        print("Code Estatus:", xml_res.xpath(".//s0:CodEstatus", namespaces=namespaces)[0].text)
    except IndexError:
        pass

