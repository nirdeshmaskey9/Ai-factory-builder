from fastapi import FastAPI

app = FastAPI(title="app")


@app.get("/hello")
def hello():
    return {"message": "Hello from app"}
