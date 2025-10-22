from fastapi import FastAPI

app = FastAPI(title="test_app")


@app.get("/")
def hello():
    return {"message": "Hello, world! from AI Factory"}


@app.get("/health")
def health():
    return {"status": "ok"}