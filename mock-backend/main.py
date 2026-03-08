"""Simple mock backend for testing the gateway."""
from fastapi import FastAPI

app = FastAPI(title="Mock Backend")


@app.get("/")
def root():
    return {"message": "Mock backend", "status": "ok"}


@app.get("/get")
def get():
    return {"args": {}, "headers": {}, "url": "http://mock/get"}


@app.get("/{path:path}")
def catch_all(path: str):
    return {"path": path, "message": "Proxied through gateway"}
