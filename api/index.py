from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FirmableWebAI API is working!", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "firmablewebai"}

# Simple test endpoint
@app.get("/test")
async def test():
    return {"message": "Test endpoint working", "status": "ok"}
