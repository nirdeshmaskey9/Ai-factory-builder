from fastapi import FastAPI

app = FastAPI(title="reminder_scheduler")


@app.get("/hello")
def hello():
    return {"message": "Hello from reminder_scheduler"}


@app.get("/health")
def health():
    return {"status": "ok"}