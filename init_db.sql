-- init_db.sql
-- Contains triggers, functions and stored procedures for Parking System
-- Idempotent where possible (DROP IF EXISTS used)

-- Note: statements are separated by a sentinel comment line
-- so the Python initializer can split and execute each block safely.

-- STATEMENT_BOUNDARY
DROP TRIGGER IF EXISTS trg_after_ticket_insert;
-- STATEMENT_BOUNDARY
CREATE TRIGGER trg_after_ticket_insert
AFTER INSERT ON ParkingTicket
FOR EACH ROW
BEGIN
    IF NEW.SpotID IS NOT NULL THEN
        UPDATE ParkingSpot
        SET IsOccupied = TRUE
        WHERE SpotID = NEW.SpotID;
    END IF;
END;

-- STATEMENT_BOUNDARY
DROP TRIGGER IF EXISTS trg_before_ticket_exit;
-- STATEMENT_BOUNDARY
CREATE TRIGGER trg_before_ticket_exit
BEFORE UPDATE ON ParkingTicket
FOR EACH ROW
BEGIN
    DECLARE v_RatePerHour DECIMAL(10,2);
    DECLARE v_DurationHours DECIMAL(10,2);
    IF NEW.ExitTime IS NOT NULL AND OLD.ExitTime IS NULL THEN
        SELECT RatePerHour INTO v_RatePerHour FROM ParkingRate WHERE RateID = NEW.RateID;
        SET v_DurationHours = TIMESTAMPDIFF(MINUTE, OLD.EntryTime, NEW.ExitTime) / 60.0;
        SET NEW.TotalFee = CEILING(v_DurationHours) * v_RatePerHour;
        IF NEW.SpotID IS NOT NULL THEN
            UPDATE ParkingSpot SET IsOccupied = FALSE WHERE SpotID = NEW.SpotID;
        END IF;
    END IF;
END;

-- STATEMENT_BOUNDARY
DROP TRIGGER IF EXISTS trg_after_payment_success;
-- STATEMENT_BOUNDARY
CREATE TRIGGER trg_after_payment_success
AFTER INSERT ON Payment
FOR EACH ROW
BEGIN
    DECLARE v_TotalPaid DECIMAL(10,2);
    DECLARE v_TotalFee DECIMAL(10,2);
    IF NEW.TransactionStatus = 'Success' THEN
        SELECT TotalFee INTO v_TotalFee FROM ParkingTicket WHERE TicketID = NEW.TicketID;
        SELECT IFNULL(SUM(Amount),0) INTO v_TotalPaid FROM Payment WHERE TicketID = NEW.TicketID AND TransactionStatus = 'Success';
        IF v_TotalFee IS NOT NULL AND v_TotalPaid >= v_TotalFee THEN
            UPDATE ParkingTicket SET PaymentStatus = 'Paid' WHERE TicketID = NEW.TicketID;
        ELSEIF v_TotalPaid > 0 AND (v_TotalFee IS NOT NULL AND v_TotalPaid < v_TotalFee) THEN
            UPDATE ParkingTicket SET PaymentStatus = 'Partial' WHERE TicketID = NEW.TicketID;
        END IF;
    END IF;
END;

-- STATEMENT_BOUNDARY
DROP TRIGGER IF EXISTS trg_after_ticket_delete;
-- STATEMENT_BOUNDARY
CREATE TRIGGER trg_after_ticket_delete
AFTER DELETE ON ParkingTicket
FOR EACH ROW
BEGIN
    IF OLD.SpotID IS NOT NULL THEN
        UPDATE ParkingSpot SET IsOccupied = FALSE WHERE SpotID = OLD.SpotID;
    END IF;
END;

-- STATEMENT_BOUNDARY
DROP FUNCTION IF EXISTS fn_GetDriverTotalSpent;
-- STATEMENT_BOUNDARY
CREATE FUNCTION fn_GetDriverTotalSpent(p_DriverID INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_TotalSpent DECIMAL(10,2);
    SELECT IFNULL(SUM(pt.TotalFee),0) INTO v_TotalSpent
    FROM ParkingTicket pt
    WHERE pt.PaymentStatus = 'Paid'
      AND pt.LicensePlate IN (SELECT v.LicensePlate FROM Vehicle v WHERE v.DriverID = p_DriverID);
    RETURN v_TotalSpent;
END;

-- STATEMENT_BOUNDARY
DROP FUNCTION IF EXISTS fn_GetAvailableSpotsCount;
-- STATEMENT_BOUNDARY
CREATE FUNCTION fn_GetAvailableSpotsCount(p_LotID INT)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_AvailableCount INT;
    SELECT COUNT(*) INTO v_AvailableCount FROM ParkingSpot WHERE LotID = p_LotID AND IsOccupied = FALSE;
    RETURN v_AvailableCount;
END;

-- STATEMENT_BOUNDARY
DROP PROCEDURE IF EXISTS sp_CreateNewParkingLotWithDefaultRates;
-- STATEMENT_BOUNDARY
CREATE PROCEDURE sp_CreateNewParkingLotWithDefaultRates(
    IN p_LotName VARCHAR(100),
    IN p_Capacity INT,
    IN p_Location VARCHAR(255),
    IN p_Levels INT
)
BEGIN
    DECLARE v_LotID INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Failed to create lot with default rates';
    END;

    START TRANSACTION;
    INSERT INTO ParkingLot (LotName, Capacity, Location, Levels) VALUES (p_LotName, p_Capacity, p_Location, p_Levels);
    SET v_LotID = LAST_INSERT_ID();

    -- Insert some default rates (example defaults - adjust as needed)
    INSERT INTO ParkingRate (RatePerHour, VehicleType, SpotType, LotID) VALUES
        (50.00, 'Car', 'Standard', v_LotID),
        (30.00, 'Bike', 'Standard', v_LotID),
        (20.00, 'Car', 'Compact', v_LotID);

    COMMIT;
END;

-- STATEMENT_BOUNDARY
DROP PROCEDURE IF EXISTS sp_AddNewTicketAndOccupySpot;
-- STATEMENT_BOUNDARY
CREATE PROCEDURE sp_AddNewTicketAndOccupySpot(
    IN p_LicensePlate VARCHAR(15),
    IN p_SpotID INT,
    IN p_RateID INT,
    IN p_EntryTime DATETIME
)
BEGIN
    DECLARE v_ticket INT;
    DECLARE v_existing INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Failed to create ticket and occupy spot';
    END;

    START TRANSACTION;
    -- Optional: ensure spot is not already occupied
    SELECT COUNT(*) INTO v_existing FROM ParkingSpot WHERE SpotID = p_SpotID AND IsOccupied = TRUE;
    IF v_existing > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Target spot is already occupied';
    END IF;

    INSERT INTO ParkingTicket (EntryTime, PaymentStatus, LicensePlate, SpotID, RateID)
    VALUES (p_EntryTime, 'Unpaid', p_LicensePlate, p_SpotID, p_RateID);

    SET v_ticket = LAST_INSERT_ID();

    UPDATE ParkingSpot SET IsOccupied = TRUE WHERE SpotID = p_SpotID;

    COMMIT;
END;

-- STATEMENT_BOUNDARY
-- End of file
