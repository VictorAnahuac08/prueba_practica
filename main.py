import os
import base64
import requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_FILE = os.getenv("GITHUB_FILE")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")


def github_url():
    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    )


def get_csv():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    params = {
        "ref": GITHUB_BRANCH
    }

    response = requests.get(
        github_url(),
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="No fue posible obtener el CSV desde GitHub"
        )

    data = response.json()

    content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]

    return content, sha


def save_csv(content, sha):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    body = {
        "message": "Actualizar productos.csv desde la API",
        "content": encoded_content,
        "sha": sha,
        "branch": GITHUB_BRANCH
    }

    response = requests.put(
        github_url(),
        headers=headers,
        json=body
    )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=500,
            detail="No fue posible actualizar el CSV en GitHub"
        )

    return response.json()


def parse_csv(content):
    lines = content.strip().splitlines()

    headers = lines[0].split(",")

    rows = []

    for line in lines[1:]:
        values = line.split(",")

        row = dict(zip(headers, values))
        rows.append(row)

    return headers, rows


def build_csv(headers, rows):
    lines = [",".join(headers)]

    for row in rows:
        lines.append(
            ",".join(str(row[h]) for h in headers)
        )

    return "\n".join(lines) + "\n"


class ProductoPUT(BaseModel):
    nombre: str
    precio: float


class ProductoPATCH(BaseModel):
    nombre: str | None = None
    precio: float | None = None


@app.put("/productos/{producto_id}")
def actualizar_producto(
    producto_id: int,
    producto: ProductoPUT
):
    content, sha = get_csv()

    headers, rows = parse_csv(content)

    encontrado = False

    for row in rows:
        if int(row["id"]) == producto_id:
            row["nombre"] = producto.nombre
            row["precio"] = str(producto.precio)
            encontrado = True
            break

    if not encontrado:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    new_content = build_csv(headers, rows)

    save_csv(new_content, sha)

    return {
        "mensaje": "Producto actualizado",
        "producto": producto_id
    }


@app.patch("/productos/{producto_id}")
def modificar_producto(
    producto_id: int,
    cambios: ProductoPATCH
):
    content, sha = get_csv()

    headers, rows = parse_csv(content)

    encontrado = False

    for row in rows:
        if int(row["id"]) == producto_id:

            if cambios.nombre is not None:
                row["nombre"] = cambios.nombre

            if cambios.precio is not None:
                row["precio"] = str(cambios.precio)

            encontrado = True
            break

    if not encontrado:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    new_content = build_csv(headers, rows)

    save_csv(new_content, sha)

    return {
        "mensaje": "Producto modificado",
        "producto": producto_id
    }


@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):

    content, sha = get_csv()

    headers, rows = parse_csv(content)

    nuevos_rows = [
        row for row in rows
        if int(row["id"]) != producto_id
    ]

    if len(nuevos_rows) == len(rows):
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado"
        )

    new_content = build_csv(headers, nuevos_rows)

    save_csv(new_content, sha)

    return {
        "mensaje": "Producto eliminado",
        "producto": producto_id
    }
