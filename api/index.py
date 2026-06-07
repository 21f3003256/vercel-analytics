# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from statistics import mean
from typing import List

app = FastAPI()

# Enable CORS for POST requests
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.post("/")
async def analytics_endpoint(request: Request):
    # Get JSON body
    data = await request.json()
    regions: List[str] = data.get("regions", [])
    threshold_ms: int = data.get("threshold_ms", 180)
    
    # Load telemetry data (you'll download this file)
    with open("q-vercel-latency.json", "r") as f:
        telemetry = json.load(f)
    
    # Calculate metrics per region
    results = []
    for region in regions:
        region_records = [r for r in telemetry if r.get("region") == region]
        
        if not region_records:
            results.append({
                "region": region,
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            })
            continue
        
        latencies = [r["latency_ms"] for r in region_records]
        uptimes = [r["uptime_percent"] for r in region_records]
        
        avg_latency = mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        avg_uptime = mean(uptimes)
        breaches = len([l for l in latencies if l > threshold_ms])
        
        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })
    
    return JSONResponse(results)
