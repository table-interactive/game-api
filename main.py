from typing import Dict, List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIG : coordonnées alignées sur la map du front ---
BORNE_CONFIG = {
    "LECTEUR_PORTE_1": {"x": 250, "y": 250, "name": "Zone Entrée"},     # début du chemin
    "LECTEUR_PORTE_2": {"x": 600, "y": 360, "name": "Zone Milieu"},     # zone centrale du coude
    "BORNE_JEU_3": {"x": 950, "y": 560, "name": "Zone Sortie"},         # proche de la fin du chemin
    "BORNE_MOUVEMENT": {"type": "GLOBAL_EVENT"},
}

TAG_MAPPING = {
    "E2 45 88 A1": "Archer",
    "A4 21 55 B2": "Swordsman",
    "CC 12 99 00": "Mage",
    "DEFAULT": "Healer",
}

game_state = {
    "towers": [],
    "events": [],
    "last_rfid": None,
    "players": [],
}


class GameEventRequest(BaseModel):
    towerId: str
    rfidTag: Optional[str] = None
    action: Optional[str] = None


@app.post("/tower/place")
def handle_game_event(request: GameEventRequest):
    device_id = request.towerId.strip()

    # --- GESTION DU MOUVEMENT ---
    if "MOUVEMENT" in device_id.upper() or "PORTE_2" in device_id.upper() or request.action == "movement":
        print(f"🌊 VAGUE DÉCLENCHÉE par {device_id}")
        event = {"type": "START_WAVE", "source": device_id}
        game_state["events"].append(event)
        return {"status": "wave_started", "events": game_state["events"]}

    # --- GESTION DES TOURS ---
    if device_id in BORNE_CONFIG:
        config = BORNE_CONFIG[device_id]
        rfid = request.rfidTag
        tower_type = TAG_MAPPING.get(rfid, TAG_MAPPING["DEFAULT"])

        print(f"🏰 Tour {tower_type} placée en {config['name']} ({config['x']}, {config['y']})")

        new_tower = {
            "towerId": device_id,
            "towerType": tower_type,
            "x": config["x"],
            "y": config["y"],
        }

        existing_index = next(
            (i for i, t in enumerate(game_state["towers"]) if t["towerId"] == device_id),
            None,
        )
        if existing_index is not None:
            game_state["towers"][existing_index] = new_tower
        else:
            game_state["towers"].append(new_tower)

        game_state["last_rfid"] = rfid
        return {"status": "tower_placed", "towers": game_state["towers"]}

    return {"error": "Unknown device or missing data"}


@app.get("/state")
def get_state():
    return game_state


@app.post("/reset")
def reset_game():
    game_state["towers"].clear()
    game_state["events"].clear()
    game_state["last_rfid"] = None
    game_state["players"].clear()
    return {"message": "Game reset", "current": game_state}
