from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from sqlalchemy import text, func, case
from . import db
from .models import Driver, Vehicle, ParkingLot, ParkingSpot, ParkingRate, ParkingTicket, Payment, Staff
from datetime import datetime
import math
from .db_helpers import add_new_ticket_and_occupy_spot, create_parking_lot_with_default_rates

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__)

@main_bp.route("/")
def index():
    lots = ParkingLot.query.all()
    tickets_unpaid = ParkingTicket.query.filter_by(PaymentStatus="Unpaid").count()
    spots_total = ParkingSpot.query.count()
    spots_occupied = ParkingSpot.query.filter_by(IsOccupied=True).count()

    drivers_count = Driver.query.count()
    vehicles_count = Vehicle.query.count()
    staff_count = db.session.query(func.count()).select_from(Staff).scalar()

    tickets_today = db.session.query(func.count(ParkingTicket.TicketID)).filter(func.date(ParkingTicket.EntryTime) == func.curdate()).scalar() or 0
    revenue_today = db.session.query(func.coalesce(func.sum(Payment.Amount), 0)).filter(func.date(Payment.PaymentTimestamp) == func.curdate()).scalar() or 0
    revenue_month = db.session.query(func.coalesce(func.sum(Payment.Amount), 0)).filter(func.month(Payment.PaymentTimestamp) == func.month(func.now()), func.year(Payment.PaymentTimestamp) == func.year(func.now())).scalar() or 0

    # Charts: tickets per day (last 7) and revenue per day (last 7)
    tickets_per_day_rows = (
        db.session.query(func.date(ParkingTicket.EntryTime).label("d"), func.count(ParkingTicket.TicketID).label("c"))
        .group_by(func.date(ParkingTicket.EntryTime))
        .order_by(func.date(ParkingTicket.EntryTime).desc())
        .limit(7)
        .all()
    )
    tickets_per_day = list(reversed([(str(r.d), int(r.c)) for r in tickets_per_day_rows]))

    revenue_per_day_rows = (
        db.session.query(func.date(Payment.PaymentTimestamp).label("d"), func.coalesce(func.sum(Payment.Amount), 0).label("s"))
        .group_by(func.date(Payment.PaymentTimestamp))
        .order_by(func.date(Payment.PaymentTimestamp).desc())
        .limit(7)
        .all()
    )
    revenue_per_day = list(reversed([(str(r.d), float(r.s)) for r in revenue_per_day_rows]))

    # Live occupancy per lot
    # Use lot Capacity as total; occupied from spots table
    occupancy_rows = (
        db.session.query(
            ParkingLot.LotID,
            ParkingLot.LotName,
            ParkingLot.Capacity.label("total"),
            func.coalesce(
                func.sum(case((ParkingSpot.IsOccupied == True, 1), else_=0)),
                0,
            ).label("occupied"),
        )
        .outerjoin(ParkingSpot, ParkingSpot.LotID == ParkingLot.LotID)
        .group_by(ParkingLot.LotID, ParkingLot.LotName, ParkingLot.Capacity)
        .order_by(ParkingLot.LotID.asc())
        .all()
    )
    occupancy = [
        {
            "lotId": row.LotID,
            "lotName": row.LotName,
            "total": int(row.total or 0),
            "occupied": int(row.occupied or 0),
        }
        for row in occupancy_rows
    ]

    # Alerts: overdue/unpaid open tickets (no ExitTime and Unpaid)
    alerts_tickets = (
        ParkingTicket.query.filter(ParkingTicket.PaymentStatus == "Unpaid")
        .order_by(ParkingTicket.EntryTime.asc())
        .limit(5)
        .all()
    )

    # Recent activity
    recent_tickets = ParkingTicket.query.order_by(ParkingTicket.TicketID.desc()).limit(5).all()
    recent_payments = Payment.query.order_by(Payment.PaymentID.desc()).limit(5).all()

    return render_template(
        "index.html",
        lots=lots,
        tickets_unpaid=tickets_unpaid,
        spots_total=spots_total,
        spots_occupied=spots_occupied,
        drivers_count=drivers_count,
        vehicles_count=vehicles_count,
        staff_count=staff_count,
        tickets_today=int(tickets_today or 0),
        revenue_today=float(revenue_today or 0),
        revenue_month=float(revenue_month or 0),
        tickets_per_day=tickets_per_day,
        revenue_per_day=revenue_per_day,
        occupancy=occupancy,
        alerts_tickets=alerts_tickets,
        recent_tickets=recent_tickets,
        recent_payments=recent_payments,
    )

