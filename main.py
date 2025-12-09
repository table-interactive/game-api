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
    # REMPLACEZ CES IDs PAR VOS VRAIS BADGES !
    "E2 45 88 A1": "Archer",  # Bleu, tir rapide
    "A4 21 55 B2": "Mage",  # Violet, dégâts de zone
    "CC 12 99 00": "Swordsman",  # Rouge, courte portée rapide
    "DD 33 44 55": "Healer",  # Vert, soigne les vies
    # Type par défaut si badge inconnu
    "DEFAULT": "Swordsman",
}

# --- ÉTAT DU JEU ---
game_state = {
    "towers": [],
    "events": [],
    "players": [],  # Ajouté pour que le frontend détecte "hasPlayer"
}

# --- MODÈLES DE DONNÉES ---


# Reçu de Node.js
class GameEventRequest(BaseModel):
    towerId: str
    rfidTag: Optional[str] = None
    action: Optional[str] = None


# Envoyé au Frontend (Noms de champs alignés sur TowerDTO du frontend)
class TowerData(BaseModel):
    towerId: str  # Important: le front attend "towerId", pas "id"
    towerType: str  # Important: le front attend "towerType", pas "type"
    x: int
    y: int
    owner_rfid: str


@app.post("/tower/place")
def handle_game_event(request: GameEventRequest):
    device_id = request.towerId

    # A. GESTION DU MOUVEMENT (VAGUE)
    if request.action == "movement" or request.action == "movement_detected":
        print(f"🌊 VAGUE DÉCLENCHÉE par {device_id}")
        # Le frontend gère les vagues auto, mais on pourrait forcer ici si besoin
        # Pour l'instant, on s'assure juste qu'il y a un joueur "fictif" pour démarrer le jeu
        if not game_state["players"]:
            game_state["players"].append({"id": "player_1"})
        return {"status": "wave_signal_received"}

    # B. GESTION DES TOURS (RFID)
    if device_id in BORNE_CONFIG and request.rfidTag:
        config = BORNE_CONFIG[device_id]
        rfid = request.rfidTag

        # Mapping vers les classes du Frontend (Archer, Mage...)
        tower_type = TAG_MAPPING.get(rfid, TAG_MAPPING["DEFAULT"])

        print(f"🏰 Tour {tower_type} placée sur {device_id}")

        # On s'assure qu'il y a un joueur actif dès qu'on pose une tour
        if not game_state["players"]:
            game_state["players"].append({"id": "player_1"})

        new_tower = {
            "towerId": device_id,
            "towerType": tower_type,  # Nommage JSON corrigé
            "x": config["x"],
            "y": config["y"],
            "owner_rfid": rfid,
        }

        # Mise à jour ou ajout (remplacement si la borne est déjà occupée)
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
    return game_state


@app.post("/reset")
def reset_game():
    game_state["towers"] = []
    game_state["events"] = []
    game_state["players"] = []  # Reset des joueurs aussi
    return {"message": "Game reset", "current": game_state}
