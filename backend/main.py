from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Road Intelligence API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Road Intelligence Backend is live!", "region": "Tamil Nadu"}

@app.get("/api/road-status/{city}")
def get_road_status(city: str):
    if city.lower() == "trichy":
        return {
            "city": "Trichy",
            "total_roads_analyzed": 1420,
            "damaged_roads_detected": 35,
            "status": "Warning - Maintenance Required"
        }
    return {"error": "City data not found"}