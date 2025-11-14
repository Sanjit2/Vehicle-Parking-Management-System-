from . import db
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import relationship

class Driver(db.Model):
    __tablename__ = "Driver"
    DriverID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FirstName = db.Column(db.String(50), nullable=False)
    LastName = db.Column(db.String(50))
    PhoneNumber = db.Column(db.String(15), nullable=False, unique=True)
    Email = db.Column(db.String(100), unique=True)
    CreatedAt = db.Column(db.TIMESTAMP, server_default=db.text("CURRENT_TIMESTAMP"))

    vehicles = relationship("Vehicle", back_populates="driver")

class ParkingLot(db.Model):
    __tablename__ = "ParkingLot"
    LotID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    LotName = db.Column(db.String(100), nullable=False, unique=True)
    Capacity = db.Column(db.Integer, nullable=False)
    Location = db.Column(db.String(255))
    Levels = db.Column(db.Integer, server_default=db.text("1"))

    spots = relationship("ParkingSpot", back_populates="lot")
    staff = relationship("Staff", back_populates="lot")
    rates = relationship("ParkingRate", back_populates="lot")

class Staff(db.Model):
    __tablename__ = "Staff"
    StaffID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FirstName = db.Column(db.String(50), nullable=False)
    LastName = db.Column(db.String(50))
    Username = db.Column(db.String(50), nullable=False, unique=True)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Role = db.Column(Enum("Admin", "Attendant", name="role_enum"), nullable=False)
    LotID = db.Column(db.Integer, ForeignKey("ParkingLot.LotID"))

    lot = relationship("ParkingLot", back_populates="staff")

class Vehicle(db.Model):
    __tablename__ = "Vehicle"
    LicensePlate = db.Column(db.String(15), primary_key=True)
    VehicleType = db.Column(Enum("Car", "Bike", "Truck", "Handicap", name="veh_type_enum"), nullable=False)
    Model = db.Column(db.String(50))
    Colour = db.Column(db.String(30))
    DriverID = db.Column(db.Integer, ForeignKey("Driver.DriverID"))

    driver = relationship("Driver", back_populates="vehicles")
    tickets = relationship("ParkingTicket", back_populates="vehicle")

class ParkingSpot(db.Model):
    __tablename__ = "ParkingSpot"
    SpotID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SpotNumber = db.Column(db.String(10), nullable=False)
    SpotType = db.Column(Enum("Compact", "Standard", "Large", "Handicap", "EV", "Bike", name="spot_type_enum"), nullable=False)
    IsOccupied = db.Column(db.Boolean, server_default=db.text("FALSE"))
    LotID = db.Column(db.Integer, ForeignKey("ParkingLot.LotID"), nullable=False)

    lot = relationship("ParkingLot", back_populates="spots")
    tickets = relationship("ParkingTicket", back_populates="spot")

class ParkingRate(db.Model):
    __tablename__ = "ParkingRate"
    RateID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    RatePerHour = db.Column(db.Numeric(10, 2), nullable=False)
    VehicleType = db.Column(Enum("Car", "Bike", "Truck", "Handicap", name="rate_vehicle_enum"), nullable=False)
    SpotType = db.Column(Enum("Compact", "Standard", "Large", "Handicap", "EV", "Bike", name="rate_spot_enum"), nullable=False)
    GracePerMinute = db.Column(db.Integer, server_default=db.text("15"))
    LotID = db.Column(db.Integer, ForeignKey("ParkingLot.LotID"))

    lot = relationship("ParkingLot", back_populates="rates")
    tickets = relationship("ParkingTicket", back_populates="rate")

class ParkingTicket(db.Model):
    __tablename__ = "ParkingTicket"
    TicketID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EntryTime = db.Column(db.DateTime, nullable=False)
    ExitTime = db.Column(db.DateTime)
    PaymentStatus = db.Column(Enum("Unpaid", "Paid", "Partial", name="payment_status_enum"), server_default="Unpaid")
    TotalFee = db.Column(db.Numeric(10, 2))
    LicensePlate = db.Column(db.String(15), ForeignKey("Vehicle.LicensePlate"))
    SpotID = db.Column(db.Integer, ForeignKey("ParkingSpot.SpotID"))
    RateID = db.Column(db.Integer, ForeignKey("ParkingRate.RateID"))

    vehicle = relationship("Vehicle", back_populates="tickets")
    spot = relationship("ParkingSpot", back_populates="tickets")
    rate = relationship("ParkingRate", back_populates="tickets")
    payments = relationship("Payment", back_populates="ticket", cascade="all, delete-orphan")

class Payment(db.Model):
    __tablename__ = "Payment"
    PaymentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Amount = db.Column(db.Numeric(10, 2), nullable=False)
    PaymentMethod = db.Column(Enum("Cash", "Credit Card", "UPI", "AppWallet", name="payment_method_enum"), nullable=False)
    TransactionStatus = db.Column(Enum("Success", "Failed", "Pending", name="transaction_status_enum"), server_default="Success")
    PaymentTimestamp = db.Column(db.TIMESTAMP, server_default=db.text("CURRENT_TIMESTAMP"))
    TicketID = db.Column(db.Integer, ForeignKey("ParkingTicket.TicketID"), nullable=False)
    StaffID = db.Column(db.Integer, ForeignKey("Staff.StaffID"))

    ticket = relationship("ParkingTicket", back_populates="payments")

