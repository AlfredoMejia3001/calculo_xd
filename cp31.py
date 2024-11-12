from datetime import datetime
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style

xml_string = open('prueba2.xml', 'rb').read()
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


def realizar_calculos_cartaporte31(namespaces):
    if xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:Autotransporte', namespaces=namespaces):
        pesoKG=xml_etree.xpath('.//cartaporte31:Mercancias/cartaporte31:Mercancia/@PesoEnKg', namespaces=namespaces)
        pesoBrutoTotal= xml_etree.xpath('.//cartaporte31:Mercancias/@PesoBrutoTotal', namespaces=namespaces)
        suma_peso = sum(float(peso) for peso in pesoKG)
        
        if suma_peso != float(pesoBrutoTotal[0]):
            suma_pesoSTR=int(suma_peso)
            if suma_pesoSTR != int(pesoBrutoTotal[0]):
                print('Los pesos no coinciden')
                print(f"{suma_pesoSTR} != {pesoBrutoTotal[0]}")
            else:
                print('Los pesos coinciden')
                print(f"{suma_pesoSTR} = {pesoBrutoTotal[0]}")
        else:
            print('Los pesos coinciden')
            print(f"{suma_peso} = {pesoBrutoTotal[0]}")

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
                print(f"{suma_pesoSTR} != {pesoBrutoTotal[0]}")
            else:
                print('Los pesos coinciden')
                print(f"{suma_pesoSTR} = {pesoBrutoTotal[0]}")
        else:
            print('Los pesos coinciden')
            print(f"{suma_peso} = {pesoBrutoTotal[0]}")        
        suma_pesoN = sum(float(peso) for peso in pesoNeto)
        if suma_pesoN != (pesoNetoTotal[0]):
            suma_pesoNT=int(suma_pesoN)
            print(suma_pesoNT)
            if suma_pesoNT != int(pesoNetoTotal[0]):
                print('Los pesos no coinciden')
                print(f"{suma_pesoNT} != {pesoNetoTotal[0]}")
            else:
                print('Los pesos coinciden neto')
                print(f"{suma_pesoNT} = {pesoNetoTotal[0]}")
        else:
            print('Los pesos coinciden neto 1')
            print(f"{suma_pesoN} = {float(pesoNetoTotal[0])}")      

def NumTotalMercancias(namespaces):           
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
def ferroviario(namespaces):   
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
        print('Son iguales')


#--------------------------------------------TotalDistRec-----------------------------------------------#
def total_dist(namespaces):
    total_dist_rec = xml_etree.xpath('.//cartaporte31:CartaPorte/@TotalDistRec', namespaces=namespaces)
    print(total_dist_rec[0],"km")
    distancia_recorrida = xml_etree.xpath('.//cartaporte31:Ubicaciones/cartaporte31:Ubicacion/@DistanciaRecorrida', namespaces=namespaces)
    total_dist = sum(float(dist) for dist in distancia_recorrida)
    print(total_dist, "km")

