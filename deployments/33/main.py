import os
if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', '8000'))
    uvicorn.run('app:app', host='127.0.0.1', port=port)
