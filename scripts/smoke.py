"""Verify an installed standalone package over native loopback HTTP."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "repository.json").read_text())


def main() -> None:
    tools = ROOT / ".tools"
    tools.mkdir(exist_ok=True)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"

    def fetch(path: str, payload: dict[str, Any] | None = None) -> Any:
        request = Request(  # noqa: S310 - fixed loopback origin
            origin + path,
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={
                "Content-Type": "application/json",
                "X-Demo-Identity": "finance" if CONFIG["project"] == "beauty" else "steward",
                "X-Demo-Retailer": "north",
            },
        )  # noqa: S310 - fixed loopback origin
        with urlopen(request, timeout=5) as response:  # noqa: S310 - fixed loopback origin
            data = response.read()
            return (
                json.loads(data)
                if response.headers.get_content_type() == "application/json"
                else data
            )

    with tempfile.TemporaryDirectory(dir=tools) as folder:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.update(
            SOLUTION_DEMO_ROOT=str(ROOT),
            SOLUTION_DEMO_STATE_ROOT=folder,
            TIRE_DEMO_ROOT=str(ROOT),
            DEMO_DATABASE=str(Path(folder) / "tire.sqlite"),
            DATA_BACKEND="sqlite",
            AI_PROVIDER="template",
        )
        with (Path(folder) / "server.log").open("w+") as log:
            process = subprocess.Popen(  # noqa: S603 - fixed local application
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    CONFIG["app"],
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=ROOT,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )  # noqa: S603 - fixed local application
            try:
                deadline = time.monotonic() + 20
                while True:
                    try:
                        assert fetch("/api/health")["synthetic"]
                        break
                    except (URLError, TimeoutError):
                        if process.poll() is not None or time.monotonic() > deadline:
                            log.seek(0)
                            raise RuntimeError(log.read()) from None
                        time.sleep(0.1)
                project = CONFIG["project"]
                assert fetch("/") and fetch(f"/{project}-demo/")
                if project == "tire":
                    assert fetch("/api/tire/recommendations", {"scenario": "standard"})[
                        "recommendations"
                    ]
                else:
                    state = fetch(f"/api/labs/{project}/runs", {"scenario": "clean"})
                    route = f"/api/labs/{project}/runs/{state['run_id']}"
                    if project == "master":
                        assert (
                            fetch(
                                route + "/actions",
                                {"revision": state["revision"], "action": "publish"},
                            )["publish_version"]
                            == 1
                        )
                    else:
                        assert fetch(
                            route + "/questions", {"question": "net revenue", "market": "US"}
                        )["evidence"]["markets"] == ["US"]
                count = 0
                for artifact in (ROOT / "dist" / f"{project}-demo/artifacts").iterdir():
                    if artifact.is_file():
                        assert fetch(f"/{project}-demo/artifacts/{artifact.name}")
                        count += 1
                print(
                    f"Installed {project} HTTP startup, business flow and {count} downloads passed."
                )
            finally:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
