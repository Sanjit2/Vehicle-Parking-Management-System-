from datetime import datetime
from sqlalchemy import text
from . import db


def create_parking_lot_with_default_rates(lot_name: str, capacity: int, location: str = None, levels: int = 1):
    """Call stored procedure sp_CreateNewParkingLotWithDefaultRates.

    Uses a transactional engine connection. Raises any exception that occurs.
    """
    params = {"p_LotName": lot_name, "p_Capacity": capacity, "p_Location": location, "p_Levels": levels}
    call = text("CALL sp_CreateNewParkingLotWithDefaultRates(:p_LotName, :p_Capacity, :p_Location, :p_Levels)")
    with db.engine.begin() as conn:
        conn.execute(call, params)


def add_new_ticket_and_occupy_spot(license_plate: str, spot_id: int, rate_id: int, entry_time: str = None):
    """Call stored procedure sp_AddNewTicketAndOccupySpot.

    entry_time may be a datetime or a string 'YYYY-MM-DD HH:MM:SS'. If None, NOW() will be used by caller (pass current time).
    """
    if entry_time is None:
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    params = {"p_LicensePlate": license_plate, "p_SpotID": spot_id, "p_RateID": rate_id, "p_EntryTime": entry_time}
    call = text("CALL sp_AddNewTicketAndOccupySpot(:p_LicensePlate, :p_SpotID, :p_RateID, :p_EntryTime)")
    with db.engine.begin() as conn:
        conn.execute(call, params)
