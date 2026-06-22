"Bot de información de citas"
pip install fastapi uvicorn requests
import requests
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

# ---------------------------------------------------------------------
# CONFIGURACIÓN: Cambia esto con los datos de tu servicio final
# ---------------------------------------------------------------------
# Por ejemplo, si los mandas a Notion, Airtable, un CRM o tu base de datos:
DESTINATION_API_URL = "https://api.tu-servicio.com/v1/endpoint"
API_TOKEN = "tu_token_de_seguridad"


@app.post("/webhook/tally")
async def handle_tally_webhook(request: Request):
    try:
        # 1. Recibir el JSON idéntico al que envía Tally
        payload = await request.json()
        
        # Estructura típica de Tally: payload['data']['fields'] o payload['data']
        form_data = payload.get("data", {})
        form_name = form_data.get("formName", "Formulario Tally")
        fields = form_data.get("fields", [])
        
        # 2. Procesar o "mapear" los campos
        # Extraemos los datos basándonos en las etiquetas del formulario
        extracted_info = {}
        for field in fields:
            label = field.get("label")
            value = field.get("value")
            if label:
                extracted_info[label] = value
                
        # Ejemplo de impresión en consola para depurar localmente
        print(f"\n--- Nuevo envío recibido del formulario: {form_name} ---")
        print(f"Datos extraídos: {extracted_info}\n")
        
        # 3. Reemplazar el siguiente módulo (Enviar los datos a otra API)
        headers = {
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Adaptamos el JSON al formato que pide tu destino final
        response = requests.post(
            DESTINATION_API_URL, 
            json=extracted_info, 
            headers=headers
        )
        
        if response.status_code not in [200, 201]:
            print(f"Error enviando datos al destino final: {response.text}")
            raise HTTPException(
                status_code=500, 
                detail="Error al procesar el destino final"
            )
            
        return {
            "status": "success", 
            "message": "Datos de Tally procesados correctamente"
        }
        
    except Exception as e:
        print(f"Error procesando el webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Payload inválido")

# ---------------------------------------------------------------------
# Para ejecutar localmente, escribe esto en tu terminal:
# uvicorn main:app --reload
# ---------------------------------------------------------------------