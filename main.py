from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En dev, on laisse tout passer
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION HARDCODÉE (La "Carte" physique) ---
# Associe le nom de l'Arduino (DEVICE_ID) à une position X/Y sur l'écran
BORNE_CONFIG = {
    "BORNE_JEU_1": {"x": 150, "y": 300, "name": "Zone Entrée"},
    "BORNE_JEU_2": {"x": 400, "y": 100, "name": "Zone Centre"},
    "BORNE_JEU_3": {"x": 650, "y": 300, "name": "Zone Sortie"},
    # Le capteur de mouvement n'a pas de position fixe, il déclenche un événement global
    "BORNE_MOUVEMENT": {"type": "GLOBAL_EVENT"},
}

# --- CONFIGURATION DES BADGES (Le "Grimoire") ---
# Associe un ID de badge RFID à un Type de Tour (Feu, Glace, etc.)
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
    towerId: str  # ex: "BORNE_JEU_1"
    rfidTag: Optional[str] = None  # ex: "E2 45 88..." (Seulement si RFID)
    action: Optional[str] = None  # ex: "movement" (Seulement si Mouvement)


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

        game_state["last_rfid"] = rfid
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
