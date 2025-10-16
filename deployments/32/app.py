from fastapi import FastAPI
app = FastAPI(title='Deployed App', version='1.0.0')

GOAL = 'registry test'
@app.get('/health')
def health():
    return {'status':'ok','goal':GOAL}
