from fastapi import FastAPI

app = FastAPI()

@app.get('/hello')
def read_root():
    return {'message': 'Factory Online'}

@app.get('/')
def index():
    return {'message': 'App deployed successfully'}
