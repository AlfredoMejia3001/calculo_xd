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