@main_bp.route("/drivers")
def list_drivers():
    drivers = Driver.query.order_by(Driver.DriverID.asc()).all()
    return render_template("drivers.html", drivers=drivers)

@main_bp.route("/drivers/new", methods=["GET", "POST"])
def new_driver():
    if request.method == "POST":
        first = request.form.get("FirstName")
        last = request.form.get("LastName")
        phone = request.form.get("PhoneNumber")
        email = request.form.get("Email")
        if not first or not phone:
            abort(400, "FirstName and PhoneNumber are required")
        d = Driver(FirstName=first, LastName=last, PhoneNumber=phone, Email=email)
        db.session.add(d)
        db.session.commit()
        return redirect(url_for("main.list_drivers"))
    return render_template("driver_form.html")

@main_bp.route("/drivers/<int:driver_id>/edit", methods=["GET", "POST"])
def edit_driver(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    if request.method == "POST":
        driver.FirstName = request.form.get("FirstName") or driver.FirstName
        driver.LastName = request.form.get("LastName")
        driver.PhoneNumber = request.form.get("PhoneNumber") or driver.PhoneNumber
        driver.Email = request.form.get("Email")
        db.session.commit()
        return redirect(url_for("main.list_drivers"))
    return render_template("driver_form.html", driver=driver)

@main_bp.route("/drivers/<int:driver_id>/delete", methods=["POST"])
def delete_driver(driver_id: int):
    driver = Driver.query.get_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    return redirect(url_for("main.list_drivers"))

@main_bp.route("/tickets")
def list_tickets():
    tickets = ParkingTicket.query.order_by(ParkingTicket.TicketID.asc()).all()
    return render_template("tickets.html", tickets=tickets)

@main_bp.route("/tickets/new", methods=["GET", "POST"])
def new_ticket():
    vehicles = Vehicle.query.all()
    spots = ParkingSpot.query.filter_by(IsOccupied=False).all()
    rates = ParkingRate.query.all()
    if request.method == "POST":
        license_plate = request.form.get("LicensePlate")
        spot_id = request.form.get("SpotID", type=int)
        rate_id = request.form.get("RateID", type=int)
        entry_time = request.form.get("EntryTime")  # 'YYYY-MM-DD HH:MM:SS'
        if not (license_plate and spot_id and rate_id and entry_time):
            abort(400, "All fields are required")
        try:
            # Use stored procedure to create ticket and mark spot occupied atomically
            add_new_ticket_and_occupy_spot(license_plate, spot_id, rate_id, entry_time)
        except Exception as e:
            # Surface DB errors to client
            abort(400, str(e))
        return redirect(url_for("main.list_tickets"))
    return render_template("ticket_form.html", vehicles=vehicles, spots=spots, rates=rates)

@main_bp.route("/tickets/<int:ticket_id>/edit", methods=["GET", "POST"])
def edit_ticket(ticket_id: int):
    ticket = ParkingTicket.query.get_or_404(ticket_id)
    vehicles = Vehicle.query.all()
    spots = ParkingSpot.query.all()
    rates = ParkingRate.query.all()
    if request.method == "POST":
        ticket.LicensePlate = request.form.get("LicensePlate") or ticket.LicensePlate
        ticket.SpotID = request.form.get("SpotID", type=int) or ticket.SpotID
        ticket.RateID = request.form.get("RateID", type=int) or ticket.RateID
        ticket.EntryTime = request.form.get("EntryTime") or ticket.EntryTime
        ticket.ExitTime = request.form.get("ExitTime") or ticket.ExitTime
        db.session.commit()
        return redirect(url_for("main.list_tickets"))
    return render_template("ticket_form.html", ticket=ticket, vehicles=vehicles, spots=spots, rates=rates)

@main_bp.route("/tickets/<int:ticket_id>/delete", methods=["POST"])
def delete_ticket(ticket_id: int):
    ticket = ParkingTicket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    return redirect(url_for("main.list_tickets"))

# ---- Vehicle CRUD ----

@main_bp.route("/vehicles")
def list_vehicles():
    vehicles = Vehicle.query.order_by(Vehicle.LicensePlate.asc()).all()
    drivers = Driver.query.all()
    return render_template("vehicles.html", vehicles=vehicles, drivers=drivers)

@main_bp.route("/vehicles/new", methods=["GET", "POST"])
def new_vehicle():
    drivers = Driver.query.all()
    if request.method == "POST":
        plate = request.form.get("LicensePlate")
        vtype = request.form.get("VehicleType")
        model = request.form.get("Model")
        colour = request.form.get("Colour")
        driver_id = request.form.get("DriverID", type=int)
        if not (plate and vtype):
            abort(400, "LicensePlate and VehicleType are required")
        v = Vehicle(LicensePlate=plate, VehicleType=vtype, Model=model, Colour=colour, DriverID=driver_id)
        db.session.add(v)
        db.session.commit()
        return redirect(url_for("main.list_vehicles"))
    return render_template("vehicle_form.html", drivers=drivers)

@main_bp.route("/vehicles/<string:license_plate>/edit", methods=["GET", "POST"])
def edit_vehicle(license_plate: str):
    vehicle = Vehicle.query.get_or_404(license_plate)
    drivers = Driver.query.all()
    if request.method == "POST":
        vehicle.VehicleType = request.form.get("VehicleType") or vehicle.VehicleType
        vehicle.Model = request.form.get("Model")
        vehicle.Colour = request.form.get("Colour")
        vehicle.DriverID = request.form.get("DriverID", type=int)
        db.session.commit()
        return redirect(url_for("main.list_vehicles"))
    return render_template("vehicle_form.html", vehicle=vehicle, drivers=drivers)

@main_bp.route("/vehicles/<string:license_plate>/delete", methods=["POST"])
def delete_vehicle(license_plate: str):
    vehicle = Vehicle.query.get_or_404(license_plate)
    db.session.delete(vehicle)
    db.session.commit()
    return redirect(url_for("main.list_vehicles"))

# ---- Parking Lot CRUD ----

@main_bp.route("/lots")
def list_lots():
    lots = ParkingLot.query.order_by(ParkingLot.LotID.asc()).all()
    return render_template("lots.html", lots=lots)

@main_bp.route("/lots/new", methods=["GET", "POST"])
def new_lot():
    if request.method == "POST":
        name = request.form.get("LotName")
        capacity = request.form.get("Capacity", type=int)
        location = request.form.get("Location")
        levels = request.form.get("Levels", type=int)
        if not (name and capacity is not None):
            abort(400, "LotName and Capacity are required")
        try:
            # Use stored procedure to create lot and associated default rates in a single transaction
            create_parking_lot_with_default_rates(name, capacity, location, levels)
        except Exception as e:
            abort(400, str(e))
        return redirect(url_for("main.list_lots"))
    return render_template("lot_form.html")

@main_bp.route("/lots/<int:lot_id>/edit", methods=["GET", "POST"])
def edit_lot(lot_id: int):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == "POST":
        lot.LotName = request.form.get("LotName") or lot.LotName
        lot.Capacity = request.form.get("Capacity", type=int) or lot.Capacity
        lot.Location = request.form.get("Location")
        lot.Levels = request.form.get("Levels", type=int) or lot.Levels
        db.session.commit()
        return redirect(url_for("main.list_lots"))
    return render_template("lot_form.html", lot=lot)

@main_bp.route("/lots/<int:lot_id>/delete", methods=["POST"])
def delete_lot(lot_id: int):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    return redirect(url_for("main.list_lots"))

# ---- Parking Spot CRUD ----

@main_bp.route("/spots")
def list_spots():
    spots = ParkingSpot.query.order_by(ParkingSpot.SpotID.asc()).all()
    lots = ParkingLot.query.all()
    return render_template("spots.html", spots=spots, lots=lots)

@main_bp.route("/spots/new", methods=["GET", "POST"])
def new_spot():
    lots = ParkingLot.query.all()
    if request.method == "POST":
        number = request.form.get("SpotNumber")
        spot_type = request.form.get("SpotType")
        lot_id = request.form.get("LotID", type=int)
        is_occupied = bool(request.form.get("IsOccupied"))
        if not (number and spot_type and lot_id):
            abort(400, "SpotNumber, SpotType and LotID are required")
        s = ParkingSpot(SpotNumber=number, SpotType=spot_type, LotID=lot_id, IsOccupied=is_occupied)
        db.session.add(s)
        db.session.commit()
        return redirect(url_for("main.list_spots"))
    return render_template("spot_form.html", lots=lots)

@main_bp.route("/spots/<int:spot_id>/edit", methods=["GET", "POST"])
def edit_spot(spot_id: int):
    spot = ParkingSpot.query.get_or_404(spot_id)
    lots = ParkingLot.query.all()
    if request.method == "POST":
        spot.SpotNumber = request.form.get("SpotNumber") or spot.SpotNumber
        spot.SpotType = request.form.get("SpotType") or spot.SpotType
        spot.LotID = request.form.get("LotID", type=int) or spot.LotID
        spot.IsOccupied = bool(request.form.get("IsOccupied"))
        db.session.commit()
        return redirect(url_for("main.list_spots"))
    return render_template("spot_form.html", spot=spot, lots=lots)

@main_bp.route("/spots/<int:spot_id>/delete", methods=["POST"])
def delete_spot(spot_id: int):
    spot = ParkingSpot.query.get_or_404(spot_id)
    db.session.delete(spot)
    db.session.commit()
    return redirect(url_for("main.list_spots"))

# ---- Parking Rate CRUD ----

@main_bp.route("/rates")
def list_rates():
    rates = ParkingRate.query.order_by(ParkingRate.RateID.asc()).all()
    lots = ParkingLot.query.all()
    return render_template("rates.html", rates=rates, lots=lots)

@main_bp.route("/rates/new", methods=["GET", "POST"])
def new_rate():
    lots = ParkingLot.query.all()
    if request.method == "POST":
        rate_per_hour = request.form.get("RatePerHour")
        veh_type = request.form.get("VehicleType")
        spot_type = request.form.get("SpotType")
        grace = request.form.get("GracePerMinute", type=int)
        lot_id = request.form.get("LotID", type=int)
        if not (rate_per_hour and veh_type and spot_type):
            abort(400, "RatePerHour, VehicleType, SpotType are required")
        r = ParkingRate(RatePerHour=rate_per_hour, VehicleType=veh_type, SpotType=spot_type, GracePerMinute=grace, LotID=lot_id)
        db.session.add(r)
        db.session.commit()
        return redirect(url_for("main.list_rates"))
    return render_template("rate_form.html", lots=lots)

@main_bp.route("/rates/<int:rate_id>/edit", methods=["GET", "POST"])
def edit_rate(rate_id: int):
    rate = ParkingRate.query.get_or_404(rate_id)
    lots = ParkingLot.query.all()
    if request.method == "POST":
        rate.RatePerHour = request.form.get("RatePerHour") or rate.RatePerHour
        rate.VehicleType = request.form.get("VehicleType") or rate.VehicleType
        rate.SpotType = request.form.get("SpotType") or rate.SpotType
        rate.GracePerMinute = request.form.get("GracePerMinute", type=int) or rate.GracePerMinute
        rate.LotID = request.form.get("LotID", type=int)
        db.session.commit()
        return redirect(url_for("main.list_rates"))
    return render_template("rate_form.html", rate=rate, lots=lots)

@main_bp.route("/rates/<int:rate_id>/delete", methods=["POST"])
def delete_rate(rate_id: int):
    rate = ParkingRate.query.get_or_404(rate_id)
    db.session.delete(rate)
    db.session.commit()
    return redirect(url_for("main.list_rates"))

# ---- Payment CRUD ----

@main_bp.route("/payments")
def list_payments():
    payments = Payment.query.order_by(Payment.PaymentID.asc()).all()
    tickets = ParkingTicket.query.all()
    return render_template("payments.html", payments=payments, tickets=tickets)

@main_bp.route("/payments/new", methods=["GET", "POST"])
def new_payment():
    tickets = ParkingTicket.query.all()
    if request.method == "POST":
        amount = request.form.get("Amount")
        method = request.form.get("PaymentMethod")
        status = request.form.get("TransactionStatus")
        ticket_id = request.form.get("TicketID", type=int)
        if not (amount and method and ticket_id):
            abort(400, "Amount, PaymentMethod, TicketID are required")
        p = Payment(Amount=amount, PaymentMethod=method, TransactionStatus=status, TicketID=ticket_id)
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("main.list_payments"))
    return render_template("payment_form.html", tickets=tickets)

