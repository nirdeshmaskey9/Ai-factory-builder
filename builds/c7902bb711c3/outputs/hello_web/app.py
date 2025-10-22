from fastapi import FastAPI

app = FastAPI(title="hello_web")


@app.get("/hello")
def hello():
    return {"message": "Hello from hello_web"}


@app.get("/health")
def health():
    return {"status": "ok"}