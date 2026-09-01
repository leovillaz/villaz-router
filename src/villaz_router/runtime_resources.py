from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path


_RUNTIME_DATA_PACKAGE = "villaz_router.runtime_data"


@contextmanager
def packaged_configuration_root() -> Iterator[Path]:
    resource_root = files(_RUNTIME_DATA_PACKAGE)

    with as_file(resource_root) as extracted_root:
        yield Path(extracted_root).resolve()
