from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Simulation de ton état de jeu
game_state = {"towers": []}


class TowerData(BaseModel):
    towerId: str
    x: int
    y: int


# --- CORRECTIF 422 : Modèle pour la requête ---
class TowerRequest(BaseModel):
    towerId: str


# ----------------------------------------------


@app.post("/tower/place")
def place_tower(request: TowerRequest):  # On utilise le modèle ici
    towerId = request.towerId

    print(f"Reçu towerId: {towerId}")  # Log pour debug

    if towerId == "LECTEUR_PORTE_1":
        data = TowerData(towerId=towerId, x=250, y=250)
    elif towerId == "LECTEUR_PORTE_2":
        data = TowerData(towerId=towerId, x=650, y=200)
    else:
        # Cas par défaut (ex: un badge inconnu)
        data = TowerData(towerId=towerId, x=950, y=450)

    game_state["towers"].append(data.dict())

    return {"message": "Tower placed", "current": game_state["towers"]}


@app.get("/state")
def get_state():
    return game_state
