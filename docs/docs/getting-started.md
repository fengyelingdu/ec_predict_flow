---
sidebar_position: 2
---

# 快速开始

本指南将帮助你快速安装和运行事件合约预测工作流系统。

## 环境要求

- Node.js >= 16
- Python >= 3.8
- npm 或 yarn

## 安装步骤

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

## 启动系统


### 启动后端服务

1. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置
```

2. 启动Redis
```bash
redis-server
```

3. 启动Celery Worker
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

4. 启动FastAPI服务
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

### 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

## 访问系统

打开浏览器访问 `http://localhost:5173`，你将看到工作流概览页面。

## API文档

启动后端服务后，访问以下地址查看API文档:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 下一步

- 查看[数据下载](./modules/data-download.md)模块了解如何获取数据
- 按照工作流顺序依次使用各个模块
