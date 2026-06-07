# api/index.py
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from statistics import mean
import json
import os

# Custom CORS middleware that FORCESets *
class ForceCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        # Remove Vary header that causes origin echoing
        if "Vary" in response.headers:
            del response.headers["Vary"]
        return response

app = FastAPI()
app.add_middleware(ForceCORSMiddleware)

@app.post("/analytics")
def analytics_endpoint(data: dict):
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 180)
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
        with open(file_path, "r") as f:
            telemetry = json.load(f)
    except FileNotFoundError:
        return JSONResponse(status_code=404, content={"error": "File not found"})
    
    results = []
    
    for region in regions:
        region_data = [r for r in telemetry if r.get("region") == region]
        if not region_data:
            continue
        
        avg_latency = mean([r.get("latency_ms", 0) for r in region_data])
        latencies = sorted([r.get("latency_ms", 0) for r in region_data])
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[min(p95_index, len(latencies) - 1)] if latencies else 0
        avg_uptime = mean([r.get("uptime", 0) for r in region_data])
        breaches = sum(1 for r in region_data if r.get("latency_ms", 0) > threshold_ms)
        
        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })
    
    return JSONResponse(content=results)

@app.get("/")
def read_root():
    return {"message": "OK"}
