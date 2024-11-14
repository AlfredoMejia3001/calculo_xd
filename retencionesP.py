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

def calcular_retenciones():
    # Verificar si existen retenciones en el comprobante
    retenciones_exist = xml_etree.xpath(
        ".//pago20:RetencionDR", namespaces=namespaces)

    if not retenciones_exist:
        print(
            Fore.CYAN + "No se encontraron retenciones en el comprobante." + Style.RESET_ALL)
        return  # No hay retenciones, no se realizan cálculos

    print(Fore.GREEN + "-------------- Cálculos Retenciones --------------" + Style.RESET_ALL)

    BaseRetencionDR = [Decimal(x) for x in xml_etree.xpath(
        ".//pago20:RetencionDR/@BaseDR", namespaces=namespaces)]
    TasaOCuotaRetencionDR = [Decimal(x) for x in xml_etree.xpath(
        ".//pago20:RetencionDR/@TasaOCuotaDR", namespaces=namespaces)]
    ImporteRetencionDR_calculado = [round(
        base * tasa, 2) for base, tasa in zip(BaseRetencionDR, TasaOCuotaRetencionDR)]
    ImporteRetencionDR_xml = [round(Decimal(x), 2) for x in xml_etree.xpath(
        ".//pago20:RetencionDR/@ImporteDR", namespaces=namespaces)]

    for idx, (base, tasa, imp_calc, imp_xml) in enumerate(zip(BaseRetencionDR, TasaOCuotaRetencionDR, ImporteRetencionDR_calculado, ImporteRetencionDR_xml)):
        if imp_calc != imp_xml:
            print(
                Fore.RED + f"\nDiscrepancia detectada en la RetencionDR {idx + 1}:")
            print(
                Fore.YELLOW + f"Importe calculado: {imp_calc}, Importe en XML: {imp_xml}" + Style.RESET_ALL)
            node1= xml_etree.xpath('.//pago20:RetencionDR', namespaces=namespaces)
            node1.set("ImporteDR", imp_calc)
    print(Fore.GREEN + "----------------------------------------------\n" + Style.RESET_ALL)
    with open("cfdi_modificado.xml", "wb") as f:
        f.write(etree.tostring(xml_etree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8'))
    print("El archivo XML modificado ha sido guardado como 'cfdi_modificado.xml'.")
    xml = "cfdi_modificado.xml"
    timbrar(xml)