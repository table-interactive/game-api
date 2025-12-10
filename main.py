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

# --- 1. CONFIGURATION DES EMPLACEMENTS (Aligné sur le Frontend) ---
# On utilise exactement les coordonnées de vos "SLOTS" dans le code React (S1, S2, S3)
BORNE_CONFIG = {
    # Slot 1 (S1) du frontend
    "BORNE_JEU_1": {"x": 250, "y": 250, "name": "Emplacement Haut Gauche"},
    # Slot 2 (S2) du frontend
    "BORNE_JEU_2": {"x": 650, "y": 200, "name": "Emplacement Haut Centre"},
    # Slot 3 (S3) du frontend
    "BORNE_JEU_3": {"x": 950, "y": 450, "name": "Emplacement Bas Droite"},
    # Capteur ultrason
    "BORNE_MOUVEMENT": {"type": "GLOBAL_EVENT"},
}

# --- 2. CONFIGURATION DES BADGES (Aligné sur le Frontend) ---
# On mappe les RFIDs vers les noms exacts attendus par PIXI.js :
# "Archer", "Swordsman", "Mage", "Healer"
TAG_MAPPING = {
    "E2 45 88 A1": "Archer",
    "A4 21 55 B2": "Swordsman",
    "CC 12 99 00": "Mage",
    "DEFAULT": "Healer",  # Si le badge est inconnu
}

# --- ÉTAT DU JEU ---
game_state = {
    "towers": [],  # Liste des tours posées
    "events": [],  # Liste des événements (ex: "WAVE_START")
    "last_rfid": None,
    "players": [],  # Pour compatibilité avec le front
}


# --- MODÈLES DE DONNÉES ---

class GameEventRequest(BaseModel):
    towerId: str
    rfidTag: Optional[str] = None
    action: Optional[str] = None


# --- ROUTES ---

@app.post("/tower/place")
def handle_game_event(request: GameEventRequest):
    """
    Gère placement/remplacement de tours ou détection de mouvement.
    """
    device_id = request.towerId

    # 1. Gestion du mouvement
    if request.action == "movement" or request.action == "movement_detected":
        print(f"🌊 VAGUE DÉCLENCHÉE par {device_id}")
        event = {"type": "START_WAVE", "source": device_id}
        game_state["events"].append(event)
        return {"status": "wave_started", "events": game_state["events"]}

    # 2. Gestion des tours (RFID)
    if device_id in BORNE_CONFIG and request.rfidTag:
        config = BORNE_CONFIG[device_id]
        rfid = request.rfidTag

        tower_type = TAG_MAPPING.get(rfid, TAG_MAPPING["DEFAULT"])
        print(f"🏰 Tour {tower_type} placée en {config['name']} ({config['x']}, {config['y']})")

        new_tower = {
            "towerId": device_id,        # ✅ cohérent avec le front
            "towerType": tower_type,     # ✅ cohérent avec le front
            "x": config["x"],
            "y": config["y"],
        }

        # Remplacement si la borne a déjà une tour
        existing_index = next(
            (
                index
                for (index, d) in enumerate(game_state["towers"])
                if d["towerId"] == device_id
            ),
            None,
        )

        if existing_index is not None:
            game_state["towers"][existing_index] = new_tower
        else:
            game_state["towers"].append(new_tower)

        return {"status": "tower_placed", "towers": game_state["towers"]}

    return {"error": "Unknown device or missing data"}


@app.get("/state")
def get_state():
    """
    Appelé par le frontend toutes les ~secondes pour mettre à jour l'affichage.
    """
    return game_state


@app.post("/reset")
def reset_game():
    """
    Réinitialise complètement le jeu.
    """
    game_state["towers"].clear()
    game_state["events"].clear()
    game_state["last_rfid"] = None
    game_state["players"].clear()
    return {"message": "Game reset", "current": game_state}
