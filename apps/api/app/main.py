from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI, File, Header, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.base import RequestResponseEndpoint

from .config import Settings, get_settings
from .db import build_session_factory
from .errors import install_error_handlers
from .models import Category, Product, Sale
from .schemas import (
    AnnulmentInput,
    CategoryInput,
    CategoryOutput,
    CurrentSessionOutput,
    ErrorOutput,
    LoginInput,
    ObservationInput,
    ProductInput,
    ProductOutput,
    SaleInput,
    SaleOutput,
    SalesByDayOutput,
)
from .services.catalog import MAX_IMAGE_BYTES, ProductCatalog
from .services.sales import Sales
from .services.sessions import CurrentUser, Sessions
from .storage import ImageStorage, UnconfiguredStorage, VercelBlobStorage


def money(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def product_output(product: Product) -> ProductOutput:
    return ProductOutput(
        id=product.id,
        name=product.name,
        price=money(product.price),
        active=product.active,
        image_url=product.image_url,
        category=category_output(product.category),
    )


def category_output(category: Category) -> CategoryOutput:
    return CategoryOutput(id=category.id, name=category.name)


def sale_output(sale: Sale) -> SaleOutput:
    return SaleOutput.model_validate(
        {
            "id": sale.id,
            "payment_method": sale.payment_method,
            "total": money(sale.total),
            "sold_at": sale.sold_at,
            "sale_day": sale.sale_day,
            "observation": sale.observation,
            "annulment": (
                {"reason": sale.annulment_reason, "annulled_at": sale.annulled_at}
                if sale.annulment_reason is not None and sale.annulled_at is not None
                else None
            ),
            "details": [
                {
                    "id": detail.id,
                    "product_id": detail.product_id,
                    "product_name": detail.product_name,
                    "unit_price": money(detail.unit_price),
                    "quantity": detail.quantity,
                    "position": detail.position,
                }
                for detail in sale.details
            ],
        }
    )


def create_app(
    settings: Settings | None = None,
    session_factory: sessionmaker[Session] | None = None,
    image_storage: ImageStorage | None = None,
    clock: Callable[[], datetime] | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    factory = session_factory or build_session_factory(app_settings)
    storage = image_storage or (
        VercelBlobStorage(app_settings)
        if app_settings.vercel_blob_read_write_token is not None
        else UnconfiguredStorage()
    )
    sessions = Sessions(app_settings)
    catalog = ProductCatalog(storage)
    sales = Sales(clock)

    app = FastAPI(
        title="Cucurucho API",
        version="1.0.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        responses={
            status_code: {"model": ErrorOutput}
            for status_code in (401, 403, 404, 409, 422, 502)
        },
    )
    install_error_handlers(app)

    def get_db() -> Iterator[Session]:
        with factory() as db:
            yield db

    def authenticated_user(request: Request, db: Session = Depends(get_db)) -> CurrentUser:
        token = request.cookies.get(app_settings.session_cookie_name)
        return sessions.resolve(db, token)

    @app.middleware("http")
    async def enforce_same_origin(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        is_mutation = request.method not in {"GET", "HEAD", "OPTIONS"}
        if is_mutation and request.url.path.startswith("/api/"):
            if request.headers.get("origin") != app_settings.app_origin.rstrip("/"):
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": "invalid_origin",
                        "message": "La solicitud no proviene de esta aplicación.",
                        "field_errors": {},
                    },
                )
        return await call_next(request)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/sesion/login", status_code=status.HTTP_204_NO_CONTENT)
    def login(payload: LoginInput, response: Response, db: Session = Depends(get_db)) -> None:
        started = sessions.authenticate(db, payload.username, payload.password)
        response.set_cookie(
            app_settings.session_cookie_name,
            started.raw_token,
            max_age=started.max_age_seconds,
            secure=app_settings.session_cookie_secure,
            httponly=True,
            samesite="lax",
            path="/",
        )

    @app.post("/api/sesion/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(
        request: Request,
        response: Response,
        db: Session = Depends(get_db),
    ) -> None:
        sessions.revoke(db, request.cookies.get(app_settings.session_cookie_name))
        response.delete_cookie(
            app_settings.session_cookie_name,
            path="/",
            secure=app_settings.session_cookie_secure,
            httponly=True,
            samesite="lax",
        )

    @app.get("/api/sesion/actual")
    def current_session(user: CurrentUser = Depends(authenticated_user)) -> CurrentSessionOutput:
        return CurrentSessionOutput(id=user.id, username=user.username)

    @app.get("/api/productos", response_model=list[ProductOutput])
    def list_products(
        incluir_inactivos: bool = False,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> list[ProductOutput]:
        return [product_output(item) for item in catalog.list_products(db, incluir_inactivos)]

    @app.get("/api/categorias", response_model=list[CategoryOutput])
    def list_categories(
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> list[CategoryOutput]:
        return [category_output(item) for item in catalog.list_categories(db)]

    @app.post("/api/categorias", response_model=CategoryOutput, status_code=201)
    def create_category(
        payload: CategoryInput,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> CategoryOutput:
        return category_output(catalog.create_category(db, payload))

    @app.put("/api/categorias/{category_id}", response_model=CategoryOutput)
    def update_category(
        category_id: uuid.UUID,
        payload: CategoryInput,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> CategoryOutput:
        return category_output(catalog.update_category(db, category_id, payload))

    @app.post("/api/productos", response_model=ProductOutput, status_code=201)
    def create_product(
        payload: ProductInput,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> ProductOutput:
        return product_output(catalog.create(db, payload))

    @app.put("/api/productos/{product_id}", response_model=ProductOutput)
    def update_product(
        product_id: uuid.UUID,
        payload: ProductInput,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> ProductOutput:
        return product_output(catalog.update(db, product_id, payload))

    @app.post("/api/productos/{product_id}/activar", response_model=ProductOutput)
    def activate_product(
        product_id: uuid.UUID,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> ProductOutput:
        return product_output(catalog.set_active(db, product_id, True))

    @app.post("/api/productos/{product_id}/inactivar", response_model=ProductOutput)
    def deactivate_product(
        product_id: uuid.UUID,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> ProductOutput:
        return product_output(catalog.set_active(db, product_id, False))

    @app.put("/api/productos/{product_id}/imagen", response_model=ProductOutput)
    async def replace_product_image(
        product_id: uuid.UUID,
        image: Annotated[UploadFile, File()],
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> ProductOutput:
        content = await image.read(MAX_IMAGE_BYTES + 1)
        return product_output(
            catalog.replace_image(db, product_id, content, image.content_type)
        )

    @app.delete("/api/productos/{product_id}/imagen", response_model=ProductOutput)
    def remove_product_image(
        product_id: uuid.UUID,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> ProductOutput:
        return product_output(catalog.remove_image(db, product_id))

    @app.post("/api/ventas", response_model=SaleOutput, status_code=201)
    def confirm_sale(
        response: Response,
        payload: SaleInput,
        idempotency_key: Annotated[
            str, Header(alias="Idempotency-Key", min_length=1, max_length=200)
        ],
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> SaleOutput:
        sale, created = sales.confirm(db, idempotency_key, payload)
        response.status_code = 201 if created else 200
        return sale_output(sale)

    @app.get("/api/ventas", response_model=SalesByDayOutput)
    def sales_by_day(
        dia: date,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> SalesByDayOutput:
        records, total_sold = sales.by_day(db, dia)
        return SalesByDayOutput(
            day=dia,
            total_sold=money(total_sold),
            sales=[sale_output(sale) for sale in records],
        )

    @app.get("/api/ventas/{sale_id}", response_model=SaleOutput)
    def sale_detail(
        sale_id: uuid.UUID,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> SaleOutput:
        return sale_output(sales.get(db, sale_id))

    @app.post("/api/ventas/{sale_id}/anulacion", response_model=SaleOutput)
    def annul_sale(
        sale_id: uuid.UUID,
        payload: AnnulmentInput,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> SaleOutput:
        return sale_output(sales.annul(db, sale_id, payload.reason))

    @app.put("/api/ventas/{sale_id}/observacion", response_model=SaleOutput)
    def replace_observation(
        sale_id: uuid.UUID,
        payload: ObservationInput,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> SaleOutput:
        return sale_output(sales.replace_observation(db, sale_id, payload.observation))

    @app.delete("/api/ventas/{sale_id}/observacion", response_model=SaleOutput)
    def remove_observation(
        sale_id: uuid.UUID,
        _user: CurrentUser = Depends(authenticated_user),
        db: Session = Depends(get_db),
    ) -> SaleOutput:
        return sale_output(sales.remove_observation(db, sale_id))

    return app


app = create_app()
