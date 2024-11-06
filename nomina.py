from datetime import datetime
from decimal import Decimal
from lxml import etree
from colorama import Fore, Style

xml_string = open('prueba.xml', 'rb').read()
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


