from fastapi import FastAPI
from app.database import engine, Base
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Auth Service",
    description="JWT Authentication microservice for Housing Data Validation",
    version="1.0.0"
)

app.include_router(router, prefix="/auth", tags=["Authentication"])

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "auth-service"}