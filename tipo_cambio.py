import requests
from datetime import datetime, timedelta

# Configuración de la API
token = "a0d9d68a166b6565e59872885d9bb2927abd03f00acdcadded548b96684dc93d"
url = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/SF43718/datos/{fecha_ini}/{fecha_fin}?token={token}"

# Fechas de inicio y fin
today = datetime.now()
format = today.strftime('%Y-%m-%d')

# Inicializar la fecha de inicio
fecha_ini = format

# Intentar hasta tres días atrás si la respuesta está vacía
for i in range(4):  # Del día actual hasta tres días antes
    fecha_ini = (today - timedelta(days=i)).strftime('%Y-%m-%d')
    fecha_fin = format  # Fecha actual
    
    # Formatear la URL
    formatted_url = url.format(fecha_ini=fecha_ini, fecha_fin=fecha_fin, token=token)

    # Realizar la solicitud GET
    response = requests.get(formatted_url)

    # Verificar el estado de la respuesta
    if response.status_code == 200:
        data = response.json()
        if data['bmx']['series'][0]['datos']:  # Comprobar si hay datos
            print(f"Datos obtenidos para la fecha: {fecha_ini}")
            print(data)  # Procesar los datos como necesite
            break  # Salir del bucle si se obtienen datos
        else:
            print(f"No hay datos para la fecha: {fecha_ini}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
