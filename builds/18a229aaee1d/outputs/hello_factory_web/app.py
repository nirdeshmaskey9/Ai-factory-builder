from fastapi import FastAPI

app = FastAPI(title="hello_factory_web")


@app.get("/hello")
def hello():
    return {"message": "Hello, Factory!"}


@app.get("/health")
def health():
    return {"status": "ok"}