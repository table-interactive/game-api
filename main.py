from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game_state = {"towers": []}

class TowerData(BaseModel):
    towerId: str
    x: int
    y: int


@app.post("/tower/place")
def place_tower(towerId: str):
    if towerId == "LECTEUR_1":
        data = TowerData(towerId=towerId, x=250, y=250)
    elif towerId == "LECTEUR_2":
        data = TowerData(towerId=towerId, x=650, y=200)
    elif towerId == "LECTEUR_3":
        data = TowerData(towerId=towerId, x=950, y=450)
    else:
        return {"error": "Invalid towerId"}
    game_state["towers"].append(data.dict())
    return {"message": "Tower placed", "current": game_state["towers"]}

@app.get("/state")
def get_state():
    return game_state

@app.post("/players")
def add_player(playerId: str):
    if "players" not in game_state:
        game_state["players"] = []
    game_state["players"].append({"playerId": playerId})
    return {"message": "Player added", "current": game_state.get("players", [])}

