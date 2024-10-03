from lxml import etree
from colorama import Fore
from decimal import Decimal

# pylint: disable=C0301
# pylint: disable=C0103
# pylint: disable=I1101
# pylint: disable=C0200
# pylint: disable=W0621

xml_string = open("pago.xml", "rb").read()
pregunta = input("Tipo de cfdi: ")
if pregunta.lower() == 'p':
    # Crear objeto ElemenTree
    xml_etree = etree.fromstring(xml_string)

    # Asignar namespaces
    my_namespaces = xml_etree.nsmap

    # Obtener valor base
    string_base = xml_etree.xpath(
        ".//pago20:TrasladoDR/@BaseDR", namespaces=my_namespaces)

    # Conversión de tipos
    num_bases = [Decimal(element) for element in string_base]
    suma_base = sum(num_bases)

    # Obtener TipoFactorDR y realizar cálculos si no es Exento
    BaseT = []
    TasaOCuota = []
    for traslado in xml_etree.xpath(".//pago20:TrasladoDR", namespaces=my_namespaces):
        tipo_factor = traslado.get('TipoFactorDR')
        if tipo_factor == 'Exento':
            print("TipoFactorDR es Exento, no se realiza el cálculo para este elemento")
        else:
            base = traslado.get('BaseDR')
            tasa_o_cuota = traslado.get('TasaOCuotaDR')
            if base and tasa_o_cuota:
                BaseT.append(Decimal(base))
                TasaOCuota.append(Decimal(tasa_o_cuota))

    # Realizar cálculos si hay elementos válidos
    if BaseT and TasaOCuota:
        # Calcular importes
        importeT = [x * y for x, y in zip(BaseT, TasaOCuota)]
        print("Los importes son", importeT)

        # Obtener EquivalenciaDR
        EquivalenciaDR_string = xml_etree.xpath(
            ".//pago20:DoctoRelacionado/@EquivalenciaDR", namespaces=my_namespaces)
        EquivalenciaDR = [Decimal(x) for x in EquivalenciaDR_string]

        # Calcular BaseP e ImporteP
        suma_base = sum(BaseT)
        suma_imp = sum(importeT)
        ImporteP = [suma_imp / x for x in EquivalenciaDR]
        BaseP = [suma_base / x for x in EquivalenciaDR]
        print(Fore.GREEN, "--------------TrasladosP------------------------")
        print(Fore.GREEN + "BaseP es:", BaseP[0])
        print(Fore.GREEN + "ImporteP es:", ImporteP[0])
        print("------------------------------------------------")

        # Calcular sumatorias
        sumatoria = '(' + ' + '.join(
            [f"{BaseT[i]}/{EquivalenciaDR[i]}" for i in range(len(BaseT))]) + ')'
        sumatoriaimporte = '(' + ' + '.join(
            [f"{importeT[i]}/{EquivalenciaDR[i]}" for i in range(len(importeT))]) + ')'

        print(Fore.RED, "La sumatoria de BaseP es: ", sumatoria, "=", BaseP[0])
        print(Fore.BLUE, "La sumatoria de ImporteP es: ",
              sumatoriaimporte, "=", ImporteP[0])
