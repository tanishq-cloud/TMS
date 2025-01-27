from fastapi import FastAPI
from app.routers import tasks, auth, data_analysis, visualisation, trigger
from app.database import init_db
from app.utils.scheduler import init_scheduler
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scheduler globally
scheduler = init_scheduler()

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
    except Exception as e:
        logging.error(f"Database initialization failed: {str(e)}", exc_info=True)
        raise RuntimeError("Failed to initialize database") from e
    
    
  
    scheduler.start()

    

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)
    print("Scheduler shutdown.")

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Register and Access Token"])
app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
app.include_router(data_analysis.router, prefix="/data", tags=["Data Analysis using Pandas"])
app.include_router(visualisation.router, prefix="/visualisation", tags=["Visualisation using using Matplotlib/Seaborn"])
app.include_router(trigger.router, prefix="/trigger", tags=["Trigger to notify admin"])

