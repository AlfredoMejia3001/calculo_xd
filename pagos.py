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

