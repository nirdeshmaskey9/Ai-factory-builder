from fastapi import FastAPI
app = FastAPI(title='Deployed App', version='1.0.0')

GOAL = 'hello-world-deploy'
@app.get('/health')
def health():
    return {'status':'ok','goal':GOAL}
