# api/index.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from statistics import mean
import json
import os

app = FastAPI()

# Handle CORS preflight OPTIONS requests
@app.options("/analytics")
async def cors_preflight(request: Request):
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response

# Enable CORS for all requests
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.post("/analytics")
def analytics_endpoint(data: dict):
    # Get the regions and threshold from the request body
    regions = data.get("regions", [])
    threshold_ms = data.get("threshold_ms", 180)
    
    # Load the telemetry data from the JSON file
    try:
        # Get the file path - in Vercel serverless, it's in the root directory
        file_path = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
        with open(file_path, "r") as f:
            telemetry = json.load(f)
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Telemetry file not found"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error reading file: {str(e)}"}
        )
    
    # Calculate metrics for each region
    results = []
    
    for region in regions:
        # Filter data for this region
        region_data = [record for record in telemetry if record.get("region") == region]
        
        if not region_data:
            continue
        
        # Calculate average latency (mean)
        avg_latency = mean([record.get("latency_ms", 0) for record in region_data])
        
        # Calculate p95 latency (95th percentile)
        latencies = sorted([record.get("latency_ms", 0) for record in region_data])
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[min(p95_index, len(latencies) - 1)] if latencies else 0
        
        # Calculate average uptime (mean)
        avg_uptime = mean([record.get("uptime", 0) for record in region_data])
        
        # Count breaches (records where latency_ms > threshold_ms)
        breaches = sum(1 for record in region_data if record.get("latency_ms", 0) > threshold_ms)
        
        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        })
    
    return JSONResponse(content=results)

# Optional: Root endpoint for testing
@app.get("/")
def read_root():
    return {"message": "Analytics endpoint is running!"}
