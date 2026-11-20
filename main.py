import os
import base64
import requests
import pandas as pd

from io import StringIO
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


app = FastAPI()


# ============================================================
# CONFIGURACIÓN DE GITHUB
# ============================================================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_FILE = os.getenv("GITHUB_FILE")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")


# ============================================================
# FUNCIONES PARA LEER Y GUARDAR EL CSV
# ============================================================

def github_url():
    """
    Construye la URL de la API de GitHub
    que apunta al archivo CSV.
    """

    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/"
        f"{GITHUB_FILE}"
    )


def get_csv():
    """
    Descarga el CSV desde GitHub.

    Regresa:
        df  -> DataFrame con los datos
        sha -> SHA actual del archivo en GitHub
    """

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(
        github_url(),
        headers=headers,
        params={"ref": GITHUB_BRANCH}
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="No se pudo leer el archivo desde GitHub"
        )

    data = response.json()

    # GitHub guarda el contenido en Base64
    content = base64.b64decode(data["content"]).decode("utf-8")

    # Convertimos el CSV en DataFrame
    df = pd.read_csv(StringIO(content))

    return df, data["sha"]


def save_csv(df, sha):
    """
    Guarda un DataFrame actualizado en GitHub.

    Parámetros:
        df  -> DataFrame que queremos guardar
        sha -> SHA actual del archivo
    """

    # Convertimos el DataFrame a CSV
    csv_content = df.to_csv(index=False)

    # GitHub requiere el contenido en Base64
    encoded_content = base64.b64encode(
        csv_content.encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "message": "Actualizar datos desde FastAPI",
        "content": encoded_content,
        "sha": sha,
        "branch": GITHUB_BRANCH
    }

    response = requests.put(
        github_url(),
        headers=headers,
        json=data
    )

    if response.status_code not in [200, 201]:
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar el archivo en GitHub"
        )

    return True


# ============================================================
# MODELOS PYDANTIC
# ============================================================

class Producto(BaseModel):
    nombre: str
    precio: float


class ProductoPatch(BaseModel):
    nombre: str | None = None
    precio: float | None = None


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/productos")
def obtener_productos():

    # Leer el CSV desde GitHub
    df, sha = get_csv()

    # Convertir el DataFrame a una lista de diccionarios
    productos = df.to_dict(orient="records")

    return {
        "productos": productos
    }

@app.get("/productos/prueba")
def prueba_guardado():

    # Leer el CSV
    df, sha = get_csv()

    # Modificar el DataFrame
    df["precio"] = df["precio"] * 1.10

    # Guardar el DataFrame actualizado
    save_csv(df, sha)

    return {
        "mensaje": "Los precios fueron actualizados",
        "productos": df.to_dict(orient="records")
    }
  

@app.post("/productos")
def crear_producto(producto: Producto):

    # TODO:
    # 1. Leer el CSV
    # 2. Crear un nuevo ID
    # 3. Crear el nuevo registro
    # 4. Agregarlo al DataFrame
    # 5. Guardar el DataFrame en GitHub
    # 6. Regresar el producto creado

    pass


@app.put("/productos/{producto_id}")
def reemplazar_producto(
    producto_id: int,
    producto: Producto
):

    # TODO:
    # 1. Leer el CSV
    # 2. Buscar el producto por ID
    # 3. Reemplazar nombre y precio
    # 4. Guardar el DataFrame en GitHub
    # 5. Regresar el producto actualizado

    pass


@app.patch("/productos/{producto_id}")
def modificar_producto(
    producto_id: int,
    producto: ProductoPatch
):

    # TODO:
    # 1. Leer el CSV
    # 2. Buscar el producto por ID
    # 3. Modificar solamente los campos recibidos
    # 4. Guardar el DataFrame en GitHub
    # 5. Regresar el producto actualizado

    pass


@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):

    # TODO:
    # 1. Leer el CSV
    # 2. Buscar el producto por ID
    # 3. Eliminar el registro
    # 4. Guardar el DataFrame en GitHub
    # 5. Regresar un mensaje de confirmación

    pass
