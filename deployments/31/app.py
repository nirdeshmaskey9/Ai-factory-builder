from fastapi import FastAPI
app = FastAPI(title='Deployed App', version='1.0.0')

GOAL = 'deploy a tiny app'
@app.get('/health')
def health():
    return {'status':'ok','goal':GOAL}
