from flask import Flask, request
from flasgger import Swagger
import requests
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
from flask_cors import CORS
import requests
from flask import Response

load_dotenv()

app = Flask(__name__)
swagger = Swagger(app) 
CORS(app)

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

@app.route('/filteredDonations', methods=['GET'])
def getFilteredDonations():
    """
    List the donations with applied filters
    ---
    parameters:
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

    donations = requests.get("http://localhost:5000/api/donations").json()

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
def sendNotification():
    """
    Send a notification to the donor saying someone is interested in their donation
    ---
    parameters:
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
        sender="from@example.com",
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
def proxy_image(filename):
    url = f"http://localhost:5000/api/uploads/{filename}"
    response = requests.get(url)

    if response.status_code == 200:
        return Response(response.content, content_type=response.headers['Content-Type'])
    else:
        return "Imagen no encontrada", 404


if __name__ == "__main__":
    app.run(debug=True, port=5001)