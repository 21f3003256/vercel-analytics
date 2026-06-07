from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
from statistics import mean
import math

app = FastAPI()

@app.middleware("http")
async def cors(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


def percentile(arr, p):
    arr = sorted(arr)
    k = (len(arr) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return arr[int(k)]
    return arr[f] * (c - k) + arr[c] * (k - f)


@app.post("/")
async def analytics_endpoint(request: Request):
    data = await request.json()

    regions = data.get("regions", [])
    threshold = data.get("threshold_ms", 180)

    with open("q-vercel-latency.json") as f:
        telemetry = json.load(f)

    output = {}

    for region in regions:
        records = [r for r in telemetry if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        output[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile(latencies, 0.95),
            "avg_uptime": mean(uptimes),
            "breaches": sum(l > threshold for l in latencies)
        }

    return JSONResponse(output)
