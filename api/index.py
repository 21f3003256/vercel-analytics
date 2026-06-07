# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from statistics import mean
import json
import os

app = FastAPI()

# CORS headers dictionary
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response

@app.post("/analytics")
async def analytics_endpoint(request: Request):
    try:
        body = await request.json()
        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)
    except:
        response = JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON", "regions": []}
        )
        for key, value in CORS_HEADERS.items():
            response.headers[key] = value
        return response
    
    try:
        file_path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
        with open(file_path, "r") as f:
            telemetry = json.load(f)
    except FileNotFoundError:
        response = JSONResponse(
            status_code=404,
            content={"error": "File not found", "regions": []}
        )
        for key, value in CORS_HEADERS.items():
            response.headers[key] = value
        return response
    
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
    
    # Return with regions array at top level
    response = JSONResponse(content={"regions": results})
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    return response

@app.get("/")
def read_root():
    return {"message": "OK"}

@app.options("/analytics")
async def options_handler(request: Request):
    response = JSONResponse(content={})
    for key, value in CORS_HEADERS.items():
        response.headers[key] = value
    response.headers["Access-Control-Max-Age"] = "86400"
    return response
