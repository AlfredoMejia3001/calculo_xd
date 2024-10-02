from collections import defaultdict
from decimal import Decimal
from sys import orig_argv
from lxml import etree
from colorama import Fore, Style

Token= "a0d9d68a166b6565e59872885d9bb2927abd03f00acdcadded548b96684dc93d"
URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/{{fecha_ini}}/{{fecha_fin}}?token={Token}}"


# Cargar el archivo XML
xml_string = open(
    "/home/soporte-residentes/Documentos/Tareas_Alfredo/cfdi.xml", "rb").read()
xml_etree = etree.fromstring(xml_string)

namespaces = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20',
    'cce20': 'http://www.sat.gob.mx/ComercioExterior20'
}


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
    xml_importes = [round(float(imp), 2) for imp in xml_etree.xpath(
        ".//cfdi:Concepto/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@Importe", namespaces=namespaces)]

    for clave, base_calc, importe_calc, importe_xml in zip(claves_prod_serv, Base, importeT, xml_importes):
        if importe_calc != importe_xml:
            print(
                Fore.CYAN + f"\nDiscrepancia detectada en el producto con ClaveProdServ: " +
                Fore.RED + f"{clave}" + Fore.BLUE +
                f"\nBase calculada: " + Fore.GREEN + f"{base_calc}" + Fore.BLUE +
                f", Importe calculado: " + Fore.GREEN + f"{importe_calc}" + Fore.BLUE +
                f", Importe en XML: " + Fore.RED +
                f"{importe_xml}" + Style.RESET_ALL
            )

    subtotal = round(sum(Base), 2)
    total_traslados = round(sum(importeT), 2)
    xml_subtotal = float(xml_etree.get("SubTotal"))
    xml_total = float(xml_etree.get("Total"))

    # Sumar los importes de las retenciones si existen
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

    # Mostrar las discrepancias entre el total y el subtotal
    if round(subtotal, 2) != round(xml_subtotal, 2):
        print(
            Fore.RED + f"Discrepancia en el subtotal: Calculado: {subtotal}, XML: {xml_subtotal}" + Style.RESET_ALL)
    if round(total_calculado, 2) != round(xml_total, 2):
        print(
            Fore.RED + f"Discrepancia en el total: Calculado: {total_calculado}, XML: {xml_total}" + Style.RESET_ALL)

    # Mostrar la suma de impuestos (traslados y retenciones)
    print(Fore.GREEN +
          f"Suma total de impuestos trasladados: {total_traslados}" + Style.RESET_ALL)
    print(Fore.GREEN +
          f"Suma total de retenciones: {total_retenciones}" + Style.RESET_ALL)
    print(Fore.GREEN +
          f"Suma total de impuestos (traslados - retenciones): {total_calculado}" + Style.RESET_ALL)

    print(Fore.GREEN + "----------------------------------------------\n" + Style.RESET_ALL)


def realizar_calculos_pago():
    print(Fore.GREEN + "\n-------------- Cálculos Pago ------------------" + Style.RESET_ALL)

    BaseDR = [Decimal(x) for x in xml_etree.xpath(
        ".//pago20:TrasladoDR/@BaseDR", namespaces=namespaces)]
    TasaOCuotaDR = [Decimal(x) for x in xml_etree.xpath(
        ".//pago20:TrasladoDR/@TasaOCuotaDR", namespaces=namespaces)]
    ImporteDR_calculado = [round(base * tasa, 2)
                           for base, tasa in zip(BaseDR, TasaOCuotaDR)]
    ImporteDR_xml = [round(Decimal(x), 2) for x in xml_etree.xpath(
        ".//pago20:TrasladoDR/@ImporteDR", namespaces=namespaces)]

    for idx, (base, tasa, imp_calc, imp_xml) in enumerate(zip(BaseDR, TasaOCuotaDR, ImporteDR_calculado, ImporteDR_xml)):
        if imp_calc != imp_xml:
            print(Fore.BLUE +
                  f"\nDiscrepancia detectada en el TrasladoDR {idx + 1}:")
            print(
                Fore.YELLOW + f"Importe calculado: {imp_calc}, Importe en XML: {imp_xml}" + Style.RESET_ALL)

    total_pago = Decimal(xml_etree.xpath(
        ".//pago20:Totales/@MontoTotalPagos", namespaces=namespaces)[0])
    print(Fore.GREEN +
          f"Total de pagos según XML: {total_pago}" + Style.RESET_ALL)
    print(Fore.GREEN + "-----------------------------------------------\n" + Style.RESET_ALL)


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

    print(Fore.GREEN + "----------------------------------------------\n" + Style.RESET_ALL)


def realizar_calculos_comercio_exterior():
    print("calculos ")


# Verificar el tipo de comprobante y proceder
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
        realizar_calculos_generales()

    elif tipo == 'P':
        realizar_calculos_pago()
        calcular_retenciones()

    else:
        print(Fore.RED + "Tipo de comprobante no identificado." + Style.RESET_ALL)
else:
    print(Fore.RED + "No se encontró el tipo de comprobante en el XML." + Style.RESET_ALL)