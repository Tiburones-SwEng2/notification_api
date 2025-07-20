from flask import Flask, request
from flasgger import Swagger
import requests
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from flask_cors import CORS
import requests
from flask import Response
from flask_jwt_extended import jwt_required, JWTManager
from prometheus_client import Counter, Histogram, generate_latest
import time
from functools import wraps

load_dotenv()

app = Flask(__name__)
swagger = Swagger(app) 
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
app.config["JWT_SECRET_KEY"] = "lkhjap8gy2p 03kt"
jwt = JWTManager(app)

app.config.update(
    dict(
        MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
        MAIL_SERVER = 'smtp.gmail.com',
        MAIL_PORT = 587,
        MAIL_USE_TLS = True,
        MAIL_USE_SSL = False,
    )
)

mail = Mail(app)

# MÉTRICAS
REQUEST_COUNT = Counter('notification_http_requests_total', 'Total Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('notification_http_request_duration_seconds', 'Request Latency', ['endpoint'])
ERROR_COUNT = Counter('notification_http_request_errors_total', 'Total Errors', ['endpoint'])

def monitor_metrics(f):
    """Decorador para monitorear métricas de Prometheus"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        endpoint = request.endpoint or 'unknown'
        method = request.method
        
        # Incrementar contador de requests
        REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
        
        try:
            # Ejecutar la función
            response = f(*args, **kwargs)
            return response
        except Exception as e:
            # Incrementar contador de errores
            ERROR_COUNT.labels(endpoint=endpoint).inc()
            raise
        finally:
            # Medir latencia
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
    
    return decorated_function

@app.route('/filteredDonations', methods=['GET'])
@jwt_required()
@monitor_metrics
def getFilteredDonations():
    """
    List the donations with applied filters
    ---
    parameters:
        - in : header
          name: Authorization
          required: true
          type: string
          description: "Formato: Bearer [Token]"

        - in: query
          name: category 
          schema:
            type: string
          required: false

        - in: query
          name: city 
          schema:
            type: string
          required: false

        - in: query
          name: condition 
          schema:
            type: string
          required: false
    
    responses:
        200:
            description: Filtered donations returned successfully
    """
    category = request.args.get("category")
    city = request.args.get("city")
    condition = request.args.get("condition")

    token = request.headers.get("Authorization")

    headers = {
        "Authorization": token
    }

    url = "http://localhost:5000/api/donations"

    donations = requests.get(url, headers=headers).json()


    filtered_donations = []
    for donation in donations:
        if category and donation["category"] != category:
            continue
        if city and donation["city"] != city:
            continue
        if condition and donation["condition"] != condition:
            continue

        filtered_donations.append(donation)

    return filtered_donations, 200

@app.route('/sendNotification', methods=['POST'])
@jwt_required()
@monitor_metrics
def sendNotification():
    """
    Send a notification to the donor saying someone is interested in their donation
    ---
            
    parameters:
        - in : header
          name: Authorization
          required: true
          type: string
          description: "Formato: Bearer [Token]"
            
        - in: body
          name: donation_information
          schema:
            type: object
            required:
                - email
                - id
                - description
            properties:
                email:
                    type: string
                    example: prueba1@example.com
                id:
                    type: string
                    example: 6844c9dd3894943e5eeec9b1
                description:
                    type: string
                    example: Conjunto de chaquetas
    
    responses:
        200:
            description: Notification sent successfully
        400:
            description: Not enough information or 
        500: 
            description: The availability of the donation could not be updated
    """
    data = request.get_json()
    email = data["email"]
    donation_id = data["id"]

    if not email or not donation_id:
        return {"error": "No se cuenta con la informacion suficiente para realizar la notificacion"}

    msg = Message(
        subject="¡Alguien está interesado en tu donación!",
        sender=os.getenv('MAIL_USERNAME'),
        recipients=[email],
        body=f"""Hola, ¡alguien se ha interesado en una de tus donaciones! En los próximos días, la persona interesada se pondrá en contacto contigo para coordinar la entrega. ¡Gracias por tu generosidad!
        
        Descripcion del producto: {data["description"]}"""
    )

    try:
        mail.send(msg)
    except:
        return {"error": f"No se pudo realizar el envio de la notificacion"}, 400
    
    try:
        requests.put(f"http://localhost:5000/api/donations/{donation_id}")
    except :
        return {"error": f"No se pudo actualizar la disponibilidad de la donacion"}, 500


    return {"mensaje": "La notificacion fue enviada correctamente"}, 200

@app.route("/proxy-image/<filename>")
@jwt_required()
@monitor_metrics
def proxy_image(filename):
    """
    Busca y envia una imagen que tenga el nombre indicado en el parametro filename
    ---
    parameters:
        - in : header
          name: Authorization
          required: true
          type: string
          description: "Formato: Bearer [Token]"

        - in: path
          name: filename
          required: true
          schema:
            type: string
          description: Nombre de la imagen que se va a buscar.
    responses:
        200:
            description: Imagen retornada con éxito 
            content:
              image/png:
                schema:
                  type: string
                  format: binary
              image/jpeg:
                schema:
                  type: string
                  format: binary
              image/jpg:
                schema:
                  type: string
                  format: binary
        404:
            description: Imagen no encontrada
    """
    url = f"http://localhost:5000/api/uploads/{filename}"
    #token = request.headers.get("Authorization")

    # headers = {
    #     "Authorization": token
    # }

    response = requests.get(url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers['Content-Type'])
    else:
        return "Imagen no encontrada", 404

@app.route("/metrics", methods=["GET"])
def metrics():
    """
    Endpoint para exponer métricas de Prometheus
    ---
    tags:
      - Métricas
    responses:
      200:
        description: Métricas de Prometheus
        content:
          text/plain:
            schema:
              type: string
    """
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}



if __name__ == "__main__":
    app.run(debug=True, port=5001)