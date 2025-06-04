# 3D - Quotes - Backend

**Descripción:** Este es el backend del proyecto "3D - Quotes", desarrollado como parte de un trabajo universitario personal. Implementa una API REST usando **FastAPI** para gestionar cotizaciones de impresión 3D, con autenticación de usuarios y lógica de optimización de parámetros de impresión. El backend se conecta a una base de datos MongoDB usando **Beanie** (ODM asíncrono basado en Pydantic) y **Motor** (driver asíncrono de MongoDB). También incluye hashing de contraseñas con **Passlib** y JWT para autenticación. La aplicación está pensada para comunicarse con un frontend (React/Vite) vía peticiones HTTP.

**Librerías principales (con versión):** A partir de la lista de paquetes del entorno ( `conda list` ) se utilizan:
- **Python** 3.12.9 (versión base).
- **FastAPI** (framework web moderno y de alto rendimiento) – por ejemplo v0.111.0.
- **Uvicorn** (servidor ASGI para Python) – por ejemplo v0.19.0.
- **Beanie** (ODM asíncrono para MongoDB basado en Pydantic) – por ejemplo v1.x.x.
- **Motor** (driver asíncrono oficial de MongoDB) – por ejemplo v3.7.1.
- **Authlib** (biblioteca para OAuth 2.0 y gestión de JWT) – por ejemplo v1.6.0.
- **Passlib** (para hashing de contraseñas, con esquema bcrypt).
- **python-jose** (para operaciones JWT, p.ej. decodificar tokens).
- **Pydantic Settings** (gestiona configuración desde archivo `.env`).
- **python-dotenv** (para cargar variables de entorno desde `.env`).
- **Pymongo** (sólo implícito vía Motor/Beanie, maneja conexiones MongoDB).
- **Otras:** `typing`, `datetime`, `bson` (para ObjectId), etc.

**Tecnologías principales:** FastAPI, Beanie, Uvicorn, Authlib, Python, MongoDB. FastAPI es “un framework moderno, rápido y de alto rendimiento” para construir APIs en Python. Uvicorn es un servidor ASGI asíncrono para Python. Beanie simplifica la interacción con MongoDB como un ODM asíncrono. Authlib permite implementar OAuth/JWT. Todo esto se integra para crear la API.

## Estructura del proyecto

El repositorio tiene la siguiente organización (omitimos la carpeta `.git` y archivos bytecode):

- **`main.py`**: Punto de entrada de la aplicación FastAPI. Define el objeto `app`, configura CORS para permitir peticiones desde el frontend (por ejemplo `http://localhost:3000` o `http://localhost:5173`), inicializa la base de datos en el evento de arranque, e incluye los routers de autenticación (`/auth`), de cotizaciones (`/api/quotes`) y de optimización.

- **`.env`**: Archivo con variables de entorno para configuración (no subir a repositorio si contuviera datos sensibles). Incluye:
  - `MONGO_URI`: cadena de conexión a MongoDB (ej. `mongodb://root:pass@localhost:27017/`).
  - `DATABASE_NAME`: nombre de la base de datos (ej. `quotes_db`).
  - `SECRET_KEY`: clave secreta para firmar JWT.
  Ejemplo proporcionado:
  ```
  MONGO_URI=mongodb://root:Monguitofeliz1234@localhost:27017/?authSource=admin
  DATABASE_NAME=quotes_db
  SECRET_KEY=ChanchitoFeliz1234
  ```

- **`core/`**: Contiene código de configuración y utilidades centrales:
  - **`core/config.py`**: Usa `pydantic-settings` para leer variables de entorno (`.env`). Define la clase `Settings` con `MONGO_URI`, `DATABASE_NAME`, `SECRET_KEY`.
  - **`core/database.py`**: Se encarga de la conexión a MongoDB. La función `initiate_database()` se llama al inicio y realiza la conexión usando Motor (`AsyncIOMotorClient`) y registra los modelos `Quote` y `User` en Beanie. Registra logs de éxito o falla.
  - **`core/auth.py`**: Lógica de autenticación y autorización. Incluye:
    - Contexto de Passlib (`CryptContext`) para hashear y verificar contraseñas con bcrypt.
    - Funciones para crear/verificar JWT usando `python-jose` (`create_access_token`, `verify_token`, etc.).
    - Dependencia `get_current_user` para rutas protegidas (lee el token Bearer y retorna el usuario activo).

