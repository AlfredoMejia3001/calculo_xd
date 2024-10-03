"""Calculo de bases e importes"""
from collections import defaultdict
from decimal import Decimal
from lxml import etree
from colorama import Fore
# pylint: disable=C0301
# pylint: disable=C0103
# pylint: disable=I1101
# pylint: disable=C0200
# pylint: disable=W0621

xml_string = open(
    "2024_52985_P_27352.xml", "rb").read()
pregunta = input("Tipo de cfdi: ")
if pregunta.lower() == 'c':

    # Crear objeto ElemenTree
    xml_etree = etree.fromstring(xml_string)

    # Asignar namespaces
    my_namespaces = xml_etree.nsmap

    # Obtener valor base
    string_base = xml_etree.xpath(
        ".//cfdi:Traslado/@Base", namespaces=my_namespaces)

    # Conversión de tipos
    num_bases = [float(element) for element in string_base]

    # Eliminar el valor totales de las bases e imprimir
    num_bases.pop()
    suma_base = sum(num_bases)

    # Obtener valor importe
    string_import = xml_etree.xpath(
        ".//cfdi:Traslado/@Importe", namespaces=my_namespaces)

    # Conversión de tipos
    num_import = [float(elementI) for elementI in string_import]

    # Eliminar el valor totales de las bases e imprimir
    num_import.pop()
    suma_imp = sum(num_import)

    # Cálculo de los valores importes
    ValorUnitario_string = xml_etree.xpath(
        ".//cfdi:Concepto/@ValorUnitario", namespaces=my_namespaces)
    Cantidad_string = xml_etree.xpath(
        ".//cfdi:Concepto/@Cantidad", namespaces=my_namespaces)

    ValorUnitario = [float(x) for x in ValorUnitario_string]
    Cantidad = [float(x) for x in Cantidad_string]
    print("Cantidad", Cantidad)
    print("ValorUnitario", ValorUnitario)
    Base = [x * y for x, y in zip(ValorUnitario, Cantidad)]
    Base.pop()  # Excluir el último elemento
    print(Fore.GREEN + "La Base es:", Base)
    print()

    bases_por_tasa = defaultdict(float)
    importe_por_tasa = defaultdict(float)

    # Importe
    Base_string = xml_etree.xpath(
        ".//cfdi:Traslado/@Base", namespaces=my_namespaces)
    TasaOCuota_string = xml_etree.xpath(
        ".//cfdi:Traslado/@TasaOCuota", namespaces=my_namespaces)

    BaseT = [float(x) for x in Base_string]
    TasaOCuota = [float(x) for x in TasaOCuota_string]
    print(Fore.BLUE + "Base", BaseT)
    print("TasaOcuota", TasaOCuota)

    BaseT.pop()  # Excluir el último elemento
    TasaOCuota.pop()  # Excluir el último elemento
    importeT = [x * y for x, y in zip(BaseT, TasaOCuota)]
    print(Fore.GREEN + "El Importe es:", importeT)

    bases_por_tasa = defaultdict(float)

    for traslado in xml_etree.xpath(".//cfdi:Traslado", namespaces=my_namespaces):
        base = float(traslado.get("Base"))
        tasa_ocuota = float(traslado.get("TasaOCuota"))

        if base:
            bases_por_tasa[tasa_ocuota] += base

        importe = base * tasa_ocuota
        if importe:
            importe_por_tasa[tasa_ocuota] += importe

    # Imprimir los resultados de las bases
    print(Fore.GREEN + "Suma de bases por tasa o cuota:")
    for tasa, total_base in bases_por_tasa.items():
        print(f"Tasa: {tasa}, Suma de Bases: {total_base}")
    print("----------------------------------------------")

    # Imprimir los resultados de los importes
    print(Fore.GREEN + "Suma de importes por tasa o cuota:")
    for tasa, total_importe in importe_por_tasa.items():
        print(f"Tasa: {tasa}, Suma de Importes: {total_importe}")
    print("----------------------------------------------")


