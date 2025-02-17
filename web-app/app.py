from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI

import yaml
import uvicorn

from routes import home

app = FastAPI()
config = yaml.safe_load(open('./config.yaml'))

app.mount('/static/', StaticFiles(directory='./web/static/'))
app.mount('/node_modules', StaticFiles(directory='./web/node_modules/'))

app.include_router(home.router)



if __name__ == '__main__':
    uvicorn.run(
        app,
        host=config['server']['host'],
        port=5050,
        ssl_keyfile=
        config['server']['ssl_privkey']
        if config['server']['ssl_work']
        else None,
        ssl_certfile=
        config['server']['ssl_cert'] 
        if config['server']['ssl_work']
        else None
        )