@main_bp.route("/payments/<int:payment_id>/edit", methods=["GET", "POST"])
def edit_payment(payment_id: int):
    payment = Payment.query.get_or_404(payment_id)
    tickets = ParkingTicket.query.all()
    if request.method == "POST":
        payment.Amount = request.form.get("Amount") or payment.Amount
        payment.PaymentMethod = request.form.get("PaymentMethod") or payment.PaymentMethod
        payment.TransactionStatus = request.form.get("TransactionStatus") or payment.TransactionStatus
        payment.TicketID = request.form.get("TicketID", type=int) or payment.TicketID
        db.session.commit()
        return redirect(url_for("main.list_payments"))
    return render_template("payment_form.html", payment=payment, tickets=tickets)

@main_bp.route("/payments/<int:payment_id>/delete", methods=["POST"])
def delete_payment(payment_id: int):
    payment = Payment.query.get_or_404(payment_id)
    db.session.delete(payment)
    db.session.commit()
    return redirect(url_for("main.list_payments"))

# ---- Staff CRUD ----

@main_bp.route("/staff")
def list_staff():
    staff = Staff.query.order_by(Staff.StaffID.asc()).all()
    lots = ParkingLot.query.all()
    return render_template("staff.html", staff=staff, lots=lots)

@main_bp.route("/staff/new", methods=["GET", "POST"])
def new_staff():
    lots = ParkingLot.query.all()
    if request.method == "POST":
        first = request.form.get("FirstName")
        last = request.form.get("LastName")
        username = request.form.get("Username")
        password_hash = request.form.get("PasswordHash")
        role = request.form.get("Role")
        lot_id = request.form.get("LotID", type=int)
        if not (first and username and password_hash and role):
            abort(400, "FirstName, Username, PasswordHash, Role are required")
        s = Staff(FirstName=first, LastName=last, Username=username, PasswordHash=password_hash, Role=role, LotID=lot_id)
        db.session.add(s)
        db.session.commit()
        return redirect(url_for("main.list_staff"))
    return render_template("staff_form.html", lots=lots)

