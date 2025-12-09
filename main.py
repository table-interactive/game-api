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
    # Exemples de badges (à remplacer par vos vrais IDs reçus dans les logs)
    "E2 45 88 A1": "FIRE_TOWER",
    "A4 21 55 B2": "ICE_TOWER",
    "CC 12 99 00": "ARCHER_TOWER",
    "DEFAULT": "BASIC_TOWER",  # Si le badge est inconnu
}

# --- ÉTAT DU JEU ---
game_state = {
    "towers": [],  # Liste des tours posées
    "events": [],  # Liste des événements (ex: "WAVE_START")
    "last_rfid": None,  # Pour debug
}

# --- MODÈLES DE DONNÉES ---


# Ce que Node.js nous envoie
class GameEventRequest(BaseModel):
    towerId: str  # ex: "BORNE_JEU_1"
    rfidTag: Optional[str] = None  # ex: "E2 45 88..." (Seulement si RFID)
    action: Optional[str] = None  # ex: "movement" (Seulement si Mouvement)


# Ce qu'on renvoie au Frontend
class TowerData(BaseModel):
    id: str
    type: str
    x: int
    y: int
    owner_rfid: str


@app.post("/tower/place")
def handle_game_event(request: GameEventRequest):
    """
    Route unique qui gère TOUT : placement de tours et événements de mouvement.
    """
    device_id = request.towerId

    # 1. GESTION DU MOUVEMENT (Capteur Ultrason)
    if request.action == "movement" or request.action == "movement_detected":
        print(f"🌊 VAGUE DÉCLENCHÉE par {device_id}")

        # On ajoute un événement que le frontend pourra lire pour lancer la vague
        event = {"type": "START_WAVE", "source": device_id}
        game_state["events"].append(event)

        return {"status": "wave_started", "events": game_state["events"]}

    # 2. GESTION DES TOURS (Capteurs RFID)
    if device_id in BORNE_CONFIG and request.rfidTag:
        config = BORNE_CONFIG[device_id]
        rfid = request.rfidTag

        # Déterminer le type de tour grâce au badge
        tower_type = TAG_MAPPING.get(rfid, TAG_MAPPING["DEFAULT"])

        print(
            f"🏰 Tour {tower_type} placée en {config['name']} ({config['x']}, {config['y']})"
        )

        # Création de la donnée de la tour
        new_tower = {
            "towerId": device_id,  # On utilise l'ID de la borne comme ID unique de l'emplacement
            "type": tower_type,
            "x": config["x"],
            "y": config["y"],
            "owner_rfid": rfid,
        }

        # Logique : Si une tour existe déjà sur cette borne, on l'écrase (mise à jour)
        # On cherche si une tour a déjà cet ID de borne
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
    Appelé par le frontend (React/Vue) toutes les X ms pour mettre à jour l'écran
    """
    # On renvoie l'état et on peut 'consommer' les événements si besoin
    # Ici on laisse les événements, le front devra gérer les doublons ou on peut les clear
    response = game_state.copy()
    return response


@app.post("/reset")
def reset_game():
    game_state["towers"] = []
    game_state["events"] = []
    game_state["last_rfid"] = None
    return {"message": "Game reset", "current": game_state}