- **`models/`**: Define los modelos de datos que se guardan en MongoDB, usando Pydantic/Beanie:
  - **`models/user_model.py`**: Modelo `User` con campos como `username`, `email`, `hashed_password`, `is_active` (verificado), etc. Incluye validaciones para usuario/contraseña.
  - **`models/quote_model.py`**: Modelo `Quote` con campos anidados para cotización de impresión 3D: nombre de cotización, datos de impresora, filamento, energía, modelo 3D, datos comerciales, resumen calculado, fechas, referencias a usuario (`user_id`), etc.
  - **`models/enums/`**: Contiene enumeraciones usadas por los modelos, p.ej. tipos de impresora, colores de filamento, etc. (Clases `Enum` para varios atributos).

- **`schemas/`**: Define los esquemas de datos (Pydantic) para request/response (separados de los modelos de base de datos):
  - **`schemas/user_schema.py`**: 
    - `UserCreateSchema` para el registro (`username`, `email`, `password`, `confirm_password`).
    - `UserLoginSchema` para login (`identifier` (username o email), `password`).
    - `TokenSchema` para la respuesta de acceso (`access_token`, `token_type`).
  - **`schemas/quote_schema.py`**: 
    - `QuoteCreateSchema` con los campos necesarios para crear una cotización (p.ej. `quote_name`, datos anidados de `printer`, `filament`, `energy`, `model`, `commercial`).
    - `QuoteUpdateSchema` con los mismos campos pero todos opcionales (para actualizar).
    - `QuoteOutSchema` para la respuesta (incluye `id`, `user_id`, todos los datos de la cotización, así como campos de resumen, fechas, etc.).
  - **`schemas/optimization_schema.py`**: Define la estructura de la respuesta de optimización (`fast`, `economic`, `balanced`), cada uno con `new_parameters` y `results` (contiene tiempos, costos, desperdicio, etc.).

- **`repositories/`**: Contiene funciones que interactúan directamente con la base de datos (p.ej. consultas Mongo):
  - **`repositories/quote_repository.py`**: Funciones `create_quote`, `get_quote_by_id`, `get_user_quotes`, `update_quote`, `delete_quote`. Cada función usa los modelos de Beanie (`Quote`) para realizar operaciones en la colección.
  - *(En este repositorio, la autenticación de usuario se maneja directamente en `core/auth.py` y no hay repositorio de usuarios separado.)*

- **`services/`**: Lógica de negocio adicional:
  - **`services/quote_service.py`**: Orquesta las llamadas del API a los repositorios. Convierte esquemas Pydantic en modelos, y viceversa. Por ejemplo, `create_quote()` recibe un `QuoteCreateSchema`, crea un `Quote` en la DB, y retorna un `QuoteOutSchema`.
  - **`services/pricing_logic.py`**: Contiene la función `generate_optimization(quote)` que, dado un objeto `Quote`, calcula tres propuestas de optimización (fast, economic, balanced) ajustando parámetros de impresión. Retorna un diccionario con costos y parámetros optimizados para cada modo.

- **`api/`**: Define los routers (endpoints):
  - **`api/auth.py`**: Rutas de autenticación bajo `/auth` (al incluirse con `prefix="/auth"` en `main.py`):
    - `POST /auth/register`: registra nuevo usuario. Recibe JSON con `UserCreateSchema`. Crea usuario (checando duplicados) y retorna token (JWT).
    - `POST /auth/login`: autentica con `identifier` y `password`. Verifica credenciales y retorna JWT.
  - **`api/quotes.py`**: Rutas CRUD para cotizaciones, bajo prefijo `/api/quotes`:
    - `POST /api/quotes/`: Crea cotización nueva. Recibe `QuoteCreateSchema` y retorna `QuoteOutSchema`.
    - `GET /api/quotes/`: Obtiene todas las cotizaciones del usuario autenticado (`get_user_quotes`).
    - `GET /api/quotes/{quote_id}`: Obtiene una cotización por ID (`get_quote_by_id`).
    - `PUT /api/quotes/{quote_id}`: Actualiza una cotización existente (datos de `QuoteUpdateSchema`).
    - `DELETE /api/quotes/{quote_id}`: Elimina una cotización por ID. Retorna código 204 si tuvo éxito.
    Todas estas rutas requieren autenticación: se depende de `get_current_user`, por lo que se debe enviar el token JWT en el header `Authorization: Bearer <token>`.

  - **`api/quote_optimization.py`**: Ruta para optimización de cotización, bajo `/api/quotes`:
    - `GET /api/quotes/{quote_id}/optimize`: Genera tres modos de optimización para la cotización dada. Verifica que exista y pertenezca al usuario. Retorna `OptimizationOutputSchema` con campos `fast`, `economic`, `balanced`. Cada uno incluye nuevos parámetros recomendados y los resultados de costos/tiempo.

