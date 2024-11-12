from datetime import datetime, timedelta
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style
from decimal import ROUND_HALF_UP

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

if nodo:  
    emisor = nodo[0]  
    emisor.set('Rfc', str(rfc))
    emisor.set('Nombre', str(name))
    emisor.set('RegimenFiscal', str(regi))


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
    

def valor_unitario(namespaces):
    valor_unitario = xml_etree.xpath("//cfdi:Conceptos/cfdi:Concepto/@ValorUnitario", namespaces=namespaces)
    total_otros_pagos = xml_etree.xpath("//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    total_persepciones = xml_etree.xpath("//nomina12:Nomina/@TotalPercepciones", namespaces=namespaces)
    tot_pag = float(total_otros_pagos[0]) if total_otros_pagos else 0
    tot_per = float(total_persepciones[0]) if total_persepciones else 0
    suma= tot_pag + tot_per
    if suma != float(valor_unitario[0]):
        print("no son iguales val uni")
    else:
        print("si son iguales val uni")
    print("suma:",suma)


def importe(namespaces):
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


def descuento (namespaces):
    desc = xml_etree.xpath("//cfdi:Conceptos/cfdi:Concepto/@Descuento", namespaces=namespaces)
    total_deduciones = xml_etree.xpath("//nomina12:Nomina/@TotalDeducciones", namespaces=namespaces)
    des = str(desc[0])
    total_deducione = str(total_deduciones[0])
    if des != total_deducione:
        print("El descuento no coincide")
    else:
        print("Todo esta correcto descuento")

        
def total_percepciones(namespaces):
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


def total_desucciones(namespaces):
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


def total_otros_pagos(namespaces):
    imp = (xml_etree.xpath("//nomina12:Nomina/nomina12:OtrosPagos/nomina12:OtroPago/@Importe", namespaces=namespaces))
    total_otros_pagos= xml_etree.xpath("//nomina12:Nomina/@TotalOtrosPagos", namespaces=namespaces)
    suma_imp = sum(float (impor) for impor in imp )
    if float(total_otros_pagos[0]) != suma_imp:
        print("son diferentes")
    else:
        print('son iguales')


def monto_recurso_propio(namespaces): 
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


def percep_val(namespaces):
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


def total_sueldos(namespaces):
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


def total_separacion(namespaces):
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


def total_jubilacion(namespaces):
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


def total_gravado(namespaces):
    total_gravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalGravado", namespaces=namespaces)
    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    if ImporteGravad != float(total_gravado[0]):
        print(f"no son iguales total gravado XML:{total_gravado[0]} calculo: {ImporteGravad}")
    else:
        print("son iguales gravado")
    
    
def total_excemto(namespaces):
    total_excento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalExento", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)
    ImporteExent = sum(float (impor) for impor in ImporteExento ) 
    if ImporteExent != float(total_excento[0]):
        print(f"no son iguales total excento XML:{total_excento[0]} Calculo: {ImporteExent}")
    else:
        print("son iguales Excento")
    

def total_imp_reten_deduc(namespaces):
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


def condicion_nomina(namespaces):
    valor_unitario(namespaces)
    importe(namespaces)
    descuento(namespaces)
    if xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones", namespaces=namespaces):
        total_percepciones(namespaces)
    if xml_etree.xpath("//nomina12:Nomina/nomina12:Deducciones", namespaces=namespaces):
        total_desucciones(namespaces)
    if xml_etree.xpath("//nomina12:Nomina/nomina12:OtrosPagos", namespaces=namespaces):
        total_otros_pagos(namespaces)
    monto_recurso_propio(namespaces)
    percep_val(namespaces)
    if xml_etree.xpath('//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion[@TipoPercepcion="022" or @TipoPercepcion="023" or @TipoPercepcion="025" or @TipoPercepcion="039" or @TipoPercepcion="044"]', namespaces=namespaces):
        print
    else:
        total_sueldos(namespaces)
    
    if xml_etree.xpath('//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion[@TipoPercepcion="022" or @TipoPercepcion="023" or @TipoPercepcion="025"]', namespaces=namespaces):
        total_separacion(namespaces)

    if xml_etree.xpath('//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion[@TipoPercepcion="039" or @TipoPercepcion="044"]', namespaces=namespaces):
        total_sueldos(namespaces)

    total_gravado(namespaces)
    total_excemto(namespaces)
    if xml_etree.xpath("//nomina12:Deducciones/nomina12:Deduccion[@TipoDeduccion='002']", namespaces=namespaces):
        total_imp_reten_deduc(namespaces)

condicion_nomina(namespaces)