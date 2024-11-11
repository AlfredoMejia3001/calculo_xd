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
    total_otros_pagos = float(total_otros_pagos[0])
    total_persepciones = float(total_persepciones[0])
    monto = total_otros_pagos + total_persepciones

    print("percepciones")
    print(monto)
    print(monto_rec[0])
    if monto != float(monto_rec[0]):
        print("Son diferentes ")
    else:
        print("son iguales")


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
        print("no son iguales")
    else:
        print("son iguales")


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
        print("no son iguales")
    else:
        print("son iguales")


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
        print("no son iguales")
    else:
        print("son iguales")


def total_gravado():
    total_gravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalGravado", namespaces=namespaces)

    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)
    
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    ImporteExent = sum(float (impor) for impor in ImporteExento )

    ImporteExento = float(ImporteExento[0])
    ImporteGravado = float(ImporteGravado[0])
    tot_suel = ImporteExent + ImporteGravad

    if tot_suel != float(total_gravado[0]):
        print("no son iguales")
    else:
        print("son iguales")
    
    
def total_excemto():
    total_excento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/@TotalExento", namespaces=namespaces)

    ImporteGravado = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteGravado", namespaces=namespaces)
    ImporteExento = xml_etree.xpath("//nomina12:Nomina/nomina12:Percepciones/nomina12:Percepcion/@ImporteExento", namespaces=namespaces)
    
    ImporteGravad = sum(float (impor) for impor in ImporteGravado )
    ImporteExent = sum(float (impor) for impor in ImporteExento )

    ImporteExento = float(ImporteExento[0])
    ImporteGravado = float(ImporteGravado[0])
    tot_suel = ImporteExent + ImporteGravad

    if tot_suel != float(total_excento[0]):
        print("no son iguales")
    else:
        print("son iguales")
    

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


total_imp_reten_deduc()