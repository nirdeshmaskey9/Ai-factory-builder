from fastapi import FastAPI
app = FastAPI(title='Deployed App', version='1.0.0')

GOAL = 'Build and run a FastAPI app locally with a single /hello endpoint returning JSON {"message": "Factory Online"}'
@app.get('/health')
def health():
    return {'status':'ok','goal':GOAL}
