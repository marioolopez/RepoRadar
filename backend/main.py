from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message ": "Bienvenido a SentinelForge API"}


@app.get("/health")
def health():
    return {"status": "ok"}