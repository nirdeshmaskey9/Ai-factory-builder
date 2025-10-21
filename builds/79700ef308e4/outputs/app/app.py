from fastapi import FastAPI

app = FastAPI(title="app")


@app.get("/hello")
def hello():
    return {"message": "Hello from app"}


@app.get("/health")
def health():
    return {"status": "ok"}