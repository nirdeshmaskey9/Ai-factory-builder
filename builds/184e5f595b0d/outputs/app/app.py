import time
from fastapi import FastAPI

app = FastAPI(title="app")


@app.get("/hello")
def hello():
    time.sleep(0.5)
    return {"message": "Hello from app"}


@app.get("/health")
def health():
    return {"status": "ok"}