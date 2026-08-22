from fastapi import FastAPI
from pydantic import BaseModel


#fastapi app declearation
app = FastAPI()

@app.get("/health")
async def api_health_check():
    return {
        "message": "This is an API health checkpoint, and if you're seeing this message it means that the API is healthy and working properly."
    }

@app.get("/")
async def home():
    return {
        "message": "Welcom to the home of the DataDump!",
        "descrition": "This is an ongoing project that takes and processes the CSV file"
        }

@app.get("/jobs")
async def get_job():
    pass

@app.post("/jobs")
async def post_job():
    pass
