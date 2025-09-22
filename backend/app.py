
from db.connect_db import create_db_and_tables
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import holdings
from sqlmodel import SQLModel, create_engine, Session

################ FASTAPI ENTRYPOINT ##############
app = FastAPI()
# Middleware
# cors
origins = [
    "*"  # Allows all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"], 
)

# Route mounting
app.include_router(holdings.router)

@app.get("/")
async def root():
    return {"message": "Hello from top-level app!"}


@app.on_event("startup")
def on_startup():
    create_db_and_tables()