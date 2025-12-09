from typing import Dict, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- État global du jeu ---
game_state = {"towers": [], "players": []}


class TowerData(BaseModel):
    towerId: str
    towerType: str
    x: int
    y: int


class TowerRequest(BaseModel):
    towerId: str
    towerType: str


@app.post("/tower/place")
def place_tower(request: TowerRequest):
    towerId = request.towerId
    towerType = request.towerType

    # --- Gestion des positions prédéfinies ---
    positions = {
        "LECTEUR_PORTE_1": (250, 250),
        "LECTEUR_1": (250, 250),
        "LECTEUR_2": (650, 200),
        "LECTEUR_PORTE_3": (950, 450),
    }

    # --- Cas particulier : lecteur joueur ---
    if towerId == "LECTEUR_PORTE_2":
        if "players" not in game_state:
            game_state["players"] = []
        # éviter les doublons de joueurs
        if not any(p["playerId"] == towerId for p in game_state["players"]):
            game_state["players"].append({"playerId": towerId})
        return {"message": "Player added", "current": game_state.get("players", [])}

    # --- Position de la tour ---
    if towerId in positions:
        x, y = positions[towerId]
        data = TowerData(towerId=towerId, towerType=towerType, x=x, y=y)
    else:
        return {"error": f"Unknown tower ID: {towerId}"}

    # --- Si une tour avec le même ID existe déjà, on la remplace ---
    existing_index = next(
        (i for i, t in enumerate(game_state["towers"]) if t["towerId"] == towerId),
        None,
    )

    if existing_index is not None:
        game_state["towers"][existing_index] = data.dict()
        message = "Tower replaced"
    else:
        game_state["towers"].append(data.dict())
        message = "Tower placed"

    return {"message": message, "current": game_state["towers"]}


@app.get("/state")
def get_state():
    return game_state


@app.post("/reset")
def reset_game():
    game_state.clear()
    game_state["towers"] = []
    game_state["players"] = []
    return {"message": "Game reset", "current": game_state}
