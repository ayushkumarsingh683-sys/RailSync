import os
import uuid
from datetime import datetime
import enum

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# ==========================================
# 1. Database Configuration (Local SQLite)
# ==========================================
DATABASE_URL = "sqlite:///./railsync.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} # Required for SQLite multi-threading
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. Database Models
# ==========================================
class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

class Train(Base):
    __tablename__ = "trains"
    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String, unique=True, index=True, nullable=False)
    train_name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    
    coaches = relationship("Coach", back_populates="train")

class Coach(Base):
    __tablename__ = "coaches"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False)
    coach_number = Column(String, nullable=False) # e.g., "S1"
    coach_type = Column(String, nullable=False) # e.g., "Sleeper"

    train = relationship("Train", back_populates="coaches")
    seats = relationship("Seat", back_populates="coach")

class Seat(Base):
    __tablename__ = "seats"
    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    seat_number = Column(Integer, nullable=False) # e.g., 1, 2, 3...
    status = Column(String, default=SeatStatus.AVAILABLE, nullable=False)

    coach = relationship("Coach", back_populates="seats")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    pnr = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    booking_status = Column(String, default="CONFIRMED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def seed_initial_data():
    """Seeds a sample train, coach, and 10 seats if database is empty."""
    db = SessionLocal()
    try:
        train_exists = db.query(Train).first()
        if not train_exists:
            print("🌱 Seeding initial sample data into database...")
            sample_train = Train(
                train_number="12424",
                train_name="Rajdhani Express",
                source="New Delhi",
                destination="Dibrugarh"
            )
            db.add(sample_train)
            db.commit()
            db.refresh(sample_train)

            sample_coach = Coach(
                train_id=sample_train.id,
                coach_number="S1",
                coach_type="Sleeper"
            )
            db.add(sample_coach)
            db.commit()
            db.refresh(sample_coach)

            # Create seats 1 to 10
            for i in range(1, 11):
                seat = Seat(
                    coach_id=sample_coach.id,
                    seat_number=i,
                    status=SeatStatus.AVAILABLE
                )
                db.add(seat)
            db.commit()
            print("✅ Sample data seeded successfully! Train ID: 1, Coach ID: 1, Seats: 1-10")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

# ==========================================
# 3. Pydantic Schemas
# ==========================================
class BookingRequest(BaseModel):
    user_id: int
    train_id: int
    coach_id: int
    seat_number: int

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. FastAPI App & Routes
# ==========================================
app = FastAPI(
    title="RailSync - Railway Reservation Backend",
    description="IRCTC-style backend featuring high-concurrency seat reservation.",
    version="1.0.0"
)

# Enable CORS for local webpage testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    seed_initial_data()
    print("Database tables initialized successfully!")

@app.get("/")
def home():
    return {"status": "ok", "message": "RailSync Railway Concurrency API is running."}

# CRITICAL ENDPOINT: Seat Booking
@app.post("/api/book-seat")
def book_seat(payload: BookingRequest, db: Session = Depends(get_db)):
    try:
        seat = db.query(Seat).join(Coach).filter(
            Coach.train_id == payload.train_id,
            Coach.id == payload.coach_id,
            Seat.seat_number == payload.seat_number
        ).first()

        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found.")

        if seat.status != SeatStatus.AVAILABLE:
            raise HTTPException(
                status_code=400, 
                detail=f"Seat {payload.seat_number} is already {seat.status}. Double-booking prevented!"
            )

        seat.status = SeatStatus.BOOKED
        pnr_code = f"PNR-{uuid.uuid4().hex[:8].upper()}"
        
        new_booking = Booking(
            pnr=pnr_code,
            user_id=payload.user_id,
            seat_id=seat.id,
            booking_status="CONFIRMED"
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {
            "success": True,
            "message": "Ticket successfully booked!",
            "pnr": pnr_code,
            "train_id": payload.train_id,
            "coach_id": payload.coach_id,
            "seat_number": payload.seat_number
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    import os
import uuid
from datetime import datetime
import enum

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# ==========================================
# 1. Database Configuration (Local SQLite)
# ==========================================
DATABASE_URL = "sqlite:///./railsync.db"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} # Required for SQLite multi-threading
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 2. Database Models
# ==========================================
class SeatStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

class Train(Base):
    __tablename__ = "trains"
    id = Column(Integer, primary_key=True, index=True)
    train_number = Column(String, unique=True, index=True, nullable=False)
    train_name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    
    coaches = relationship("Coach", back_populates="train")

class Coach(Base):
    __tablename__ = "coaches"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(Integer, ForeignKey("trains.id"), nullable=False)
    coach_number = Column(String, nullable=False) # e.g., "S1"
    coach_type = Column(String, nullable=False) # e.g., "Sleeper"

    train = relationship("Train", back_populates="coaches")
    seats = relationship("Seat", back_populates="coach")

class Seat(Base):
    __tablename__ = "seats"
    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("coaches.id"), nullable=False)
    seat_number = Column(Integer, nullable=False) # e.g., 1, 2, 3...
    status = Column(String, default=SeatStatus.AVAILABLE, nullable=False)

    coach = relationship("Coach", back_populates="seats")

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    pnr = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False)
    booking_status = Column(String, default="CONFIRMED", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def seed_initial_data():
    """Seeds a sample train, coach, and 10 seats if database is empty."""
    db = SessionLocal()
    try:
        train_exists = db.query(Train).first()
        if not train_exists:
            print("🌱 Seeding initial sample data into database...")
            sample_train = Train(
                train_number="12424",
                train_name="Rajdhani Express",
                source="New Delhi",
                destination="Dibrugarh"
            )
            db.add(sample_train)
            db.commit()
            db.refresh(sample_train)

            sample_coach = Coach(
                train_id=sample_train.id,
                coach_number="S1",
                coach_type="Sleeper"
            )
            db.add(sample_coach)
            db.commit()
            db.refresh(sample_coach)

            # Create seats 1 to 10
            for i in range(1, 11):
                seat = Seat(
                    coach_id=sample_coach.id,
                    seat_number=i,
                    status=SeatStatus.AVAILABLE
                )
                db.add(seat)
            db.commit()
            print("✅ Sample data seeded successfully! Train ID: 1, Coach ID: 1, Seats: 1-10")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

# ==========================================
# 3. Pydantic Schemas
# ==========================================
class BookingRequest(BaseModel):
    user_id: int
    train_id: int
    coach_id: int
    seat_number: int

# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 4. FastAPI App & Routes
# ==========================================
app = FastAPI(
    title="RailSync - Railway Reservation Backend",
    description="IRCTC-style backend featuring high-concurrency seat reservation.",
    version="1.0.0"
)

# Enable CORS for local webpage testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    seed_initial_data()
    print("Database tables initialized successfully!")

@app.get("/")
def home():
    return {"status": "ok", "message": "RailSync Railway Concurrency API is running."}

# CRITICAL ENDPOINT: Seat Booking
@app.post("/api/book-seat")
def book_seat(payload: BookingRequest, db: Session = Depends(get_db)):
    try:
        seat = db.query(Seat).join(Coach).filter(
            Coach.train_id == payload.train_id,
            Coach.id == payload.coach_id,
            Seat.seat_number == payload.seat_number
        ).first()

        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found.")

        if seat.status != SeatStatus.AVAILABLE:
            raise HTTPException(
                status_code=400, 
                detail=f"Seat {payload.seat_number} is already {seat.status}. Double-booking prevented!"
            )

        seat.status = SeatStatus.BOOKED
        pnr_code = f"PNR-{uuid.uuid4().hex[:8].upper()}"
        
        new_booking = Booking(
            pnr=pnr_code,
            user_id=payload.user_id,
            seat_id=seat.id,
            booking_status="CONFIRMED"
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)

        return {
            "success": True,
            "message": "Ticket successfully booked!",
            "pnr": pnr_code,
            "train_id": payload.train_id,
            "coach_id": payload.coach_id,
            "seat_number": payload.seat_number
        }

    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))