else:

    # para pagpos-------------------------------------------------------------------------------------------------------------------------------------------

    my_namespaces = {'cfdi': 'http://www.sat.gob.mx/cfd/4', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                     'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital', 'pago20': 'http://www.sat.gob.mx/Pagos20'}

    # crear objeto ElemenTree
    xml_etree = etree.fromstring(xml_string)

    # asigna namespaces
    my_namespaces = xml_etree.nsmap

    # Obtener valor base
    string_base = xml_etree.xpath(
        ".//pago20:TrasladoDR/@BaseDR", namespaces=my_namespaces)

    # conversion de tipos
    num_bases = []
    for element in string_base:
        num_bases.append(Decimal(element))

    # elimina el valor totales de las bases e imprime
    # num_bases.pop()
    suma_base = sum(num_bases)
    # print(suma_base)

    string_import = xml_etree.xpath(
        ".//pago20:TrasladoDR/@ImporteDR", namespaces=my_namespaces)

    # conversion de tipos
    num_import = []
    for elementI in string_import:
        num_import.append(Decimal(elementI))

    # elimina el valor totales de las bases e imprime
    # num_import.pop()
    suma_imp = sum(num_import)
    # importe
    Base_string = xml_etree.xpath(
        ".//pago20:TrasladoDR/@BaseDR", namespaces=my_namespaces)
    TasaOCuota_string = xml_etree.xpath(
        ".//pago20:TrasladoDR/@TasaOCuotaDR", namespaces=my_namespaces)

    BaseT = ([Decimal(x) for x in Base_string])
    TasaOCuota = ([Decimal(x) for x in TasaOCuota_string])
    # print(Base_string)
    # print("Base", BaseT)
    # print("TasaOCuota", TasaOCuota)

    importeT = [x*y for x, y in zip(BaseT, TasaOCuota)]
    print("los importes son", importeT)
    # baseP e importeP
    EquivalenciaDR_string = xml_etree.xpath(
        ".//pago20:DoctoRelacionado/@EquivalenciaDR", namespaces=my_namespaces)
    EquivalenciaDR = ([Decimal(x) for x in EquivalenciaDR_string])

    ImporteP = [suma_imp/x for x in EquivalenciaDR]
    BaseP = [suma_base/x for x in EquivalenciaDR]
    print(Fore.GREEN, "--------------TrasladosP------------------------")
    print(Fore.GREEN+"BaseP es:", BaseP[0])
    print(Fore.GREEN+"ImporteP es:", ImporteP[0])
    print("------------------------------------------------")

    sumatoria = '('
    for i in range(len(BaseT)):
        sumatoria += str(BaseT[i]) + '/' + format(EquivalenciaDR[i])
        if i != len(BaseT) - 1:
            sumatoria += ' + '
    sumatoria += ')'

    sumatoriaimporte = '('
    for i in range(len(importeT)):
        sumatoriaimporte += str(importeT[i]) + '/' + format(EquivalenciaDR[i])
        if i != len(importeT) - 1:
            sumatoriaimporte += ' + '
    sumatoriaimporte += ')'

    print(Fore.RED, "La sumatoria de BaseP es: ", sumatoria, "=",  BaseP[0])

    print(Fore.BLUE, "La sumatoria de ImporteP es: ",
          sumatoriaimporte, "=",  ImporteP[0])


def calculo_reten(xml_etree):
    """Calculo de retenciones CRP20"""
    print("=============================Retenciones=================================")
    # Obtener valor base
    string_base = xml_etree.xpath(
        ".//pago20:RetencionDR/@BaseDR", namespaces=my_namespaces)

    # conversion de tipos
    num_bases = []
    for element in string_base:
        num_bases.append(Decimal(element))

        # elimina el valor totales de las bases e imprime
        # num_bases.pop()
    suma_base = sum(num_bases)
    # print(suma_base)

    string_import = xml_etree.xpath(
        ".//pago20:RetencionDR/@ImporteDR", namespaces=my_namespaces)

    # conversion de tipos
    num_import = []
    for elementI in string_import:
        num_import.append(Decimal(elementI))

        # elimina el valor totales de las bases e imprime
        # num_import.pop()
        suma_imp = sum(num_import)
        # importe
        Base_string = xml_etree.xpath(
            ".//pago20:RetencionDR/@BaseDR", namespaces=my_namespaces)
        TasaOCuota_string = xml_etree.xpath(
            ".//pago20:RetencionDR/@TasaOCuotaDR", namespaces=my_namespaces)

        BaseT = ([Decimal(x) for x in Base_string])
        TasaOCuota = ([Decimal(x) for x in TasaOCuota_string])
        # print(Base_string)
        # print("Base", BaseT)
        # print("TasaOCuota", TasaOCuota)

        importeT = [x*y for x, y in zip(BaseT, TasaOCuota)]
        # print("los importes son", importeT)
        # baseP e importeP
        EquivalenciaDR_string = xml_etree.xpath(
            ".//pago20:DoctoRelacionado/@EquivalenciaDR", namespaces=my_namespaces)
        EquivalenciaDR = ([Decimal(x) for x in EquivalenciaDR_string])

        ImporteP = [suma_imp/x for x in EquivalenciaDR]
        BaseP = [suma_base/x for x in EquivalenciaDR]
        print(Fore.GREEN, "--------------TrasladosP------------------------")
        print(Fore.GREEN+"BaseP es:", BaseP[0])
        print(Fore.GREEN+"ImporteP es:", ImporteP[0])
        print("------------------------------------------------")

        sumatoria = '['
        for i in range(len(BaseT)):
            sumatoria += str(BaseT[i]) + '/' + format(EquivalenciaDR[i])
            if i != len(BaseT) - 1:
                sumatoria += ' + '
        sumatoria += ']'

        sumatoriaimporte = '['
        for i in range(len(importeT)):
            sumatoriaimporte += str(importeT[i]) + \
                '/' + format(EquivalenciaDR[i])
            if i != len(importeT) - 1:
                sumatoriaimporte += ' + '
        sumatoriaimporte += ']'

        print(Fore.RED, "La sumatoria de BaseP es: ",
              sumatoria, "=",  BaseP[0])

        print(Fore.BLUE, "La sumatoria de ImporteP es: ", sumatoriaimporte)


if pregunta.lower() == 'p':
    get_retenciones = xml_etree.xpath(
        ".//pago20:RetencionDR/@BaseDR", namespaces=my_namespaces)
    if get_retenciones:
        print()
        calculo_reten(xml_string)
    else:
        print("sin retenciones en el XML")
else:
    pass
