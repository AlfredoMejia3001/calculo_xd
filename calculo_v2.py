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
import math
from lxml import etree
from colorama import Fore, Style
from decimal import ROUND_HALF_UP
import requests
from sig import timbrar

xml = input("Ingresa el nombre del xml: ")

# Cargar el archivo XML
xml_string = open(
    xml, "rb").read()
xml_etree = etree.fromstring(xml_string)
namespaces = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20',
    'cce20': 'http://www.sat.gob.mx/ComercioExterior20',
    'nomina12': 'http://www.sat.gob.mx/nomina12',
    'cartaporte31': 'http://www.sat.gob.mx/CartaPorte31',
    's0': 'apps.services.soap.core.views'
}

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


def realizar_calculos_pago():
    print(Fore.GREEN + "-------------- Cálculos de Pagos --------------" + Style.RESET_ALL)

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

    imppagado = xml_etree.xpath(".//pago20:DoctoRelacionado/@ImpPagado", namespaces=namespaces)

    sumImp = sum(float(pag) for pag in imppagado )

    print("suma de los importes pagados:", sumImp)
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

def realizar_calculos_comercio_exterior():
    print(Fore.GREEN + "-------------- Cálculos Comercio Exterior --------------" + Style.RESET_ALL)
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

    tipo_cambio_api = obtener_tipo_cambio_api()
    tipo_cambio_api_str =str(tipo_cambio_api)
    if tipo_cambio_api is not None:
        if tipo_cambio_xml == tipo_cambio_api:
            print(Fore.GREEN + "Los tipos de cambio coinciden." + Style.RESET_ALL)
        else:
            print(
                Fore.RED + f"Los tipos de cambio NO coinciden. XML: " + Fore.YELLOW + f"{tipo_cambio_xml}" + Fore.RED + f", API: " + Fore.YELLOW + f"{tipo_cambio_api}" + Style.RESET_ALL)
            nodo1= xml_etree.xpath('.//cce20:ComercioExterior', namespaces=namespaces)
            
           # nodo1.set('TipoCambioUSD', str(tipo_cambio_api_str[0]) )
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
                    Fore.RED + f"El valor de ValorDolares (" + Fore.YELLOW + f"{valor_dolares}" + Fore.RED + f") está fuera de los límites para la mercancía con NoIdentificacion: {no_identificacion}." + Style.RESET_ALL)
                print(Fore.CYAN + f"Limite inferior: " + Fore.YELLOW +
                      f"{limite_inferior_truncado}" + Fore.CYAN + f"--"+Fore.CYAN + f"Limite superior: "+Fore.YELLOW + f"{limite_superior_redondeado}")

    print(Fore.GREEN + "--------------------------------------------------------" + Style.RESET_ALL)
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



