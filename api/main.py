from uuid import uuid4
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from .models import (
    JobStatus,
    JobCreate,
    JobUpdate,
    JobResponse
)


class FakeDb():
    def __init__(self):
        self.items : dict = {}
    
    def create_job(self,job: JobCreate):
        stored_job = JobResponse(
            id = uuid4(),
            source = job.source,
            destination = job.destination,
            batch_size= job.batch_size,
                
            status= JobStatus.PENDING,
            processed_records = 0,
            total_records= 0,
            error_message= None,
                
            created_at = datetime.now(),
            updated_at = None,
            completed_at  = None
        )
        
        self.items.update(
            {
                f"job {str(stored_job.id)}" : stored_job
            }
        )
        
        # return self.items.get(f"{int(stored_job.id)}")
        return self.items
        
    
    def get_job(self,id=None):
        if id is None:
            return self.items
        return self.items.get(f"job {id}")

fake_db = FakeDb()   
    
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
async def get_all_job():
    return fake_db.get_job()
    
@app.get("/jobs/{id}")
async def get_job(id):
    return fake_db.get_job(id=id)

@app.post("/jobs")
async def post_job(job: JobCreate):
    return fake_db.create_job(job)

@app.put("/jobs/{id}")
async def put_job():
    return {"message":"the job put section is still under construction"}

@app.patch("/jobs/{id}")
async def patch_job():
    return {"message":"the job patch section is still under construction"}