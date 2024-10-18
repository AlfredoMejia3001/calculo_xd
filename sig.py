from suds.client import Client
import logging
import base64
 
# Configurar el nivel de log para depuración

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
    
    # Guardar el XML estampado
    with open("stamp.xml", "w") as archivo:
        archivo.write(str(xml))
    
    # Guardar la solicitud SOAP
    with open('request.xml', 'w') as req_file:
        req_file.write(str(client.last_sent()))
    
    # Guardar la respuesta SOAP
    with open('response.xml', 'w') as res_file:
        res_file.write(str(client.last_received()))