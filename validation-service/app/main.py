from fastapi import FastAPI
from app.database import engine, Base
from app.routes import router
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Validation Service",
    description="Housing data CSV validation microservice",
    version="1.0.0"
)

app.include_router(router, prefix="/validate", tags=["Validation"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "validation-service"}