- **`README.md` o documentación**: Archivo con instrucciones (no incluido en la ejecución de la aplicación).

- **Archivos de configuración**:
  - `.gitignore`, archivos de entorno, scripts de arranque, etc.

## Conexión con el Frontend

El backend expone una API REST que el frontend (React/Vite) consumirá vía HTTP. Por defecto, el backend corre en `http://localhost:8000`. Las rutas base son:
- Autenticación: `http://localhost:8000/auth/...`
- Cotizaciones: `http://localhost:8000/api/quotes/...`

En `main.py` se definieron los *prefix* `/auth` y `/api/quotes`. El frontend debe incluir en las cabeceras de las peticiones la autorización con el token: `Authorization: Bearer <token>` después de que el usuario inicie sesión.

## Instalación y ejecución

Para ejecutar este backend usando **Miniconda** (o Anaconda):

1. **Clonar o descomprimir** el repositorio. Abrir terminal en la carpeta del backend.
2. **Crear un entorno Conda:**  
   ```bash
   conda create -n 3dquotes-backend python=3.12.9
   conda activate 3dquotes-backend
   ```
3. **Instalar dependencias:** No hay un archivo `environment.yml` proporcionado, así que puede instalar manualmente:
   ```bash
   conda install fastapi uvicorn beanie motor pymongo passlib bcrypt python-jose python-dotenv authlib -c conda-forge
   ```
   (Si alguna librería no está en conda-forge, usar `pip install nombre-lib` dentro del entorno, e.g. `pip install beanie`).
4. **Configuración de entorno:** Copiar el archivo `.env` (ya incluido) o crearlo en la raíz con las variables `MONGO_URI`, `DATABASE_NAME`, `SECRET_KEY`. Asegurarse de que MongoDB esté corriendo y accesible con esas credenciales.
5. **Iniciar la aplicación:**  
   Ejecutar con uvicorn:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   Esto inicia el servidor en `http://localhost:8000` con recarga automática.
6. **Verificar:** Abrir en navegador `http://localhost:8000/docs` para ver la documentación automática de FastAPI (OpenAPI/Swagger) y probar los endpoints.

## Uso de los endpoints

A continuación se detallan las rutas disponibles, su método HTTP, datos de entrada y salida, con ejemplos:

- **`POST /auth/register`** (Registrar usuario)  
  - **Datos recibidos:** JSON con `{ "username": "...", "email": "...", "password": "...", "confirm_password": "..." }`.  
  - **Respuesta:** `201 Created`. JSON con `{ "access_token": "TOKEN", "token_type": "bearer" }`.  
  - **Ejemplo:**  
    ```bash
    curl -X POST http://localhost:8000/auth/register       -H "Content-Type: application/json"       -d '{
        "username": "juanperez",
        "email": "juan@example.com",
        "password": "MiClave123",
        "confirm_password": "MiClave123"
      }'
    ```  
    **Respuesta:**  
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...",
      "token_type": "bearer"
    }
    ```

- **`POST /auth/login`** (Iniciar sesión)  
  - **Datos recibidos:** JSON con `{ "identifier": "...", "password": "..." }`, donde `identifier` es el username o email.  
  - **Respuesta:** `200 OK`. JSON con `{ "access_token": "TOKEN", "token_type": "bearer" }` si las credenciales son válidas.  
  - **Ejemplo:**  
    ```bash
    curl -X POST http://localhost:8000/auth/login       -H "Content-Type: application/json"       -d '{
        "identifier": "juanperez",
        "password": "MiClave123"
      }'
    ```  
    **Respuesta:**  
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...",
      "token_type": "bearer"
    }
    ```

- **`POST /api/quotes/`** (Crear cotización)  
  - **Autorización:** Requiere token en header `Authorization: Bearer <token>`.  
  - **Datos recibidos:** JSON con los campos de `QuoteCreateSchema`. Ejemplo simplificado:  
    ```json
    {
      "quote_name": "MiCotizacion",
      "printer": {
        "name": "Prusa i3",
        "watts": 150.0,
        "type": "FDM",
        "speed": 60.0,
        "nozzle": 0.4,
        "layer": 0.2
      },
      "filament": {
        "type": "PLA",
        "color": "Rojo",
        "diameter": 1.75,
        "unit_cost": 20.0
      },
      "energy": {
        "cost_per_kwh": 0.15
      },
      "model": {
        "weight": 30.0,
        "height": 5.0,
        "infill": 20.0,
        "support": "NONE"
      },
      "commercial": {
        "profit_margin": 10.0
      }
    }
    ```  
  - **Respuesta:** `201 Created`. JSON de `QuoteOutSchema`, p.ej.:  
    ```json
    {
      "id": "65f1...abc",              // _id en MongoDB
      "user_id": "65f1...xyz",
      "quote_name": "MiCotizacion",
      "printer": { ... },
      "filament": { ... },
      "energy": { ... },
      "model": { ... },
      "commercial": { ... },
      "summary": { ... },           // Resumen calculado (costos, tiempo, sugerencias)
      "created_at": "2025-06-01T12:34:56",
      "updated_at": "2025-06-01T12:34:56"
    }
    ```  
  - **Ejemplo:**  
    ```bash
    curl -X POST http://localhost:8000/api/quotes/       -H "Content-Type: application/json"       -H "Authorization: Bearer eyJhbGciOiJI..."       -d '{ ... }'
    ```

