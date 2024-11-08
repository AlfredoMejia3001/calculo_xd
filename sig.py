from datetime import datetime
from suds.client import Client
import logging
import base64
from lxml import etree


xml="prueba.xml"
xml_string = open(
    xml, "rb").read()
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
if nodo:  # Check if the list is not empty
    emisor = nodo[0]  # Get the first matching node
    emisor.set('Rfc', str(rfc))
    emisor.set('Nombre', str(name))
    emisor.set('RegimenFiscal', str(regi))


with open("prueba.xml", "wb") as f:
        f.write(etree.tostring(xml_etree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8'))
    
# Usuario y contraseña, asignados por FINKOK
username = 'amejia@finkok.com.mx'
password = 'yN8Q4vp,LPQQ6*y'
 
# Leer el archivo XML y codificarlo en base64
def timbrar(xml):
    invoice_path = xml
    with open(invoice_path, 'r') as file:
        xml_content = file.read()
    xml_base64 = base64.b64encode(xml_content.encode('utf-8')).decode('utf-8')
    
    # Consumir el servicio de estampado (stamp service)
    url = "https://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl"
    client = Client(url, cache=None)
    contenido = client.service.sign_stamp(xml_base64, username, password)
    xml = contenido.xml
    
    # Guardar la solicitud SOAP
    with open('request.xml', 'w') as req_file:
        req_file.write(str(client.last_sent()))
    
    # Guardar la respuesta SOAP
    with open('response.xml', 'w') as res_file:
        res_file.write(str(client.last_received()))


timbrar(xml)