def valor_unitario():
    valor_unitario = xml_etree.xpath(".//cfdi:Conceptos/cfdi:Concepto/@ValorUnitario", namespaces=namespaces)
    if xml_etree.xpath(".//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces): 
        total_otros_pagos = xml_etree.xpath(".//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    total_persepciones = xml_etree.xpath(".//nomina12:Nomina/@TotalPercepciones", namespaces=namespaces)
    tot_pag = float(total_otros_pagos[0]) if total_otros_pagos else 0
    tot_per = float(total_persepciones[0]) if total_persepciones else 0
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
    tot_pag = float(total_otros_pagos[0]) if total_otros_pagos else 0
    tot_per = float(total_persepciones[0]) if total_persepciones else 0
    suma= tot_pag + tot_per
    if suma != float(imp[0]):
        print("no son iguales importe")
    else:
        print("si son iguales importe")
    print("suma:",suma)


def descuento ():
    desc = xml_etree.xpath("//cfdi:Conceptos/cfdi:Concepto/@Descuento", namespaces=namespaces)
    total_deduciones = xml_etree.xpath("//nomina12:Nomina/@TotalDeducciones", namespaces=namespaces)
    des = str(desc[0])
    total_deducione = str(total_deduciones[0])
    if des != total_deducione:
        print("El descuento no coincide")
    else:
        print("Todo esta correcto descuento")

        
def total_percepciones():
    total_perp = xml_etree.xpath("//nomina12:Nomina/@TotalPercepciones", namespaces=namespaces)
    total_sueldos = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalSueldos", namespaces=namespaces)
    total_separacion = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalSeparacionIndemnizacion", namespaces=namespaces)
    total_jubilacion = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalJubilacionPensionRetiro", namespaces=namespaces)
    total_sueldos = float(total_sueldos[0]) if total_sueldos else 0
    total_separacion = float(total_separacion[0]) if total_separacion else 0
    total_jubilacion = float(total_jubilacion[0]) if total_jubilacion else 0
    total_percepciones = total_sueldos + total_separacion + total_jubilacion
    if float(total_perp[0]) != total_percepciones:
        print(f"El total percepciones no es igual XML:{total_perp[0]} calculo en el script:{total_percepciones}")
    else:
        print("Son iguales las totales percepciones ")


def total_desucciones():
    total_deduc = xml_etree.xpath("//nomina12:Nomina/@TotalDeducciones", namespaces=namespaces)
    total_otras_deducciones = xml_etree.xpath("//nomina12:Nomina/nomina12:Deducciones/@TotalOtrasDeducciones", namespaces=namespaces)
    total_impuestos_retenidos = xml_etree.xpath("//nomina12:Nomina/nomina12:Deducciones/@TotalImpuestosRetenidos", namespaces=namespaces)
    total_otras_deducc = float(total_otras_deducciones[0]) if total_otras_deducciones else 0
    total_impuestos_rete = float(total_impuestos_retenidos[0]) if total_impuestos_retenidos else 0   
    total_deducciones= total_otras_deducc + total_impuestos_rete 
    if float(total_deduc[0]) != total_deducciones:
        print(f"El total deducciones no es igual, dato en el XML:{total_deduc[0]} - - resultado del calculo {total_deducciones}")
    else:
        print("Son iguales las totales deducciones ")


def total_otros_pagos():
    imp = (xml_etree.xpath("//nomina12:Nomina/nomina12:OtrosPagos/nomina12:OtroPago/@Importe", namespaces=namespaces))
    total_otros_pagos= xml_etree.xpath("//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    suma_imp = sum(float (impor) for impor in imp )
    if float(total_otros_pagos[0]) != suma_imp:
        print("son diferentes")
    else:
        print('son iguales')


def monto_recurso_propio(): 
    total_otros_pagos = xml_etree.xpath("//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    total_persepciones = xml_etree.xpath("//nomina12:Nomina/@TotalPercepciones", namespaces=namespaces)
    monto_rec = xml_etree.xpath("//nomina12:Nomina/nomina12:Emisor/nomina12:EntidadSNCF/@MontoRecursoPropio", namespaces=namespaces)
    total_otros_pagos = float(total_otros_pagos[0]) if total_otros_pagos else 0
    total_persepciones = float(total_persepciones[0]) if total_persepciones else 0
    monto = total_otros_pagos + total_persepciones
    if monto != float(monto_rec[0]) if monto_rec else 0:
        print(f"es incorrrecto el monto recurso propio, este es el resultado correcto del calculo: {monto}")
    else:
        print("es correcto el monto de recursos propios")


def percep_val():
    total_sueldos = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalSueldos", namespaces=namespaces)
    total_separacion = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalSeparacionIndemnizacion", namespaces=namespaces)
    total_jubilacion = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalJubilacionPensionRetiro", namespaces=namespaces)
    total_sueldos = float(total_sueldos[0]) if total_sueldos else 0
    total_separacion = float(total_separacion[0]) if total_separacion else 0
    total_jubilacion = float(total_jubilacion[0]) if total_jubilacion else 0
    percep= total_sueldos + total_separacion + total_jubilacion
    total_gravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalGravado", namespaces=namespaces)
    total_excento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalExento", namespaces=namespaces)
    total_gravado = float(total_gravado[0]) if total_gravado else 0
    total_excento = float(total_excento[0]) if total_excento else 0
    grav = total_gravado + total_excento
    if percep != grav:
        print('No coinciden las sumas de TotalSueldos + TotalSeparacionIndemnizacion + TotalJubilacionPensionRetiro')
        print('Y la suma de TotalGravado + TotalExento')
    else:
        print('Si coinciden las sumas de TotalSueldos + TotalSeparacionIndemnizacion + TotalJubilacionPensionRetiro ')
        print('Y la suma de TotalGravado + TotalExento')


def total_sueldos():
    total_sueldos = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalSueldos", namespaces=namespaces)
    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    ImporteExent = sum(float (impor) for impor in ImporteExento )
    ImporteExento = float(ImporteExento[0])
    ImporteGravado = float(ImporteGravado[0])
    tot_suel = ImporteExent + ImporteGravad
    if tot_suel != float(total_sueldos[0]):
        print(f"El TotalSueldos no es correcto, calculo hecho:{tot_suel}")
    else:
        print("son iguales total sueldos")


def total_separacion():
    total_separacion = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalSeparacionIndemnizacion", namespaces=namespaces)
    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    ImporteExent = sum(float (impor) for impor in ImporteExento )
    ImporteExento = float(ImporteExento[0])
    ImporteGravado = float(ImporteGravado[0])
    tot_suel = ImporteExent + ImporteGravad
    if tot_suel != float(total_separacion[0]):
        print(f"no son iguales total separacion XML:{total_separacion[0]} != calculo: {tot_suel}")
    else:
        print("son iguales separacion")


def total_jubilacion():
    total_jubilacion = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalJubilacionPensionRetiro", namespaces=namespaces)
    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)   
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    ImporteExent = sum(float (impor) for impor in ImporteExento )
    ImporteExento = float(ImporteExento[0])
    ImporteGravado = float(ImporteGravado[0])
    tot_suel = ImporteExent + ImporteGravad
    if tot_suel != float(total_jubilacion[0]):
        print(f"no son iguales total jubilacion XML:{total_jubilacion[0]} calculo: {tot_suel}")
    else:
        print("son iguales jubilacion")


def total_gravado():
    total_gravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalGravado", namespaces=namespaces)
    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    if ImporteGravad != float(total_gravado[0]):
        print(f"no son iguales total gravado XML:{total_gravado[0]} calculo: {ImporteGravad}")
    else:
        print("son iguales gravado")
    
    
def total_excemto():
    total_excento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalExento", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)
    ImporteExent = sum(float (impor) for impor in ImporteExento)
    ImporteExent = round(ImporteExent,2) 
    if ImporteExent != float(total_excento[0]):
        print(f"no son iguales total excento XML: {total_excento[0]} Calculo: {ImporteExent}")
    else:
        print("son iguales Excento")
    

def total_imp_reten_deduc():
    total_impuestos_retenidos = xml_etree.xpath("//nomina12:Deducciones/@TotalImpuestosRetenidos", namespaces=namespaces)    
    deducciones_002 = xml_etree.xpath("//nomina12:Deducciones/nomina12:Deduccion[@TipoDeduccion='002']/@Importe", namespaces=namespaces)
    suma_deducciones_002 = sum(float(importe) for importe in deducciones_002)
    if total_impuestos_retenidos:
        total_impuestos_retenidos = float(total_impuestos_retenidos[0]) 
        if total_impuestos_retenidos == suma_deducciones_002:
            print(f"La validación es correcta: total impuestos {total_impuestos_retenidos} suma de los importes {suma_deducciones_002}")
        else:
            print(f"Error: El TotalImpuestosRetenidos ({total_impuestos_retenidos}) no coincide con la suma de deducciones TipoDeduccion=002 ({suma_deducciones_002}).")
    else:
        if deducciones_002:
            print("Error: No se debe incluir TotalImpuestosRetenidos cuando no hay deducciones con TipoDeduccion=002.")
        else:
            print("No hay deducciones TipoDeduccion=002 y no se debe incluir el atributo TotalImpuestosRetenidos.")


def condicion_nomina():
    valor_unitario()
    importe()
    descuento()
    if xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones", namespaces=namespaces):
        total_percepciones()
    if xml_etree.xpath("//nomina12:Nomina/nomina12:Deducciones", namespaces=namespaces):
        total_desucciones()
    if xml_etree.xpath("//nomina12:Nomina/nomina12:OtrosPagos", namespaces=namespaces):
        total_otros_pagos()
    monto_recurso_propio()
    percep_val()
    if xml_etree.xpath('//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion[@TipoPercepcion="022" or @TipoPercepcion="023" or @TipoPercepcion="025" or @TipoPercepcion="039" or @TipoPercepcion="044"]', namespaces=namespaces):
        total_sueldos()
    
    if xml_etree.xpath('//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion[@TipoPercepcion="022" or @TipoPercepcion="023" or @TipoPercepcion="025"]', namespaces=namespaces):
        total_separacion()

    if xml_etree.xpath('//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion[@TipoPercepcion="039" or @TipoPercepcion="044"]', namespaces=namespaces):
        total_sueldos()

    total_gravado()
    total_excemto()
    if xml_etree.xpath("//nomina12:Deducciones/nomina12:Deduccion[@TipoDeduccion='002']", namespaces=namespaces):
        total_imp_reten_deduc()


def pesoBrutoTotal():
    if xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:Autotransporte', namespaces=namespaces) or xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:TransporteAereo' or xml_etree.xpath(".//cartaporte31:Mercancias/cartaporte31:TransporteFerroviario")):
        pesoKG=xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:Mercancia/@PesoEnKg', namespaces=namespaces)
        pesoBrutoTotal= xml_etree.xpath('.//cartaporte31:Mercancias/@PesoBrutoTotal', namespaces=namespaces)
        suma_peso = sum(float(peso) for peso in pesoKG)
        if suma_peso != float(pesoBrutoTotal[0]):
            suma_pesoSTR=int(suma_peso)
            if suma_pesoSTR != int(pesoBrutoTotal[0]):
                print(f'Peso calculado {suma_pesoSTR} es diferente que el del xml {pesoBrutoTotal[0]}')
                print(f"{suma_pesoSTR} != {pesoBrutoTotal[0]}")
            else:
                print('Los pesos coinciden')
                print(f"Peso calculado ---> {suma_pesoSTR} = {pesoBrutoTotal[0]} <--- Peso XML")
        else:
            print('Los pesos coinciden')
            print(f"Peso calculado ---> {suma_peso} = {pesoBrutoTotal[0]} <--- Peso XML")

    elif xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:TransporteMaritimo', namespaces=namespaces):
        pesoBrutoTotal= (xml_etree.xpath('.//cartaporte31:Mercancias/@PesoBrutoTotal', namespaces=namespaces))
        pesoBruto=xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:Mercancia/cartaporte31:DetalleMercancia/@PesoBruto', namespaces=namespaces)
        pesoNeto=xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:Mercancia/cartaporte31:DetalleMercancia/@PesoNeto', namespaces=namespaces)
        pesoNetoTotal = (xml_etree.xpath('.//cartaporte31:Mercancias/@PesoNetoTotal', namespaces=namespaces))
        suma_peso = sum(float(peso) for peso in pesoBruto)
        
        if suma_peso != float(pesoBrutoTotal[0]):
            suma_pesoSTR=int(suma_peso)
            print(suma_pesoSTR)
            if suma_pesoSTR != int(pesoBrutoTotal[0]):
                print('Los pesos no coinciden')
                print(f"Peso calculado ---> {suma_pesoSTR} != {pesoBrutoTotal[0]} <--- Peso XML")
            else:
                print('Los pesos coinciden')
                print(f"Peso calculado ---> {suma_pesoSTR} = {pesoBrutoTotal[0]} <--- Peso XML")
        else:
            print('Los pesos coinciden')
            print(f"Peso calculado ---> {suma_peso} = {pesoBrutoTotal[0]} <--- Peso XML")        
        suma_pesoN = sum(float(peso) for peso in pesoNeto)
        if suma_pesoN != (pesoNetoTotal[0]):
            suma_pesoNT=int(suma_pesoN)
            print(suma_pesoNT)
            if suma_pesoNT != int(pesoNetoTotal[0]):
                print('Los pesos no coinciden')
                print(f"Peso calculado ---> {suma_pesoNT} != {pesoNetoTotal[0]} <--- Peso XML")
            else:
                print('Los pesos coinciden neto')
                print(f"Peso calculado ---> {suma_pesoNT} = {pesoNetoTotal[0]} <--- Peso XML")
        else:
            print('Los pesos coinciden neto ')
            print(f"Peso calculado ---> {suma_pesoN} = {float(pesoNetoTotal[0])} <--- Peso XML")      


def NumTotalMercancias():           
    mercancias = xml_etree.xpath(".//cartaporte31:Mercancias/cartaporte31:Mercancia", namespaces=namespaces)
    cantidad=len(mercancias)
    NumTotalMerca = xml_etree.xpath('.//cartaporte31:Mercancias/@NumTotalMercancias', namespaces=namespaces)
    print(f"Cantidad de nodos de mercancia {cantidad}")
    c = int(NumTotalMerca[0])
    if cantidad != c: 
        print(f'La cantidad de mercancias no coinciden {cantidad} != {NumTotalMerca[0]}')
    else:
        print(f'Las cantidades son iguales {cantidad} = {NumTotalMerca[0]}')
        

#---------------------------------------TransporteFerroviario-------------------------------------------#
def ferroviario():   
    toneladas_netas_carro= xml_etree.xpath(".//cartaporte31:Mercancias/cartaporte31:TransporteFerroviario/cartaporte31:Carro/@ToneladasNetasCarro", namespaces=namespaces)
    toneladas_netas_carro = int(toneladas_netas_carro[0])
    print(toneladas_netas_carro, "tn")
    peso_neto_merca= xml_etree.xpath(".//cartaporte31:Mercancias/cartaporte31:TransporteFerroviario/cartaporte31:Carro/cartaporte31:Contenedor/@PesoNetoMercancia", namespaces=namespaces)
    print(peso_neto_merca[0], "kg")
    toneladas = int(peso_neto_merca[0]) / 1000
    print(f'{int(toneladas)} == {peso_neto_merca[0]}')
    if int(toneladas) != int(toneladas_netas_carro[0]):
        print(f"El PesoNetoMercancia {peso_neto_merca[0]} es diferente al de ToneladasNetasCarro {toneladas_netas_carro[0]}")
    else:
        print(f'Son iguales los atributos PesoNetoMercancia={peso_neto_merca[0]} = {toneladas_netas_carro[0]} ToneladasNetasCarro ')


#--------------------------------------------TotalDistRec-----------------------------------------------#
def total_dist():
    if xml_etree.xpath(".//cartaporte31:Mercancias/cartaporte31:TransporteFerroviario", namespaces=namespaces) or xml_etree.xpath(".//cartaporte31:Mercancias/cartaporte31:Autotransporte", namespaces=namespaces):
        total_dist_rec = xml_etree.xpath('.//cartaporte31:CartaPorte/@TotalDistRec', namespaces=namespaces)
        print(total_dist_rec[0],"km")
        distancia_recorrida = xml_etree.xpath('.//cartaporte31:Ubicaciones/cartaporte31:Ubicacion/@DistanciaRecorrida', namespaces=namespaces)
        total_dist = sum(float(dist) for dist in distancia_recorrida)
        print(total_dist, "km")
        if total_dist != int(total_dist_rec[0]):
            print(f"Las distancias en kilometros no coinciden Distancia recorria suma = {total_dist} != {total_dist_rec[0]}")
        else:
            print(f"Las distancias en kilometros coinciden Distancia recorria suma = {total_dist} == {total_dist_rec[0]}")



def condicion_carta():
    if xml_etree.xpath("..//cartaporte31:Mercancias/cartaporte31:TransporteFerroviario", namespaces=namespaces):
        ferroviario()
    pesoBrutoTotal()
    NumTotalMercancias()
    total_dist()
    
    




tipo_comprobante = xml_etree.get("TipoDeComprobante")
if tipo_comprobante:
    tipo = tipo_comprobante[0].upper()
    print(Fore.CYAN +
          f"Detectado comprobante de tipo {tipo}." + Style.RESET_ALL)

    if tipo == "T":
        if xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces):
            realizar_calculos_comercio_exterior()
        elif xml_etree.xpath(".//cartaporte31:CartaPorte", namespaces=namespaces):   
            condicion_carta()
            print
        else:
            print(Fore.RED + "Comprobante de tipo T sin complemento de comercio exterior." + Style.RESET_ALL)
    elif tipo in ["I", "E"]:
        if xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces) and xml_etree.xpath(".//cartaporte31:CartaPorte", namespaces=namespaces):
            realizar_calculos_generales()
            realizar_calculos_comercio_exterior()
            condicion_carta()
        elif xml_etree.xpath(".//cce20:ComercioExterior", namespaces=namespaces):
            realizar_calculos_comercio_exterior()
            realizar_calculos_generales()
        elif xml_etree.xpath(".//cartaporte31:CartaPorte", namespaces=namespaces): 
            realizar_calculos_generales()
            condicion_carta()
        else:
            realizar_calculos_generales()
    elif tipo == 'P':
        realizar_calculos_pago()
        calcular_retenciones()
    elif tipo == 'N':
        condicion_nomina()
        
        print
    else:
        print(Fore.RED + "Tipo de comprobante no identificado." + Style.RESET_ALL)
else:
    print(Fore.RED + "No se encontró el tipo de comprobante en el XML." + Style.RESET_ALL)
