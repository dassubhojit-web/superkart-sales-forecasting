# SuperKart Sales Forecasting

This repository contains two decoupled Docker services:

- `backend`: Flask model API on port `7860`
- `frontend`: Streamlit client on port `8501`

## GitHub Codespaces

Launch both services with:

```bash
docker compose up --build -d
docker compose ps
```

In the Codespaces **Ports** tab, set ports `7860` and `8501` to **Public**. Copy the forwarded URL for port `7860` into the notebook for API inference and open the forwarded URL for port `8501` to use the Streamlit app.

## Manual container commands

```bash
docker build -t superkart-backend ./backend
docker build -t superkart-frontend ./frontend
docker network create superkart-network
docker run -d --name backend --network superkart-network -p 7860:7860 superkart-backend
docker run -d --name frontend --network superkart-network -p 8501:8501 -e BACKEND_URL=http://backend:7860 superkart-frontend
```
