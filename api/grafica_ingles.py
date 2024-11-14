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
db = client["test2"]
collection = db["measurements"]

# Función para obtener datos de MongoDB
def get_data(from_date, to_date, metric_type):
    pipeline = [
        {
            "$lookup": {
                "from": "sensors",
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
                "from": "concentrators",
                "localField": "sensor_doc.concentrator",
                "foreignField": "_id",
                "as": "concentrator_doc"
            }
        },
        {
            "$unwind": "$concentrator_doc"
        },
        {
            "$lookup": {
                "from": "locations",
                "localField": "concentrator_doc.location",
                "foreignField": "_id",
                "as": "location_doc"
            }
        },
        {
            "$unwind": "$location_doc"
        },
        {
            "$match": {
                f"metrics.{metric_type}": { "$exists": True },
                "sensor_doc.type": metric_type,
                "concentrator_doc.board": "raspberrypy",
                "location_doc.area": "Encinal",
                "location_doc.facility": "laboratory1"
            }
        },
        {
            "$match": {
                "timestamp": {
                    "$gte": from_date,
                    "$lte": to_date
                }
            }
        },
        {
            "$sort": { "timestamp": 1 },
            "$sort": { "type": 1 },
            "$sort": { "area": 1 },
            "$sort": { "board": 1 }
        },
        {
            "$group": {
                "_id": {
                    "year": { "$year": "$timestamp" },
                    "month": { "$month": "$timestamp" },
                    "day": { "$dayOfMonth": "$timestamp" },
                    "hour": { "$hour": "$timestamp" },
                    "minute": { "$minute": "$timestamp" },
                    "second": { "$second": "$timestamp" },
                    "millisecond": { "$millisecond": "$timestamp" }
                },
                "__value": { "$first": f"$metrics.{metric_type}" },
                "__timestamp": { "$first": "$timestamp" }
            }
        },
        {
            "$addFields": {
                "__name": { "$literal": metric_type.upper() }
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
    data = [doc for doc in result]
    #print(data)
    #for doc in result:
    #    data.append(doc)
        
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
    metric_types = ["temperature", "humidity", "pressure"]
    with app.app_context():
        while True:
            for metric in metric_types:
                # Si es la primera vez que se ejecuta, obtener los últimos 5 segundos
                if last_sent_timestamp is None:
                   from_date = datetime.utcnow() - timedelta(seconds=5)
                else:
                    from_date = last_sent_timestamp
                to_date = datetime.utcnow()
                data = get_data(from_date, to_date, metric)
                serialized_data = serialize_data(data)
                socketio.emit("new_data", {metric: serialized_data})
                time.sleep(0.25)  # Esperar 10 segundos antes de enviar datos nuevamente
            
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