import hashlib
import json
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.deps import get_current_user, get_db, get_redis, require_admin
from app.models import AuditLog, Reservation, Resource, User
from app.schemas import (
    ReservationCreate,
    ReservationOut,
    ReservationUpdate,
    ResourceCreate,
    ResourceOut,
    ResourceUpdate,
    SignupRequest,
    TokenOut,
    UserOut,
)

router = APIRouter()


def write_audit(db: Session, actor_user_id: int | None, action: str, target: str, detail: str):
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, target=target, detail=detail))


def to_utc_naive(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise HTTPException(
            status_code=400, detail=f"{field_name} must include timezone (UTC recommended)"
        )
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def find_overlap(
    db: Session,
    *,
    resource_id: int,
    start_at: datetime,
    end_at: datetime,
    exclude_reservation_id: int | None = None,
):
    q = db.query(Reservation).filter(
        and_(
            Reservation.resource_id == resource_id,
            Reservation.status == "BOOKED",
            or_(
                and_(Reservation.start_at <= start_at, Reservation.end_at > start_at),
                and_(Reservation.start_at < end_at, Reservation.end_at >= end_at),
                and_(Reservation.start_at >= start_at, Reservation.end_at <= end_at),
            ),
        )
    )
    if exclude_reservation_id is not None:
        q = q.filter(Reservation.id != exclude_reservation_id)
    return q.first()


def build_reservation_request_hash(resource_id: int, start_at: datetime, end_at: datetime) -> str:
    raw = json.dumps(
        {
            "resource_id": resource_id,
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
        },
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def success_response(request: Request, data, envelope: bool):
    if not envelope:
        return data
    return {
        "success": True,
        "data": jsonable_encoder(data),
        "request_id": getattr(request.state, "request_id", None),
    }


@router.get("/health")
def health(
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
):
    return success_response(request, {"status": "ok"}, envelope)


@router.get("/ready")
def ready(
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))
    return success_response(request, {"status": "ready", "db": "ok"}, envelope)


@router.post("/auth/signup", response_model=UserOut | dict)
def signup(
    payload: SignupRequest,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
):
    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=409, detail="email already exists")

    role = "ADMIN" if db.query(User).count() == 0 else "USER"
    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.flush()
    write_audit(db, user.id, "auth.signup", f"user:{user.id}", f"role={user.role}")
    db.commit()
    db.refresh(user)
    return success_response(request, user, envelope)


