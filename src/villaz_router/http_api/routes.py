from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse

from villaz_router.bootstrap_models import RuntimeContext
from villaz_router.dispatcher import build_dispatch_plan
from villaz_router.dispatcher_errors import DispatcherError
from villaz_router.errors import RouterError
from villaz_router.http_api.dependencies import (
    get_ollama_executor,
    get_runtime_context,
)
from villaz_router.http_api.models import (
    ErrorEnvelope,
    ErrorResponse,
    LivenessResponse,
    PromptRequest,
    PromptResponse,
    ReadinessResponse,
)
from villaz_router.http_api.router_adapter import (
    HttpRoutingError,
    route_prompt_request,
)
from villaz_router.ollama_execution.errors import (
    OllamaExecutionError,
    OllamaExecutionErrorCode,
)
from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)
from villaz_router.ollama_execution.models import (
    OllamaExecutionRequest,
)
from villaz_router.registry_errors import RegistryError


_INTERNAL_ERROR = (
    500,
    "INTERNAL_ERROR",
    "The request could not be completed due to an internal error.",
)

_OLLAMA_ERROR_MAPPING: dict[
    OllamaExecutionErrorCode,
    tuple[int, str, str],
] = {
    OllamaExecutionErrorCode.CONNECT_TIMEOUT: (
        504,
        "MODEL_SERVICE_TIMEOUT",
        "The model service timed out.",
    ),
    OllamaExecutionErrorCode.READ_TIMEOUT: (
        504,
        "MODEL_SERVICE_TIMEOUT",
        "The model service timed out.",
    ),
    OllamaExecutionErrorCode.WRITE_TIMEOUT: (
        504,
        "MODEL_SERVICE_TIMEOUT",
        "The model service timed out.",
    ),
    OllamaExecutionErrorCode.POOL_TIMEOUT: (
        503,
        "MODEL_SERVICE_UNAVAILABLE",
        "The model service is unavailable.",
    ),
    OllamaExecutionErrorCode.NETWORK_ERROR: (
        503,
        "MODEL_SERVICE_UNAVAILABLE",
        "The model service is unavailable.",
    ),
    OllamaExecutionErrorCode.PROTOCOL_ERROR: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.HTTP_STATUS_ERROR: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.INVALID_JSON_RESPONSE: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.INVALID_RESPONSE: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.MODEL_MISMATCH: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.EMPTY_RESPONSE: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.GENERATION_INCOMPLETE: (
        502,
        "MODEL_SERVICE_ERROR",
        "The model service failed to complete the request.",
    ),
    OllamaExecutionErrorCode.INVALID_EXECUTION_RESULT: _INTERNAL_ERROR,
}


router = APIRouter()


def _public_error_response(
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorEnvelope(
            code=code,
            message=message,
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(
            mode="json",
            exclude_none=True,
        ),
    )


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
    request: Request,
    response: Response,
) -> ReadinessResponse:
    try:
        get_runtime_context(request)
        get_ollama_executor(request)
    except (RuntimeError, TypeError):
        response.status_code = 503
        return ReadinessResponse(
            status="not_ready"
        )

    return ReadinessResponse()


@router.post(
    "/v1/prompt",
    response_model=PromptResponse,
)
async def post_prompt(
    prompt_request: PromptRequest,
    runtime_context: Annotated[
        RuntimeContext,
        Depends(get_runtime_context),
    ],
    ollama_executor: Annotated[
        OllamaExecutor,
        Depends(get_ollama_executor),
    ],
) -> PromptResponse | JSONResponse:
    try:
        outcome = route_prompt_request(
            prompt_request,
            runtime_context,
        )

        if isinstance(outcome, HttpRoutingError):
            return JSONResponse(
                status_code=outcome.status_code,
                content=outcome.body.model_dump(
                    mode="json",
                    exclude_none=True,
                ),
            )

        dispatch_plan = build_dispatch_plan(
            outcome,
            runtime_context.profile_registry,
        )
        execution_request = OllamaExecutionRequest(
            dispatch_plan=dispatch_plan,
            user_prompt=prompt_request.message,
        )
        execution_result = await ollama_executor.execute(
            execution_request
        )

        return PromptResponse(
            response=execution_result.response_text,
            profile=dispatch_plan.profile_id,
            model=execution_result.model,
            state=dispatch_plan.source_state.value,
            route_id=dispatch_plan.route_id,
        )
    except (RouterError, DispatcherError, RegistryError):
        return _public_error_response(*_INTERNAL_ERROR)
    except OllamaExecutionError as exc:
        return _public_error_response(
            *_OLLAMA_ERROR_MAPPING[exc.code]
        )
    except Exception:
        return _public_error_response(*_INTERNAL_ERROR)
