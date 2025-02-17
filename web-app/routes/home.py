from fastapi import APIRouter, Request
from starlette.responses import FileResponse, HTMLResponse

router = APIRouter()


@router.get('/', response_class=HTMLResponse)
async def home(req: Request):
    return FileResponse('./web/html/index.html')
