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

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style
import math
import requests
from decimal import ROUND_HALF_UP


# Cargar el archivo XML
xml_string = open(
    "/home/amejia/Documentos/EKU/cfdi_quick_1.xml", "rb").read()
xml_etree = etree.fromstring(xml_string)

namespaces = {
    'cfdi': 'http://www.sat.gob.mx/cfd/4',
    'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital',
    'pago20': 'http://www.sat.gob.mx/Pagos20',
    'cce20': 'http://www.sat.gob.mx/ComercioExterior20'
}


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
            data = response.json()
            if data['bmx']['series'][0]['datos']:  # Comprobar si hay datos
                tipo_cambio_api = float(
                    data['bmx']['series'][0]['datos'][0]['dato'])
                print(f"Tipo de cambio API Banxico: {tipo_cambio_api}")
                return tipo_cambio_api
            else:
                print(f"No hay datos para la fecha: {fecha_ini}")
        else:
            print(f"Error: {response.status_code} - {response.text}")
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

    # Extraer el valor de TotalTrasladosBaseIVA16 desde el XML
    total_traslados_base_iva16 = Decimal(xml_etree.xpath(
        ".//pago20:Totales/@TotalTrasladosBaseIVA16", namespaces=namespaces)[0])

    # Calcular las equivalencias para los pagos
    EquivalenciaDR_string = xml_etree.xpath(
        ".//pago20:DoctoRelacionado/@EquivalenciaDR", namespaces=namespaces)
    EquivalenciaDR = [Decimal(x) for x in EquivalenciaDR_string]

    # Calcular BaseP e ImporteP
    BaseP = [sum(BaseDR) / x for x in EquivalenciaDR]
    ImporteP = [sum(ImporteDR_calculado) / x for x in EquivalenciaDR]

    # Multiplicar BaseP[0] por el tipo de cambio
    resultado_base_tipo_cambio = BaseP[0] * tipo_cambio_usd
    resultado_redondeado = round(resultado_base_tipo_cambio, 2)

    # Imprimir los resultados
    print(Fore.GREEN + "--------------TrasladosP------------------------")
    print(Fore.GREEN + f"BaseP es: {BaseP[0]}")
    print(Fore.GREEN + f"ImporteP es: {ImporteP[0]}")
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
        Fore.RED + f"La sumatoria de BaseP es: {sumatoria_base} = {BaseP[0]}")
    print(Fore.BLUE +
          f"La sumatoria de ImporteP es: {sumatoria_importe} = {ImporteP[0]}")

    print(Fore.GREEN + "No se encontraron retenciones en el comprobante." + Style.RESET_ALL)


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

# Función para realizar cálculos relacionados con Comercio Exterior


def realizar_calculos_comercio_exterior():
    print(Fore.GREEN + "-------------- Cálculos Comercio Exterior --------------" + Style.RESET_ALL)

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

    if tipo_cambio_api is not None:
        if tipo_cambio_xml == tipo_cambio_api:
            print(Fore.GREEN + "Los tipos de cambio coinciden." + Style.RESET_ALL)
        else:
            print(
                Fore.RED + f"Los tipos de cambio NO coinciden. XML: " + Fore.YELLOW + f"{tipo_cambio_xml}" + Fore.RED + f", API: " + Fore.YELLOW + f"{tipo_cambio_api}" + Style.RESET_ALL)
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
