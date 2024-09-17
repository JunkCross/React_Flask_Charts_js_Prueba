from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)  # Permite CORS en todas las rutas y orígenes

# Conexión a MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["test"]
collection = db["mediciones"]

# Función para obtener datos de MongoDB
def get_data(from_date, to_date):
    pipeline = [
        {
            "$lookup": {
                "from": "sensores",
                "localField": "sensor",
                "foreignField": "_id",
                "as": "sensor_doc"
            }
        },
        {
            "$unwind": "$sensor_doc"
        },
        {
            "$lookup": {
                "from": "concentradores",
                "localField": "sensor_doc.concentrador",
                "foreignField": "_id",
                "as": "concentrador_doc"
            }
        },
        {
            "$unwind": "$concentrador_doc"
        },
        {
            "$lookup": {
                "from": "ubicaciones",
                "localField": "concentrador_doc.ubicación",
                "foreignField": "_id",
                "as": "ubicacion_doc"
            }
        },
        {
            "$unwind": "$ubicacion_doc"
        },
        {
            "$match": {
                "magnitudes.temperatura": { "$exists": True },
                "sensor_doc.tipo": "temperatura",
                "concentrador_doc.placa": "raspberrypy",
                "ubicacion_doc.área": "Encinal",
                "ubicacion_doc.recinto": "laboratorio1"
            }
        },
        {
            "$match": {
                "fecha": {
                    "$gte": from_date,
                    "$lte": to_date
                }
            }
        },
        {
            "$sort": { "fecha": 1 },
            "$sort": { "tipo": 1 },
            "$sort": { "área": 1 },
            "$sort": { "placa": 1 }
        },
        {
            "$group": {
                "_id": {
                    "year": { "$year": "$fecha" },
                    "month": { "$month": "$fecha" },
                    "day": { "$dayOfMonth": "$fecha" },
                    "hour": { "$hour": "$fecha" },
                    "minute": { "$minute": "$fecha" },
                    "second": { "$second": "$fecha" },
                    "millisecond": { "$millisecond": "$fecha" }
                },
                "__value": { "$first": "$magnitudes.temperatura" },
                "__timestamp": { "$first": "$fecha" }
            }
        },
        {
            "$addFields": {
                "__name": { "$literal": "TEMPERATURA" }
            }
        },
        {
            "$sort": { "__timestamp": 1 }
        },
        {
            "$project": { 
                "_id": 0
            }
        }
    ]
    result = collection.aggregate(pipeline)
    #print(pipeline)
    #print(result)
    #return list(result)
    data = []
    #print(data)
    for doc in result:
        data.append(doc)
        
    #print("QUE PEDO:",data)    
    return data

def serialize_data(data):
    for item in data:
        if isinstance(item['__timestamp'], datetime):
            item['__timestamp'] = item['__timestamp'].isoformat()  # Convierte a formato ISO 8601
    return data

# Variable para almacenar el último timestamp
last_sent_timestamp = None

def send_data():
    global last_sent_timestamp
    with app.app_context():
        while True:
            # Si es la primera vez que se ejecuta, obtener los últimos 5 segundos
            if last_sent_timestamp is None:
                from_date = datetime.now() - timedelta(seconds=5)
            else:
                from_date = last_sent_timestamp

            to_date = datetime.now()
            #print(from_date)
            #print(to_date)
            data = get_data(from_date, to_date)
            #print("Datos obtenidos:", data)
            
            serialized_data = serialize_data(data)
            socketio.emit("new_data", serialized_data)
            time.sleep(0.24)  # Esperar 10 segundos antes de enviar datos nuevamente
            
            """
            if data:
                # Actualizar el timestamp con el último dato enviado
                last_sent_timestamp = max(item["__timestamp"] for item in data)

                # Serializar y enviar los datos
                serialized_data = serialize_data(data)
                socketio.emit("new_data", serialized_data)

            time.sleep(0.250)  # Intervalo de 250ms
            """
            print(f"Sending data at {datetime.now()}: {data}")
            

# Intervalo de 250ms
socketio.start_background_task(send_data)

# Ruta para probar la conexión
@app.route("/")
def index():
    return "Conexión establecida"

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, use_reloader=False)