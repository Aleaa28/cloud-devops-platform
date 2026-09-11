from fastapi import FastAPI
import socket

app = FastAPI(
    title="Infrastructure Health API",
    version="1.0.1"
)


@app.get("/")
def root():
    return {
        "message": "Infrastructure Health API",
        "version": "1.0.1"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/api/system")
def system_info():
    return {
        "hostname": socket.gethostname(),
        "status": "running",
        "environment": "development"
    }