@router.post("/auth/login", response_model=TokenOut | dict)
def login(
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(user.email)
    return success_response(request, TokenOut(access_token=token), envelope)


@router.post("/resources", response_model=ResourceOut | dict)
def create_resource(
    payload: ResourceCreate,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    duplicated = db.query(Resource).filter(Resource.name == payload.name).first()
    if duplicated:
        raise HTTPException(status_code=409, detail="resource name already exists")

    resource = Resource(name=payload.name)
    db.add(resource)
    db.flush()
    write_audit(db, admin.id, "resource.create", f"resource:{resource.id}", payload.name)
    db.commit()
    db.refresh(resource)
    return success_response(request, resource, envelope)


@router.get("/resources", response_model=list[ResourceOut] | dict)
def list_resources(
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    resources = db.query(Resource).order_by(Resource.id.asc()).all()
    return success_response(request, resources, envelope)


@router.patch("/resources/{resource_id}", response_model=ResourceOut | dict)
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")

    duplicated = (
        db.query(Resource).filter(Resource.name == payload.name, Resource.id != resource_id).first()
    )
    if duplicated:
        raise HTTPException(status_code=409, detail="resource name already exists")

    old_name = resource.name
    resource.name = payload.name
    write_audit(
        db, admin.id, "resource.update", f"resource:{resource.id}", f"{old_name} -> {resource.name}"
    )
    db.commit()
    db.refresh(resource)
    return success_response(request, resource, envelope)


@router.delete("/resources/{resource_id}")
def delete_resource(
    resource_id: int,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    resource = db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")

    has_future_booked = (
        db.query(Reservation)
        .filter(
            Reservation.resource_id == resource_id,
            Reservation.status == "BOOKED",
        )
        .first()
    )
    if has_future_booked:
        raise HTTPException(status_code=409, detail="resource has active reservations")

    write_audit(db, admin.id, "resource.delete", f"resource:{resource.id}", resource.name)
    db.delete(resource)
    db.commit()
    return success_response(request, {"deleted": True}, envelope)


@router.post("/reservations", response_model=ReservationOut | dict)
def create_reservation(
    payload: ReservationCreate,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
    user: User = Depends(get_current_user),
):
    start_at = to_utc_naive(payload.start_at, "start_at")
    end_at = to_utc_naive(payload.end_at, "end_at")

    if start_at >= end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")

    request_hash = build_reservation_request_hash(payload.resource_id, start_at, end_at)
    redis_data_key = None
    redis_lock_key = None
    if idempotency_key:
        if len(idempotency_key) > 128:
            raise HTTPException(status_code=400, detail="idempotency key too long (max 128)")

        key_scope = f"idem:reservation:create:user:{user.id}:{idempotency_key}"
        redis_data_key = f"{key_scope}:data"
        redis_lock_key = f"{key_scope}:lock"

        try:
            cached = redis.get(redis_data_key)
        except RedisError as exc:
            raise HTTPException(status_code=503, detail=f"idempotency store unavailable: {exc}")

        if cached:
            cached_data = json.loads(cached)
            if cached_data.get("request_hash") != request_hash:
                raise HTTPException(
                    status_code=409, detail="idempotency key already used with different payload"
                )

            cached_id = int(cached_data["reservation_id"])
            existing_row = (
                db.query(Reservation)
                .options(joinedload(Reservation.resource), joinedload(Reservation.user))
                .filter(Reservation.id == cached_id)
                .first()
            )
            if existing_row:
                return success_response(request, existing_row, envelope)

        lock_acquired = redis.set(
            redis_lock_key, request_hash, nx=True, ex=settings.idempotency_lock_seconds
        )
        if not lock_acquired:
            cached = redis.get(redis_data_key)
            if cached:
                cached_data = json.loads(cached)
                if cached_data.get("request_hash") != request_hash:
                    raise HTTPException(
                        status_code=409,
                        detail="idempotency key already used with different payload",
                    )
                cached_id = int(cached_data["reservation_id"])
                existing_row = (
                    db.query(Reservation)
                    .options(joinedload(Reservation.resource), joinedload(Reservation.user))
                    .filter(Reservation.id == cached_id)
                    .first()
                )
                if existing_row:
                    return success_response(request, existing_row, envelope)

            raise HTTPException(
                status_code=409, detail="request with same idempotency key is in progress"
            )

    row = None
    try:
        resource = (
            db.query(Resource).filter(Resource.id == payload.resource_id).with_for_update().first()
        )
        if not resource:
            raise HTTPException(status_code=404, detail="resource not found")

        overlap = find_overlap(
            db, resource_id=payload.resource_id, start_at=start_at, end_at=end_at
        )
        if overlap:
            raise HTTPException(status_code=409, detail="time slot already booked")

        row = Reservation(
            user_id=user.id,
            resource_id=payload.resource_id,
            start_at=start_at,
            end_at=end_at,
            status="BOOKED",
        )
        db.add(row)
        db.flush()
        write_audit(
            db,
            user.id,
            "reservation.create",
            f"reservation:{row.id}",
            f"resource_id={row.resource_id}, {row.start_at.isoformat()}~{row.end_at.isoformat()}",
        )
        db.commit()

        if redis_data_key:
            try:
                redis.setex(
                    redis_data_key,
                    settings.idempotency_ttl_seconds,
                    json.dumps({"reservation_id": row.id, "request_hash": request_hash}),
                )
            except RedisError:
                pass

        created_row = (
            db.query(Reservation)
            .options(joinedload(Reservation.resource), joinedload(Reservation.user))
            .filter(Reservation.id == row.id)
            .first()
        )
        return success_response(request, created_row, envelope)
    finally:
        if redis_lock_key:
            try:
                redis.delete(redis_lock_key)
            except RedisError:
                pass


@router.patch("/reservations/{reservation_id}", response_model=ReservationOut | dict)
def update_reservation(
    reservation_id: int,
    payload: ReservationUpdate,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(Reservation, reservation_id)
    if not row:
        raise HTTPException(status_code=404, detail="reservation not found")

    if user.role != "ADMIN" and row.user_id != user.id:
        raise HTTPException(status_code=403, detail="no permission")

    if row.status != "BOOKED":
        raise HTTPException(status_code=409, detail="only BOOKED reservation can be updated")

    start_at = to_utc_naive(payload.start_at, "start_at")
    end_at = to_utc_naive(payload.end_at, "end_at")
    if start_at >= end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")

    db.query(Resource).filter(Resource.id == row.resource_id).with_for_update().first()
    overlap = find_overlap(
        db,
        resource_id=row.resource_id,
        start_at=start_at,
        end_at=end_at,
        exclude_reservation_id=row.id,
    )
    if overlap:
        raise HTTPException(status_code=409, detail="time slot already booked")

    row.start_at = start_at
    row.end_at = end_at
    write_audit(
        db,
        user.id,
        "reservation.update",
        f"reservation:{row.id}",
        f"{start_at.isoformat()}~{end_at.isoformat()}",
    )
    db.commit()

    updated_row = (
        db.query(Reservation)
        .options(joinedload(Reservation.resource), joinedload(Reservation.user))
        .filter(Reservation.id == row.id)
        .first()
    )
    return success_response(request, updated_row, envelope)


@router.get("/reservations", response_model=list[ReservationOut] | dict)
def list_reservations(
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    status: Literal["BOOKED", "CANCELED"] | None = Query(
        default=None, description="BOOKED or CANCELED"
    ),
    resource_id: int | None = Query(default=None),
    from_at: datetime | None = Query(default=None),
    to_at: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Reservation).options(
        joinedload(Reservation.resource), joinedload(Reservation.user)
    )
    if user.role != "ADMIN":
        q = q.filter(Reservation.user_id == user.id)

    if status:
        q = q.filter(Reservation.status == status)
    if resource_id:
        q = q.filter(Reservation.resource_id == resource_id)
    if from_at:
        q = q.filter(Reservation.end_at >= to_utc_naive(from_at, "from_at"))
    if to_at:
        q = q.filter(Reservation.start_at <= to_utc_naive(to_at, "to_at"))
    reservations = q.order_by(Reservation.start_at.asc()).offset(offset).limit(limit).all()
    return success_response(request, reservations, envelope)


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationOut | dict)
def cancel_reservation(
    reservation_id: int,
    request: Request,
    envelope: bool = Header(default=False, alias="X-Response-Envelope"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(Reservation, reservation_id)
    if not row:
        raise HTTPException(status_code=404, detail="reservation not found")

    if user.role != "ADMIN" and row.user_id != user.id:
        raise HTTPException(status_code=403, detail="no permission")

    if row.status == "CANCELED":
        canceled_row = (
            db.query(Reservation)
            .options(joinedload(Reservation.resource), joinedload(Reservation.user))
            .filter(Reservation.id == row.id)
            .first()
        )
        return success_response(request, canceled_row, envelope)

    row.status = "CANCELED"
    write_audit(db, user.id, "reservation.cancel", f"reservation:{row.id}", "status=CANCELED")
    db.commit()

    canceled_row = (
        db.query(Reservation)
        .options(joinedload(Reservation.resource), joinedload(Reservation.user))
        .filter(Reservation.id == row.id)
        .first()
    )
    return success_response(request, canceled_row, envelope)
