from importlib.resources import files
import os
from pathlib import Path

import villaz_router
import villaz_router.runtime_data as runtime_data


EXPECTED_RESOURCES = (
    "config/ollama.yaml",
    "config/router.yaml",
    "profiles/profiles.yaml",
    "rules/domains.yaml",
    "rules/intents.yaml",
    "rules/profiles.yaml",
    "rules/routing.yaml",
)


def main() -> int:
    module_path = Path(
        villaz_router.__file__
    ).resolve()
    checkout_value = os.environ.get(
        "GITHUB_WORKSPACE"
    )

    if checkout_value is not None:
        checkout = Path(checkout_value).resolve()
        if (
            module_path == checkout
            or checkout in module_path.parents
        ):
            raise RuntimeError(
                "villaz_router was imported from the "
                "source checkout"
            )

    resource_root = files(runtime_data)
    discovered = tuple(
        sorted(
            str(path.relative_to(resource_root)).replace(
                "\\",
                "/",
            )
            for directory in resource_root.iterdir()
            if directory.is_dir()
            and directory.name != "__pycache__"
            for path in directory.iterdir()
            if path.is_file()
        )
    )

    if discovered != EXPECTED_RESOURCES:
        raise RuntimeError(
            "installed package resources differ from "
            f"the expected set: {discovered!r}"
        )

    print(f"installed package: {module_path}")
    print(
        "installed resources: "
        f"{len(discovered)} YAML files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
