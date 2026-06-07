# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from statistics import mean
import json
import os

app = FastAPI()

# CORS middleware - sets headers to * explicitly
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Set CORS headers with wildcard *
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

@app.post("/analytics")
def analytics_endpoint(data: dict):
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 180)
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
        with open(file_path, "r") as f:
            telemetry = json.load(f)
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Telemetry file not found"}
        )
    
    results = []
    
    for region in regions:
        region_data = [record for record in telemetry if record.get("region") == region]
        
        if not region_data:
            continue
        
        avg_latency = mean([record.get("latency_ms", 0) for record in region_data])
        
        latencies = sorted([record.get("latency_ms", 0) for record in region_data])
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[min(p95_index, len(latencies) - 1)] if latencies else 0
        
        avg_uptime = mean([record.get("uptime", 0) for record in region_data])
        
        breaches = sum(1 for record in region_data if record.get("latency_ms", 0) > threshold_ms)
        
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
    return {"message": "Analytics endpoint is running!"}
