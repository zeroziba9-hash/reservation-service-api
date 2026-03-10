from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.deps import get_current_user, get_db, require_admin
from app.models import AuditLog, Reservation, Resource, User
from app.schemas import (
    ReservationCreate,
    ReservationOut,
    ResourceCreate,
    ResourceOut,
    SignupRequest,
    TokenOut,
    UserOut,
)

router = APIRouter()


def write_audit(db: Session, actor_user_id: int | None, action: str, target: str, detail: str):
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, target=target, detail=detail))


@router.get('/health')
def health():
    return {"status": "ok"}


@router.post('/auth/signup', response_model=UserOut)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
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
    return user


@router.post('/auth/login', response_model=TokenOut)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

    token = create_access_token(user.email)
    return TokenOut(access_token=token)


@router.post('/resources', response_model=ResourceOut)
def create_resource(
    payload: ResourceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    resource = Resource(name=payload.name)
    db.add(resource)
    db.flush()
    write_audit(db, admin.id, "resource.create", f"resource:{resource.id}", payload.name)
    db.commit()
    db.refresh(resource)
    return resource


@router.post('/reservations', response_model=ReservationOut)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.start_at >= payload.end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")

    resource = db.get(Resource, payload.resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="resource not found")

    overlap = db.query(Reservation).filter(
        and_(
            Reservation.resource_id == payload.resource_id,
            Reservation.status == "BOOKED",
            or_(
                and_(Reservation.start_at <= payload.start_at, Reservation.end_at > payload.start_at),
                and_(Reservation.start_at < payload.end_at, Reservation.end_at >= payload.end_at),
                and_(Reservation.start_at >= payload.start_at, Reservation.end_at <= payload.end_at),
            ),
        )
    ).first()

    if overlap:
        raise HTTPException(status_code=409, detail="time slot already booked")

    row = Reservation(
        user_id=user.id,
        resource_id=payload.resource_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
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
    db.refresh(row)
    return row


@router.get('/reservations', response_model=list[ReservationOut])
def list_reservations(
    status: Literal["BOOKED", "CANCELED"] | None = Query(default=None, description="BOOKED or CANCELED"),
    resource_id: int | None = Query(default=None),
    from_at: datetime | None = Query(default=None),
    to_at: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    q = db.query(Reservation)
    if status:
        q = q.filter(Reservation.status == status)
    if resource_id:
        q = q.filter(Reservation.resource_id == resource_id)
    if from_at:
        q = q.filter(Reservation.end_at >= from_at)
    if to_at:
        q = q.filter(Reservation.start_at <= to_at)
    return q.order_by(Reservation.start_at.asc()).offset(offset).limit(limit).all()


@router.post('/reservations/{reservation_id}/cancel', response_model=ReservationOut)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.get(Reservation, reservation_id)
    if not row:
        raise HTTPException(status_code=404, detail="reservation not found")

    if user.role != "ADMIN" and row.user_id != user.id:
        raise HTTPException(status_code=403, detail="no permission")

    row.status = "CANCELED"
    write_audit(db, user.id, "reservation.cancel", f"reservation:{row.id}", "status=CANCELED")
    db.commit()
    db.refresh(row)
    return row
