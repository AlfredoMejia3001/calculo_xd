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

# Cargar el archivo XML
#xml_string = open("prueba.xml", "rb").read()
#xml_etree = etree.fromstring(xml_string)



def truncar(valor, decimales=2):
    factor = Decimal(10) ** decimales
    return math.trunc(Decimal(valor) * factor) / factor


def obtener_tipo_cambio_api():
    token = "a0d9d68a166b6565e59872885d9bb2927abd03f00acdcadded548b96684dc93d"
    url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/{fecha_ini}/{fecha_fin}?token={token}"

    today = datetime.now()
    format = today.strftime('%Y-%m-%d')

    # Inicializar la fecha de inicio
    fecha_ini = format

    # Intentar hasta tres días atrás si la respuesta está vacía
    for i in range(4):  # Del día actual hasta tres días antes
        fecha_ini = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        fecha_fin = format  # Fecha actual

        # Formatear la URL
        formatted_url = url.format(
            fecha_ini=fecha_ini, fecha_fin=fecha_fin, token=token)

        # Realizar la solicitud GET
        response = requests.get(formatted_url)

        # Verificar el estado de la respuesta
        if response.status_code == 200:
            try:
                data = response.json()  # Convertir la respuesta a JSON

                # Verificar que las claves 'bmx' y 'series' existan en el JSON
                if 'bmx' in data and 'series' in data['bmx']:
                    serie = data['bmx']['series'][0]

                    # Verificar si hay datos dentro de 'datos'
                    if 'datos' in serie and serie['datos']:
                        tipo_cambio_api = float(serie['datos'][0]['dato'])
                        print(f"Tipo de cambio API Banxico: {tipo_cambio_api}")
                        return tipo_cambio_api
                    else:
                        print(
                            f"No hay datos disponibles para la fecha: {fecha_ini}")
                else:
                    print(
                        "Formato inesperado en la respuesta de la API. Revisa la estructura.")
            except ValueError as e:
                print(f"Error al decodificar JSON: {e}")
        else:
            print(
                f"Error en la solicitud: {response.status_code} - {response.text}")
    return None


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

def verificar_clave_prod_serv(clave):
    url = f"https://web-production-a45c8.up.railway.app/sat/claveprodserv/?search='{clave}'"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data['count'] > 0:
            return data['results'][0]['clave']
    return None

def realizar_calculos_generales(xml_etree):
    print(" -----Cálculos Generales -----\n")
    namespaces = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'pago20': 'http://www.sat.gob.mx/Pagos20',
        'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
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
    clave1 = str(claves_prod_serv[0])
    clave_encontrada = verificar_clave_prod_serv(clave1)

    if clave_encontrada:
        print(f"ClaveProdServ encontrada en el catálogo: {clave_encontrada}\n")
    else:
        print(
            f"ClaveProdServ {clave1} no encontrada en el catálogo.\n" )
    
    for clave, base_calc, importe_calc, importe_xml, nodo in zip(claves_prod_serv, Base, importeT, xml_importes, xml_etree.xpath(".//cfdi:Concepto/cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", namespaces=namespaces)):
        if importe_calc != importe_xml:
            print(
                f"\nDiscrepancia detectada en el producto con ClaveProdServ: " +f"{clave}\n" 
                f"\nBase calculada: "  f"{base_calc}\n"
                f", Importe calculado: "f"{importe_calc}\n" 
                f", Importe en XML: "
                f"{importe_xml}\n" 
            )
            # Actualiza el atributo Importe en el nodo correspondiente
            # Actualiza el Importe con el valor calculado
            nodo.set('Importe', str(importe_calc))

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
            f"Discrepancia en el subtotal: Calculado: {subtotal}, XML: {xml_subtotal}\n")
        xml_etree.set('SubTotal', str(subtotal))
    if round(total_calculado, 2) != round(xml_total, 2):
        print(
           f"Discrepancia en el total: Calculado: {total_calculado}, XML: {xml_total}")
        xml_etree.set('Total', str(total_calculado))
    # Mostrar la suma de impuestos (traslados y retenciones)
    
    tras = xml_etree.xpath('.//cfdi:Impuestos/@TotalImpuestosTrasladados', namespaces=namespaces)
    tras1 = xml_etree.xpath('.//cfdi:Impuestos', namespaces=namespaces)

  
    trasla = str(total_traslados)

    if total_traslados != tras:
        print("Discrepancia en TotalImpuestosTrasladados", trasla)
        last_element = tras1[-1]
        last_element.set('TotalImpuestosTrasladados', trasla)
     
    print(
          f"Suma total de impuestos trasladados: {total_traslados}" )
        
        
    print(
          f"Suma total de retenciones: {total_retenciones}")
    print(
          f"Suma total de impuestos (traslados - retenciones): {total_calculado}" )

    print( "----------------------------------------------\n")

    # Guardar el XML modificado en un nuevo archivo
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


