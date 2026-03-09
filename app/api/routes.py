from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Reservation, Resource, User
from app.schemas import (
    ReservationCreate,
    ReservationOut,
    ResourceCreate,
    ResourceOut,
    UserCreate,
    UserOut,
)

router = APIRouter()


@router.get('/health')
def health():
    return {"status": "ok"}


@router.post('/users', response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post('/resources', response_model=ResourceOut)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db)):
    resource = Resource(name=payload.name)
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.post('/reservations', response_model=ReservationOut)
def create_reservation(payload: ReservationCreate, db: Session = Depends(get_db)):
    if payload.start_at >= payload.end_at:
        raise HTTPException(status_code=400, detail="start_at must be before end_at")

    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

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
        user_id=payload.user_id,
        resource_id=payload.resource_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        status="BOOKED",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get('/reservations', response_model=list[ReservationOut])
def list_reservations(db: Session = Depends(get_db)):
    return db.query(Reservation).order_by(Reservation.start_at.asc()).all()


@router.post('/reservations/{reservation_id}/cancel', response_model=ReservationOut)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db)):
    row = db.get(Reservation, reservation_id)
    if not row:
        raise HTTPException(status_code=404, detail="reservation not found")
    row.status = "CANCELED"
    db.commit()
    db.refresh(row)
    return row
