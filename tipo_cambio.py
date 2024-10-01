import requests
from datetime import datetime
# Configuración de la API
token = "a0d9d68a166b6565e59872885d9bb2927abd03f00acdcadded548b96684dc93d"
url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/{fecha_ini}/{fecha_fin}?token={token}"

# Fechas de inicio y fin
today = datetime.now()
format = today.strftime('%Y-%m-%d')
fecha_ini = format  # Cambia esto a la fecha deseada
fecha_fin = format  # Cambia esto a la fecha deseada

# Formatear la URL
formatted_url = url.format(fecha_ini=fecha_ini, fecha_fin=fecha_fin, token=token)

# Realizar la solicitud GET
response = requests.get(formatted_url)

# Verificar el estado de la respuesta
if response.status_code == 200:
    data = response.json()
    print(data)  # Procesar los datos como necesites
else:
    print(f"Error: {response.status_code} - {response.text}")

print(format)   