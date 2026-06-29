from fastapi import FastAPI

from coffee_optimizer.models import (
    OptimizationRequest,
    OptimizationResult,
    CorrectionOptimizationRequest,
    CorrectionOptimizationResult,
)

from coffee_optimizer.optimizer import run_optimization
from coffee_optimizer.correction_optimizer import run_correction_optimization

app = FastAPI(title="Coffee Optimizer API", version="1.0.0")


@app.post("/optimize", response_model=OptimizationResult)
def optimize(request: OptimizationRequest) -> OptimizationResult:
    return run_optimization(request)


@app.post("/optimize/correction", response_model=CorrectionOptimizationResult)
def optimize_correction(
    request: CorrectionOptimizationRequest,
) -> CorrectionOptimizationResult:
    return run_correction_optimization(request)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "coffee-optimizer"}
