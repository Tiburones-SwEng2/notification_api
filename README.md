# API REST - Modulo de consulta y solicitud de recursos

Este módulo se encarga de realizar el filtrado de las donaciones basado en la categoría, ciudad o condición de la donación. Adicionalmente, también se encarga del envío de notificaciones a los donadores cuando alguien está interesado en ellas.

## Ejecucion de la API

Para ejecutar la API primero hay que crear un entorno virtual y activarlo con los siguientes comandos:

```bash
python -m venv venv
.\venv\Scripts\activate
```

Una vez dentro del entorno virtual, se deben instalar las librerias usados con el siguiente comando:

```bash
pip install -r requirements.txt
```

Por ultimo se ejecuta la API con el siguiente comando:

```bash
python app.py
```

Esto hara que la API se ejecuta en la URL http://127.0.0.1:5001 y su documentacion en Swagger se encontrara en http://127.0.0.1:5001/apidocs

## Endpoints disponibles

### GET /filteredDonations

Encargado de mostrar las donaciones haciendo uso de filtros. Los filtros son entregados como query parameters. Se pueden definir 3 filtros distintos:

- city
- condition
- category

#### Ejemplo

URL: http://127.0.0.1:5001/filteredDonations?city=Manizales

##### Respuesta

```json
{
  "address": null,
  "available": true,
  "category": "Ropa",
  "city": "Manizales",
  "condition": "Nuevo",
  "created_at": "2025-06-07T23:23:09.166000",
  "description": "Variedad de abrigos",
  "email": "nixaf16433@gotemv.com",
  "expiration_date": null,
  "id": "6844c9dd3894943e5eeec9b1",
  "image_url": null,
  "title": "Ropa de invierno"
}
```

### POST /sendNotification

Encargado de enviar notificaciones a los donadores cuando alguien esta interesado en alguna de sus donaciones.

#### Ejemplo

URL: http://localhost:5001/sendNotification

Body:

```json
{
  "description": "Variedad de abrigos",
  "email": "nixaf16433@gotemv.com",
  "id": "6844c9dd3894943e5eeec9b1"
}
```

##### Respuesta

```json
{
  "mensaje": "La notificacion fue enviada correctamente"
}
```
