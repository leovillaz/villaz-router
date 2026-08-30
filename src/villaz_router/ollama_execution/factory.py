import httpx2

from villaz_router.ollama_execution.config import (
    OllamaClientConfig,
)
from villaz_router.ollama_execution.executor import (
    OllamaExecutor,
)
from villaz_router.ollama_execution.httpx2_transport import (
    Httpx2OllamaTransport,
)


def create_ollama_executor(
    config: OllamaClientConfig,
) -> OllamaExecutor:
    timeout = httpx2.Timeout(
        connect=config.timeouts.connect_seconds,
        read=config.timeouts.read_seconds,
        write=config.timeouts.write_seconds,
        pool=config.timeouts.pool_seconds,
    )

    limits = httpx2.Limits(
        max_connections=(
            config.limits.max_connections
        ),
        max_keepalive_connections=(
            config.limits
            .max_keepalive_connections
        ),
        keepalive_expiry=(
            config.limits
            .keepalive_expiry_seconds
        ),
    )

    http_transport = httpx2.AsyncHTTPTransport(
        trust_env=False,
        http1=True,
        http2=False,
        limits=limits,
        retries=0,
    )

    client = httpx2.AsyncClient(
        base_url=config.base_url.rstrip("/"),
        timeout=timeout,
        follow_redirects=False,
        limits=limits,
        transport=http_transport,
        trust_env=False,
        http1=True,
        http2=False,
    )

    ollama_transport = Httpx2OllamaTransport(
        client
    )

    return OllamaExecutor(ollama_transport)