@main_bp.route("/staff/<int:staff_id>/edit", methods=["GET", "POST"])
def edit_staff(staff_id: int):
    staff = Staff.query.get_or_404(staff_id)
    lots = ParkingLot.query.all()
    if request.method == "POST":
        staff.FirstName = request.form.get("FirstName") or staff.FirstName
        staff.LastName = request.form.get("LastName")
        staff.Username = request.form.get("Username") or staff.Username
        staff.PasswordHash = request.form.get("PasswordHash") or staff.PasswordHash
        staff.Role = request.form.get("Role") or staff.Role
        staff.LotID = request.form.get("LotID", type=int)
        db.session.commit()
        return redirect(url_for("main.list_staff"))
    return render_template("staff_form.html", staff=staff, lots=lots)

@main_bp.route("/staff/<int:staff_id>/delete", methods=["POST"])
def delete_staff(staff_id: int):
    staff = Staff.query.get_or_404(staff_id)
    db.session.delete(staff)
    db.session.commit()
    return redirect(url_for("main.list_staff"))

# --- JSON API ---

@api_bp.route("/available-spots/<int:lot_id>")
def available_spots(lot_id: int):
    # Call MySQL function fn_GetAvailableSpotsCount
    result = db.session.execute(text("SELECT fn_GetAvailableSpotsCount(:lot_id) AS available"), {"lot_id": lot_id}).mappings().first()
    available = result.get("available") if result else 0
    return jsonify({"lotId": lot_id, "available": int(available or 0)})


