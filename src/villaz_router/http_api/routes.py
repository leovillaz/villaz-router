from typing import Annotated

from fastapi import APIRouter, Depends

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.http_api.dependencies import (
    get_runtime_context,
)
from villaz_router.http_api.models import (
    LivenessResponse,
    ReadinessResponse,
)


router = APIRouter()


@router.get(
    "/health/live",
    response_model=LivenessResponse,
)
def get_liveness() -> LivenessResponse:
    return LivenessResponse()


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
)
def get_readiness(
    runtime_context: Annotated[
        RuntimeContext,
        Depends(get_runtime_context),
    ],
) -> ReadinessResponse:
    return ReadinessResponse()