- **`GET /api/quotes/`** (Listar cotizaciones del usuario)  
  - **Autorización:** Requiere token.  
  - **Datos recibidos:** Ninguno.  
  - **Respuesta:** `200 OK`. JSON con una lista de cotizaciones (`QuoteOutSchema`) del usuario autenticado. Ejemplo:  
    ```json
    [
      {
        "id": "65f1...abc",
        "user_id": "65f1...xyz",
        "quote_name": "MiCotizacion",
        ... // demás campos como arriba
      },
      {
        "id": "65f1...def",
        "user_id": "65f1...xyz",
        "quote_name": "OtraCotizacion",
        ...
      }
    ]
    ```  
  - **Ejemplo:**  
    ```bash
    curl -X GET http://localhost:8000/api/quotes/       -H "Authorization: Bearer eyJhbGciOiJI..."
    ```

- **`GET /api/quotes/{quote_id}`** (Obtener cotización por ID)  
  - **Autorización:** Requiere token.  
  - **Respuesta:** `200 OK`. JSON de una sola cotización (`QuoteOutSchema`). Si no existe o no pertenece al usuario, devuelve `404 Not Found`.  
  - **Ejemplo:**  
    ```bash
    curl -X GET http://localhost:8000/api/quotes/65f1...abc       -H "Authorization: Bearer eyJhbGciOiJI..."
    ```  

- **`PUT /api/quotes/{quote_id}`** (Actualizar cotización)  
  - **Autorización:** Requiere token.  
  - **Datos recibidos:** JSON con campos de `QuoteUpdateSchema` (todos opcionales). Por ejemplo se puede enviar `{ "quote_name": "NuevoNombre" }` para cambiar solo el nombre.  
  - **Respuesta:** `200 OK`. JSON con la cotización actualizada (`QuoteOutSchema`). Si no existe, `404`.  
  - **Ejemplo:**  
    ```bash
    curl -X PUT http://localhost:8000/api/quotes/65f1...abc       -H "Content-Type: application/json"       -H "Authorization: Bearer eyJhbGciOiJI..."       -d '{ "quote_name": "NombreActualizado" }'
    ```  

- **`DELETE /api/quotes/{quote_id}`** (Eliminar cotización)  
  - **Autorización:** Requiere token.  
  - **Respuesta:** `204 No Content` si se elimina correctamente. Si la cotización no existe, `404 Not Found`.  
  - **Ejemplo:**  
    ```bash
    curl -X DELETE http://localhost:8000/api/quotes/65f1...abc       -H "Authorization: Bearer eyJhbGciOiJI..."
    ```  

- **`GET /api/quotes/{quote_id}/optimize`** (Optimizar cotización)  
  - **Autorización:** Requiere token.  
  - **Respuesta:** `200 OK`. JSON con la optimización en tres modos (`OptimizationOutputSchema`). Ejemplo estructural:  
    ```json
    {
      "fast": {
        "new_parameters": { "speed": 100.0, "layer_height": 0.1, ... },
        "results": {
          "print_time": 2.5,
          "grams_used": 50.0,
          "grams_wasted": 5.0,
          "waste_percentage": 10.0,
          "material_cost": 1.0,
          "energy_cost": 0.5,
          "machine_cost": 2.0,
          "total_cost": 3.5
        }
      },
      "economic": { ... },
      "balanced": { ... }
    }
    ```  
  - **Ejemplo:**  
    ```bash
    curl -X GET http://localhost:8000/api/quotes/65f1...abc/optimize       -H "Authorization: Bearer eyJhbGciOiJI..."
    ```  

Cada endpoint y ejemplo asume que el backend está corriendo en `localhost:8000` y que el usuario ya obtuvo un token vía `/auth/login`.

**Link al repo frontend:** [https://github.com/der-matt02/3D-Platform-Frontend](https://github.com/der-matt02/3D-Platform-Frontend)