@api_bp.route("/available-spots-list/<int:lot_id>")
def available_spots_list(lot_id: int):
    # Return list of unoccupied spots in a lot so frontend can populate a dropdown
    # For debugging: also return ALL spots so we can see what's in the lot
    all_spots = ParkingSpot.query.filter_by(LotID=lot_id).order_by(ParkingSpot.SpotNumber.asc()).all()
    available_spots = ParkingSpot.query.filter_by(LotID=lot_id, IsOccupied=False).order_by(ParkingSpot.SpotNumber.asc()).all()
    
    data = [ {"SpotID": s.SpotID, "SpotNumber": s.SpotNumber} for s in available_spots ]
    
    # Include debug info
    debug_info = {
        "totalSpots": len(all_spots),
        "availableCount": len(available_spots),
        "allSpots": [{"SpotID": s.SpotID, "SpotNumber": s.SpotNumber, "IsOccupied": s.IsOccupied} for s in all_spots]
    }
    
    return jsonify({
        "lotId": lot_id, 
        "spots": data,
        "debug": debug_info
    })

@api_bp.route("/swap-spot", methods=["POST"])
def swap_spot():
    data = request.get_json(force=True)
    ticket_id = data.get("ticketId")
    new_spot_number = data.get("newSpotNumber")
    if not ticket_id or not new_spot_number:
        abort(400, "ticketId and newSpotNumber are required")
    try:
        db.session.execute(text("CALL sp_SwapParkingSpots(:tid, :spot)"), {"tid": ticket_id, "spot": new_spot_number})
        db.session.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400