def realizar_calculos_pago(xml_etree):
    print(Fore.GREEN + "-------------- Cálculos de Pagos --------------" + Style.RESET_ALL)
    namespaces = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'pago20': 'http://www.sat.gob.mx/Pagos20',
        'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
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


    BaseDR = [Decimal(x) for x in xml_etree.xpath(
        ".//pago20:Pagos/pago20:Pago/pago20:DoctoRelacionado/pago20:ImpuestosDR/pago20:TrasladosDR/pago20:TrasladoDR/@BaseDR", namespaces=namespaces)]
    TasaOCuotaDR = xml_etree.xpath(
        ".//pago20:Pagos/pago20:Pago/pago20:DoctoRelacionado/pago20:ImpuestosDR/pago20:TrasladosDR/pago20:TrasladoDR/@TasaOCuotaDR", namespaces=namespaces)
    ImporteDR_xml = xml_etree.xpath(
        ".//pago20:Pagos/pago20:Pago/pago20:DoctoRelacionado/pago20:ImpuestosDR/pago20:TrasladosDR/pago20:TrasladoDR/@ImporteDR", namespaces=namespaces)
    TipoFactorDR = xml_etree.xpath(
        ".//pago20:Pagos/pago20:Pago/pago20:DoctoRelacionado/pago20:ImpuestosDR/pago20:TrasladosDR/pago20:TrasladoDR/@TipoFactorDR", namespaces=namespaces)

    ImporteDR_calculado = []
    for idx, tipo_factor in enumerate(TipoFactorDR):
        print(Fore.YELLOW +
              f"\n------------ TrasladoDR {idx + 1} ------------" + Style.RESET_ALL)
        print(Fore.CYAN + f"BaseDR: {BaseDR[idx]}" + Style.RESET_ALL)

        if tipo_factor == 'Exento':
            print(Fore.CYAN +
                  f"TipoFactorDR: {tipo_factor} (Exento)" + Style.RESET_ALL)
            if idx < len(TasaOCuotaDR) or idx < len(ImporteDR_xml):
                print(
                    Fore.RED + f"Error: TrasladoDR {idx + 1} con TipoFactorDR 'Exento' no debe tener TasaOCuotaDR ni ImporteDR." + Style.RESET_ALL)
            ImporteDR_calculado.append(Decimal('0.00'))

        elif tipo_factor == 'Tasa':
            if idx < len(TasaOCuotaDR):
                tasa = Decimal(TasaOCuotaDR[idx])
                base = BaseDR[idx]
                imp_calc = round(base * tasa, 2)
                ImporteDR_calculado.append(imp_calc)
                print(Fore.CYAN + f"TasaOCuotaDR: {tasa}" + Style.RESET_ALL)
                print(Fore.CYAN +
                      f"Importe calculado: {imp_calc}" + Style.RESET_ALL)
            else:
                print(
                    Fore.RED + f"Error: No se encontró TasaOCuotaDR para el TrasladoDR {idx + 1}" + Style.RESET_ALL)
                ImporteDR_calculado.append(Decimal('0.00'))

        else:
            print(
                Fore.RED + f"Error: TipoFactorDR {idx + 1} no válido." + Style.RESET_ALL)

    # Convertir ImporteDR_xml a Decimal y redondear
    ImporteDR_xml = [round(Decimal(x), 2) if x else Decimal('0.00')
                     for x in ImporteDR_xml]

    # Comparar ImporteDR calculado con ImporteDR del XML
    for idx, (imp_calc, imp_xml) in enumerate(zip(ImporteDR_calculado, ImporteDR_xml)):
        print(Fore.CYAN + f"ImporteDR del XML: {imp_xml}" + Style.RESET_ALL)
        if imp_calc != imp_xml:
            print(Fore.BLUE +
                  f"\nDiscrepancia detectada en el TrasladoDR {idx + 1}:")
            node= xml_etree.xparh("..//pago20:Pagos/pago20:Pago/pago20:DoctoRelacionado/pago20:ImpuestosDR/pago20:TrasladosDR/pago20:TrasladoDR", namespaces=namespaces)
            node.set('ImporteDR',imp_calc)
            print(
                Fore.YELLOW + f"Importe calculado: {imp_calc}, Importe en XML: {imp_xml}" + Style.RESET_ALL)
        else:
            print(
                Fore.GREEN + f"Importe calculado y Importe del XML coinciden para el TrasladoDR {idx + 1}: {imp_calc}" + Style.RESET_ALL)

    # Extraer el tipo de cambio
    tipo_cambio_usd = Decimal(xml_etree.xpath(
        ".//pago20:Pago/@TipoCambioP", namespaces=namespaces)[0])
    print(Fore.GREEN +
          f"Tipo de cambio USD: {tipo_cambio_usd}" + Style.RESET_ALL)
            
    # Extraer el total de pagos desde el XML
    total_pago = Decimal(xml_etree.xpath(
        ".//pago20:Totales/@MontoTotalPagos", namespaces=namespaces)[0])
    print(Fore.GREEN +
          f"Total de pagos según XML: {total_pago}" + Style.RESET_ALL)

    monto = Decimal(xml_etree.xpath(
        ".//pago20:Pago/@Monto", namespaces=namespaces)[0])
    total_script = redondeo(monto * tipo_cambio_usd)
    print(Fore.GREEN +
          f"Total de pagos según el script: {total_script}" + Style.RESET_ALL)
    if total_script != total_pago:
        print(
            Fore.RED + f"Discrepancia: Resultado Monto * TipoCambioP (redondeado/truncado): {total_script} vs MontoTotalPagos: {total_pago}" + Style.RESET_ALL
        )
        node1 = xml_etree.xpath(".//pago20:Totales", namespaces=namespaces)
        # Check if there are any nodes in node1
        if node1:
            # Assuming you want to set the attribute on the first matching node
            node1[0].set('MontoTotalPagos', str(total_script))
        
    else:
        print(
            Fore.GREEN + f"Los valores coinciden: {total_script} == {total_pago}" + Style.RESET_ALL)

    # Extraer el valor de TotalTrasladosBaseIVA16 desde el XML
    total_traslados_base_iva16 = Decimal(xml_etree.xpath(
        ".//pago20:Totales/@TotalTrasladosBaseIVA16", namespaces=namespaces)[0])

    # Calcular las equivalencias para los pagos
    EquivalenciaDR_string = xml_etree.xpath(
        ".//pago20:DoctoRelacionado/@EquivalenciaDR", namespaces=namespaces)
    EquivalenciaDR = [Decimal(x) for x in EquivalenciaDR_string]

    # Calcular BaseP e ImporteP
    BaseP = ([sum(BaseDR) / x for x in EquivalenciaDR])
    ImporteP = [sum(ImporteDR_calculado) / x for x in EquivalenciaDR]

    # Multiplicar BaseP[0] por el tipo de cambio
    resultado_base_tipo_cambio = BaseP[0] * tipo_cambio_usd
    resultado_redondeado = round(resultado_base_tipo_cambio, 2)

    # Imprimir los resultados
    print(Fore.GREEN + "--------------TrasladosP------------------------")
    print(Fore.GREEN + f"BaseP es: {redondeo(BaseP[0])}")
    print(Fore.GREEN + f"ImporteP es: {redondeo(ImporteP[0])}")
    print(Fore.GREEN +
          f"Resultado de BaseP * TipoCambioUSD (redondeado): {resultado_redondeado}")
    print(Fore.GREEN +
          f"TotalTrasladosBaseIVA16 del XML: {total_traslados_base_iva16}")

    # Comparar con TotalTrasladosBaseIVA16
    if resultado_redondeado != total_traslados_base_iva16:
        print(
            Fore.RED + f"Discrepancia: Resultado BaseP * TipoCambioUSD (redondeado): {resultado_redondeado} vs TotalTrasladosBaseIVA16: {total_traslados_base_iva16}" + Style.RESET_ALL)

    else:
        print(
            Fore.GREEN + f"Los valores coinciden: {resultado_redondeado} == {total_traslados_base_iva16}" + Style.RESET_ALL)

    print("------------------------------------------------")

    # Crear las sumatorias para BaseP e ImporteP
    sumatoria_base = '(' + ' + '.join(f"{base}/{equiv}" for base,
                                      equiv in zip(BaseDR, EquivalenciaDR)) + ')'
    sumatoria_importe = '(' + ' + '.join(f"{imp}/{equiv}" for imp,
                                         equiv in zip(ImporteDR_calculado, EquivalenciaDR)) + ')'

    print(
        Fore.RED + f"La sumatoria de BaseP es: {sumatoria_base} = {redondeo(BaseP[0])}")
    print(Fore.BLUE +
          f"La sumatoria de ImporteP es: {sumatoria_importe} = {redondeo(ImporteP[0])}")

    with open("cfdi_modificado.xml", "wb") as f:
        f.write(etree.tostring(xml_etree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8'))
    print("El archivo XML modificado ha sido guardado como 'prueba_modificada.xml'.")
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


def calcular_retenciones(xml_etree):
    # Verificar si existen retenciones en el comprobante
    namespaces = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'pago20': 'http://www.sat.gob.mx/Pagos20',
        'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
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
# Función para realizar cálculos relacionados con Comercio Exterior


def realizar_calculos_comercio_exterior(xml_etree):
    print(Fore.GREEN + "-------------- Cálculos Comercio Exterior --------------" + Style.RESET_ALL)
    namespaces = {
        'cfdi': 'http://www.sat.gob.mx/cfd/4',
        'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
        'pago20': 'http://www.sat.gob.mx/Pagos20',
        'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
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


    # Obtener el tipo de cambio desde el XML (ya integrado)
    try:
        tipo_cambio_xml = xml_etree.xpath(
            ".//cce20:ComercioExterior/@TipoCambioUSD", namespaces=namespaces)
        if tipo_cambio_xml:
            tipo_cambio_xml = float(tipo_cambio_xml[0])
            print(Fore.BLUE + f"Tipo de cambio XML (Comercio Exterior): " +
                  Fore.YELLOW + f"{tipo_cambio_xml}" + Style.RESET_ALL)
        else:
            print(
                Fore.RED + "No se encontró el atributo TipoCambioUSD en el XML." + Style.RESET_ALL)
            return
    except Exception as e:
        print(Fore.RED + f"Error al leer el XML: {e}" + Style.RESET_ALL)
        return

    # Obtener el tipo de cambio desde la API
    tipo_cambio_api = obtener_tipo_cambio_api()
    tipo_cambio_api_str =str(tipo_cambio_api)
    if tipo_cambio_api is not None:
        if tipo_cambio_xml == tipo_cambio_api:
            print(Fore.GREEN + "Los tipos de cambio coinciden." + Style.RESET_ALL)
        else:
            print(
                Fore.RED + f"Los tipos de cambio NO coinciden. XML: " + Fore.YELLOW + f"{tipo_cambio_xml}" + Fore.RED + f", API: " + Fore.YELLOW + f"{tipo_cambio_api}" + Style.RESET_ALL)
            nodo1= xml_etree.xpath('.//cce20:ComercioExterior', namespaces=namespaces)
            nodo1.set('TipoCambioUSD', tipo_cambio_api_str )
    else:
        print(
            Fore.RED + "No se pudo obtener el tipo de cambio de la API." + Style.RESET_ALL)

    # Validaciones adicionales para las mercancías
    mercancias = xml_etree.xpath(
        ".//cce20:ComercioExterior/cce20:Mercancias/cce20:Mercancia", namespaces=namespaces)

    for mercancia in mercancias:
        no_identificacion = mercancia.get("NoIdentificacion")
        valor_dolares = float(mercancia.get("ValorDolares", "0"))
        cantidad_aduana = mercancia.get("CantidadAduana")
        valor_unitario_aduana = mercancia.get("ValorUnitarioAduana")

        # Obtener los decimales del nodo Concepto que coinciden con NoIdentificacion
        concepto = xml_etree.xpath(
            f".//cfdi:Concepto[@NoIdentificacion='{no_identificacion}']", namespaces=namespaces)

        if concepto:
            concepto = concepto[0]
            cantidad = concepto.get("Cantidad", "0")
            valor_unitario = concepto.get("ValorUnitario", "0")

            # Calcular el número de decimales de la cantidad y el valor unitario
            num_decimales_cantidad = len(
                cantidad.split('.')[-1]) if '.' in cantidad else 0
            num_decimales_valor_unitario = len(
                valor_unitario.split('.')[-1]) if '.' in valor_unitario else 0
        else:
            num_decimales_cantidad, num_decimales_valor_unitario = None, None

        if cantidad_aduana and valor_unitario_aduana and num_decimales_cantidad is not None and num_decimales_valor_unitario is not None:
            cantidad_aduana = float(cantidad_aduana)
            valor_unitario_aduana = float(valor_unitario_aduana)

            # Evitar validaciones si ValorDolares es "0" o "1"
            if valor_dolares in [0, 1]:
                continue

            # Cálculo del límite inferior
            cantidad_inferior = cantidad_aduana - \
                (10 ** -num_decimales_cantidad) / 2
            valor_inferior = valor_unitario_aduana - \
                (10 ** -num_decimales_valor_unitario) / 2
            limite_inferior = cantidad_inferior * valor_inferior
            # Truncar a dos decimales
            limite_inferior_truncado = truncar(limite_inferior, 2)

            # Cálculo del límite superior
            cantidad_superior = cantidad_aduana + \
                (10 ** -num_decimales_cantidad) / 2 - 10 ** -12
            valor_superior = valor_unitario_aduana + \
                (10 ** -num_decimales_valor_unitario) / 2 - 10 ** -12
            limite_superior = cantidad_superior * valor_superior
            # Redondear al número entero más cercano
            limite_superior_redondeado = round(limite_superior)

            # Validar que el valor de ValorDolares esté dentro de los límites
            if limite_inferior_truncado > valor_dolares or valor_dolares > limite_superior_redondeado:
                print(
                    f"El valor de ValorDolares (" f"{valor_dolares}"f") está fuera de los límites para la mercancía con NoIdentificacion: {no_identificacion}.")
                print(f"Limite inferior: "
                      f"{limite_inferior_truncado}"f"--"f"Limite superior: ""{limite_superior_redondeado}")

    print( "--------------------------------------------------------")
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


# Verificar el tipo de comprobante y proceder
def iniciar (xml_etree):
    namespaces = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
            'pago20': 'http://www.sat.gob.mx/Pagos20',
            'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
            's0': 'apps.services.soap.core.views'
        }
    tipo_comprobante = xml_etree.get("TipoDeComprobante")
    if tipo_comprobante:
        tipo = tipo_comprobante[0].upper()
        print(
            f"Detectado comprobante de tipo {tipo}.\n")

        if tipo == "T":
            if xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces):
                realizar_calculos_comercio_exterior(xml_etree)
            else:
                print(
                    "Comprobante de tipo T sin complemento de comercio exterior.")

        elif tipo in ["I", "E"]:
            if xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces):
                realizar_calculos_generales(xml_etree)
                realizar_calculos_comercio_exterior(xml_etree)
            else:

                realizar_calculos_generales(xml_etree)

        elif tipo == 'P':
            realizar_calculos_pago(xml_etree)
            calcular_retenciones(xml_etree)

        else:
            print("Tipo de comprobante no identificado.")
    else:
        print("No se encontró el tipo de comprobante en el XML.")
