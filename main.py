from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Configuration CORS (Autorise ton frontend React/Vue/etc)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ],  # J'ai ajouté "*" pour faciliter les tests
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire
game_state = {"towers": [], "players": []}


# Modèle pour stocker les données d'une tour
class TowerData(BaseModel):
    towerId: str
    x: int
    y: int


# --- CORRECTIF 422 : Modèle pour recevoir la requête ---
class TowerRequest(BaseModel):
    towerId: str


# -------------------------------------------------------


@app.post("/tower/place")
def place_tower(request: TowerRequest):  # Utilisation du modèle Pydantic
    towerId = request.towerId
    print(f"Reçu towerId: {towerId}")  # Log pour debug

    # Logique de positionnement selon l'ID reçu
    # Note : Assure-toi que ces IDs correspondent à ce que ton Node.js envoie !
    if towerId == "LECTEUR_PORTE_1" or towerId == "LECTEUR_1":
        data = TowerData(towerId=towerId, x=250, y=250)
    elif towerId == "LECTEUR_2":
        data = TowerData(towerId=towerId, x=650, y=200)
    elif towerId == "LECTEUR_PORTE_3":
        data = TowerData(towerId=towerId, x=950, y=450)
    else:
        return {"error": "Unknown towerId"}

    # Ajout au jeu
    game_state["towers"].append(data.dict())

    return {"message": "Tower placed", "current": game_state["towers"]}


@app.get("/state")
def get_state():
    return game_state


@app.post("/players")
def add_player(
    playerId: str,
):  # Ici c'est un Query Param (?playerId=...), si tu veux du JSON, utilise aussi un BaseModel
    if "players" not in game_state:
        game_state["players"] = []

    game_state["players"].append({"playerId": playerId})
    return {"message": "Player added", "current": game_state.get("players", [])}

@app.post("/reset")
def reset_game():
    game_state.clear()
    game_state["towers"] = []
    return {"message": "Game reset", "current": game_state}