@api_bp.route("/process-exit", methods=["POST"])
def process_exit():
    data = request.get_json(force=True)
    ticket_id = data.get("ticketId")
    amount = data.get("amountPaid")
    method = data.get("paymentMethod")  # 'Cash', 'Credit Card', 'UPI', 'AppWallet'
    if not ticket_id or amount is None or not method:
        abort(400, "ticketId, amountPaid, paymentMethod are required")
    
    # Validate payment amount matches the required fee
    ticket = ParkingTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({"status": "error", "message": "Ticket not found"}), 404
    
    if not ticket.EntryTime:
        return jsonify({"status": "error", "message": "Ticket has no entry time"}), 400
    
    # Calculate expected fee
    rate = ParkingRate.query.get(ticket.RateID) if ticket.RateID else None
    if not rate:
        return jsonify({"status": "error", "message": "Rate not found for ticket"}), 400
    
    now = datetime.now()
    duration_hours = (now - ticket.EntryTime).total_seconds() / 3600.0
    billed_hours = math.ceil(duration_hours if duration_hours > 0 else 0)
    expected_fee = float(billed_hours * float(rate.RatePerHour))
    
    # Validate exact amount (allow 1 cent tolerance for floating point)
    if abs(float(amount) - expected_fee) > 0.01:
        return jsonify({
            "status": "error", 
            "message": f"Payment amount (₹{amount}) does not match required fee (₹{expected_fee:.2f}). Please pay the exact amount."
        }), 400
    
    try:
        db.session.execute(text("CALL sp_ProcessVehicleExit(:tid, :amt, :pm)"), {"tid": ticket_id, "amt": amount, "pm": method})
        db.session.commit()
        # Refresh ticket and spot info
        ticket = ParkingTicket.query.get(ticket_id)
        return jsonify({
            "status": "ok",
            "ticketId": ticket_id,
            "paymentStatus": ticket.PaymentStatus if ticket else None,
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400


@api_bp.route('/estimate-exit/<int:ticket_id>')
def estimate_exit(ticket_id: int):
    # Estimate fee for a ticket without updating DB (used to show total to user before payment)
    ticket = ParkingTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({"status": "error", "message": 'Ticket not found'}), 404

    if not ticket.EntryTime:
        return jsonify({"status": "error", "message": 'Ticket has no EntryTime'}), 400

    # Get rate
    rate = ParkingRate.query.get(ticket.RateID) if ticket.RateID else None
    if not rate:
        return jsonify({"status": "error", "message": 'Rate not found for ticket'}), 400

    now = datetime.now()
    duration_hours = (now - ticket.EntryTime).total_seconds() / 3600.0
    billed_hours = math.ceil(duration_hours if duration_hours > 0 else 0)
    total_fee = float(billed_hours * float(rate.RatePerHour))

    return jsonify({
        "status": "ok",
        "ticketId": ticket_id,
        "entryTime": ticket.EntryTime.isoformat(),
        "estimatedHours": duration_hours,
        "billedHours": billed_hours,
        "ratePerHour": float(rate.RatePerHour),
        "estimatedTotal": total_fee
    })



@api_bp.route('/create-lot-default', methods=['POST'])
def api_create_lot_default():
    data = request.get_json(force=True)
    name = data.get('LotName')
    capacity = data.get('Capacity')
    location = data.get('Location')
    levels = data.get('Levels', 1)
    if not name or capacity is None:
        return jsonify({'status': 'error', 'message': 'LotName and Capacity are required'}), 400
    try:
        create_parking_lot_with_default_rates(name, int(capacity), location, int(levels))
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@api_bp.route('/add-ticket', methods=['POST'])
def api_add_ticket():
    data = request.get_json(force=True)
    license_plate = data.get('LicensePlate')
    spot_id = data.get('SpotID')
    rate_id = data.get('RateID')
    entry_time = data.get('EntryTime')
    if not (license_plate and spot_id and rate_id):
        return jsonify({'status': 'error', 'message': 'LicensePlate, SpotID and RateID are required'}), 400
    try:
        add_new_ticket_and_occupy_spot(license_plate, int(spot_id), int(rate_id), entry_time)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@api_bp.route('/driver-total-spent/<int:driver_id>')
def api_driver_total_spent(driver_id: int):
    """Call fn_GetDriverTotalSpent function to get total spent by a driver"""
    try:
        result = db.session.execute(
            text("SELECT fn_GetDriverTotalSpent(:driver_id) AS total_spent"), 
            {"driver_id": driver_id}
        ).mappings().first()
        total = float(result.get("total_spent") or 0) if result else 0.0
        return jsonify({"status": "ok", "driverId": driver_id, "totalSpent": total})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

