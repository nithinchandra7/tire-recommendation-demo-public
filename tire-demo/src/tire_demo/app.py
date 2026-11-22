"""One-origin local preview. Identity is simulated, not production authentication."""

import logging
from collections import OrderedDict
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .data import DATA_VERSION, SCOPES
from .engine import Engine
from .local_security import install_local_boundary
from .models import InventoryUpdate, RecommendationRequest, RecommendationResponse
from .repository import SnowflakeRepository, SqliteRepository, StateConflictError
from .settings import Settings

LOG = logging.getLogger("tire_demo")


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings.from_env()
    state = SqliteRepository(config)
    repository = state if config.backend == "sqlite" else SnowflakeRepository()
    engine = Engine(config, repository, state)
    traces: OrderedDict[str, tuple[str, dict[str, Any]]] = OrderedDict()
    application = FastAPI(
        title="Synthetic Tire Recommendation Demo",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    application.state.engine = engine
    install_local_boundary(application)
    application.state.store = state

    def retailer_scope(retailer: str | None) -> str:
        if retailer not in SCOPES:
            raise HTTPException(401, "Select a valid simulated demo retailer")
        return retailer

    @application.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "backend": config.backend,
            "provider": config.provider,
            "synthetic": True,
            "identity": "simulated",
            "data_version": DATA_VERSION,
            "cloud_verified": False,
        }

    @application.get("/api/tire/options")
    def options(x_demo_retailer: Annotated[str | None, Header()] = None) -> dict[str, Any]:
        retailer = retailer_scope(x_demo_retailer)
        return {
            "vehicles": repository.query("SELECT * FROM vehicle ORDER BY vehicle_id"),
            "sizes": repository.query("SELECT DISTINCT size FROM product ORDER BY size"),
            "locations": repository.query(
                "SELECT l.* FROM location l JOIN retailer_scope r ON r.store_id=l.store_id "
                "WHERE r.retailer_id=:retailer ORDER BY l.store_id",
                {"retailer": retailer},
            ),
            "retailer": retailer,
            "product_count": repository.query("SELECT COUNT(*) AS count FROM product")[0]["count"],
            "clock": config.now().isoformat(),
            "max_age_minutes": config.max_age_minutes,
        }

    @application.post("/api/tire/recommendations", response_model=RecommendationResponse)
    def recommend(
        request: RecommendationRequest, x_demo_retailer: Annotated[str | None, Header()] = None
    ) -> dict[str, Any]:
        retailer = retailer_scope(x_demo_retailer)
        try:
            result = engine.recommend(request, retailer)
        except StateConflictError as error:
            raise HTTPException(409, str(error)) from error
        except PermissionError as error:
            raise HTTPException(403, str(error)) from error
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except Exception as error:
            LOG.error("Recommendation dependency failed (%s)", type(error).__name__)
            raise HTTPException(
                503, "Data dependency unavailable; retry after checking configuration"
            ) from error
        request_id = result["trace"]["request_id"]
        traces[request_id] = retailer, result["trace"]
        if len(traces) > 256:
            traces.popitem(last=False)
        return result

    @application.get("/api/tire/traces/{request_id}")
    def trace(
        request_id: str, x_demo_retailer: Annotated[str | None, Header()] = None
    ) -> JSONResponse:
        retailer = retailer_scope(x_demo_retailer)
        value = traces.get(request_id)
        if value is None or value[0] != retailer:
            raise HTTPException(404, "Trace not found")
        return JSONResponse(value[1])

    @application.post("/api/tire/inventory")
    def inventory(
        update: InventoryUpdate, x_demo_retailer: Annotated[str | None, Header()] = None
    ) -> dict[str, str]:
        retailer = retailer_scope(x_demo_retailer)
        if config.backend != "sqlite":
            raise HTTPException(409, "Inventory simulator is available only in local SQLite mode")
        if update.store_id not in SCOPES[retailer]:
            raise HTTPException(403, "Inventory location is outside assigned demo scope")
        if update.observed_epoch > int(config.now().timestamp()):
            raise HTTPException(422, "Inventory observation cannot be in the future")
        try:
            return {"outcome": state.update_inventory(update), "data": "synthetic"}
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    @application.get("/demo")
    def demo() -> RedirectResponse:
        return RedirectResponse("/tire-demo/")

    application.mount("/", StaticFiles(directory=config.root / "dist", html=True), name="portfolio")
    return application


app = create_app()
