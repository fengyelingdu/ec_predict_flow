from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.endpoints import workflow
import os

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 先注册 API 路由
app.include_router(
    workflow.router,
    prefix=f"{settings.API_V1_STR}/workflow",
    tags=["workflow"]
)


@app.get("/")
async def root():
    return {
        "message": "EC Predict Flow API",
        "version": settings.VERSION
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 挂载静态文件目录（用于访问生成的图片）
# 注意：静态文件挂载必须在所有路由之后，否则会覆盖路由
# 确保目录存在
os.makedirs(settings.PLOTS_DIR, exist_ok=True)
app.mount("/static/plots", StaticFiles(directory=settings.PLOTS_DIR), name="plots")
