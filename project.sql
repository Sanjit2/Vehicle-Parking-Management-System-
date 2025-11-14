/*
================================================================================
 VEHICLE PARKING MANAGEMENT SYSTEM 
================================================================================
*/

/*
================================================================================
 1. DATABASE CREATION
================================================================================
*/
DROP DATABASE IF EXISTS parking_system;
CREATE DATABASE parking_system;
USE parking_system;

/*
================================================================================
 2. DDL (DATA DEFINITION LANGUAGE) - TABLE CREATION
================================================================================
*/

-- Table 1: Driver
CREATE TABLE Driver (
    DriverID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50),
    PhoneNumber VARCHAR(15) NOT NULL UNIQUE,
    Email VARCHAR(100) UNIQUE,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table 2: ParkingLot
CREATE TABLE ParkingLot (
    LotID INT PRIMARY KEY AUTO_INCREMENT,
    LotName VARCHAR(100) NOT NULL UNIQUE,
    Capacity INT NOT NULL CHECK (Capacity > 0),
    Location VARCHAR(255),
    Levels INT DEFAULT 1
);

-- Table 3: Staff
CREATE TABLE Staff (
    StaffID INT PRIMARY KEY AUTO_INCREMENT,
    FirstName VARCHAR(50) NOT NULL,
    LastName VARCHAR(50),
    Username VARCHAR(50) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role ENUM('Admin', 'Attendant') NOT NULL,
    LotID INT,
    FOREIGN KEY (LotID) REFERENCES ParkingLot(LotID)
        ON DELETE SET NULL
        ON UPDATE CASCADE  
);

-- Table 4: Vehicle
CREATE TABLE Vehicle (
    LicensePlate VARCHAR(15) PRIMARY KEY,
    VehicleType ENUM('Car', 'Bike', 'Truck', 'Handicap') NOT NULL,
    Model VARCHAR(50),
    Colour VARCHAR(30),
    DriverID INT,
    FOREIGN KEY (DriverID) REFERENCES Driver(DriverID)
        ON DELETE SET NULL 
        ON UPDATE CASCADE   
);

-- Table 5: ParkingSpot
CREATE TABLE ParkingSpot (
    SpotID INT PRIMARY KEY AUTO_INCREMENT,
    SpotNumber VARCHAR(10) NOT NULL,
    SpotType ENUM('Compact', 'Standard', 'Large', 'Handicap', 'EV', 'Bike') NOT NULL, 
    IsOccupied BOOLEAN DEFAULT FALSE,
    LotID INT NOT NULL,
    FOREIGN KEY (LotID) REFERENCES ParkingLot(LotID)
        ON DELETE CASCADE  
        ON UPDATE CASCADE,
    UNIQUE(LotID, SpotNumber) 
);

-- Table 6: ParkingRate
CREATE TABLE ParkingRate (
    RateID INT PRIMARY KEY AUTO_INCREMENT,
    RatePerHour DECIMAL(10, 2) NOT NULL CHECK (RatePerHour >= 0),
    VehicleType ENUM('Car', 'Bike', 'Truck', 'Handicap') NOT NULL,
    SpotType ENUM('Compact', 'Standard', 'Large', 'Handicap', 'EV', 'Bike') NOT NULL, 
    GracePerMinute INT DEFAULT 15,
    LotID INT,
    FOREIGN KEY (LotID) REFERENCES ParkingLot(LotID)
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- Table 7: ParkingTicket
CREATE TABLE ParkingTicket (
    TicketID INT PRIMARY KEY AUTO_INCREMENT,
    EntryTime DATETIME NOT NULL,
    ExitTime DATETIME,
    PaymentStatus ENUM('Unpaid', 'Paid', 'Partial') DEFAULT 'Unpaid',
    TotalFee DECIMAL(10, 2),
    LicensePlate VARCHAR(15),
    SpotID INT,
    RateID INT,
    FOREIGN KEY (LicensePlate) REFERENCES Vehicle(LicensePlate)
        ON DELETE SET NULL  
        ON UPDATE CASCADE,
    FOREIGN KEY (SpotID) REFERENCES ParkingSpot(SpotID)
        ON DELETE SET NULL  
        ON UPDATE CASCADE, 
    FOREIGN KEY (RateID) REFERENCES ParkingRate(RateID)
        ON DELETE SET NULL  
        ON UPDATE CASCADE
);

-- Table 8: Payment
CREATE TABLE Payment (
    PaymentID INT PRIMARY KEY AUTO_INCREMENT,
    Amount DECIMAL(10, 2) NOT NULL CHECK (Amount > 0),
    PaymentMethod ENUM('Cash', 'Credit Card', 'UPI', 'AppWallet') NOT NULL,
    TransactionStatus ENUM('Success', 'Failed', 'Pending') DEFAULT 'Success',
    PaymentTimestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    TicketID INT NOT NULL,
    StaffID INT,
    FOREIGN KEY (TicketID) REFERENCES ParkingTicket(TicketID)
        ON DELETE CASCADE  
        ON UPDATE CASCADE,
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);



/*
================================================================================
 3. DML (DATA MANIPULATION LANGUAGE) - POPULATING TABLES (CRUD: Create)
================================================================================
*/

-- 1. Populating Driver
INSERT INTO Driver (FirstName, LastName, PhoneNumber, Email) VALUES
('Aarav', 'Sharma', '9876543210', 'aarav.sharma@example.com'),
('Sanya', 'Gupta', '9123456789', 'sanya.gupta@example.com'),
('Rohan', 'Verma', '8887776665', 'rohan.verma@example.com'),
('Priya', 'Singh', '7776665554', 'priya.singh@example.com'),
('Arjun', 'Patel', '6665554443', 'arjun.patel@example.com');

-- 2. Populating ParkingLot
INSERT INTO ParkingLot (LotName, Capacity, Location, Levels) VALUES
('PESU Basement 1 (Faculty)', 150, 'Main Campus, B-Block', 1),
('PESU Visitor Lot', 50, 'Main Campus, Front Gate', 1),
('EC Campus Open Lot', 300, 'EC Campus, Near Food Court', 1),
('PESU Multi-Level (Students)', 500, 'Main Campus, E-Block', 4),
('PESU Basement 2 (Student)', 250, 'Main Campus, C-Block', 1);

-- 3. Populating Staff
INSERT INTO Staff (FirstName, LastName, Username, PasswordHash, Role, LotID) VALUES
('Vikram', 'Rao', 'vikram_admin', 'hash_admin_pass', 'Admin', 1),
('Meena', 'Iyer', 'meena_attend', 'hash_attend1_pass', 'Attendant', 1),
('Sunil', 'Kumar', 'sunil_attend', 'hash_attend2_pass', 'Attendant', 2),
('Deepa', 'Murthy', 'deepa_admin', 'hash_admin2_pass', 'Admin', 3),
('Raj', 'Gowda', 'raj_attend', 'hash_attend3_pass', 'Attendant', 4);

-- 4. Populating Vehicle
INSERT INTO Vehicle (LicensePlate, VehicleType, Model, Colour, DriverID) VALUES
('KA-01-MJ-1234', 'Car', 'Maruti Swift', 'White', 1),
('KA-05-AB-5678', 'Bike', 'Royal Enfield', 'Black', 2),
('TN-07-CD-9101', 'Car', 'Hyundai i20', 'Red', 3),
('KA-02-EF-1121', 'Car', 'Honda City', 'Silver', 4),
('MH-12-GH-3141', 'Bike', 'Honda Activa', 'Blue', 5);

-- 5. Populating ParkingSpot
INSERT INTO ParkingSpot (SpotNumber, SpotType, IsOccupied, LotID) VALUES
('B1-001', 'Standard', TRUE, 1), -- Occupied
('B1-002', 'Standard', FALSE, 1),
('V-001', 'Handicap', FALSE, 2),
('EC-100', 'Bike', TRUE, 3), -- Occupied
('ML-A-050', 'Compact', FALSE, 4);

-- 6. Populating ParkingRate
INSERT INTO ParkingRate (RatePerHour, VehicleType, SpotType, LotID) VALUES
(50.00, 'Car', 'Standard', 1),   -- 50/hr for Faculty Car
(30.00, 'Bike', 'Standard', 1),   -- 30/hr for Faculty Bike
(100.00, 'Car', 'Standard', 2),   -- 100/hr for Visitor Car
(20.00, 'Car', 'Compact', 4),     -- 20/hr for Student Car
(10.00, 'Bike', 'Bike', 3);        -- 10/hr for Student Bike

-- 7. Populating ParkingTicket
INSERT INTO ParkingTicket (EntryTime, PaymentStatus, LicensePlate, SpotID, RateID) VALUES
('2025-10-24 09:00:00', 'Unpaid', 'KA-01-MJ-1234', 1, 1);

INSERT INTO ParkingTicket (EntryTime, ExitTime, PaymentStatus, TotalFee, LicensePlate, SpotID, RateID) VALUES
('2025-10-23 10:00:00', '2025-10-23 12:00:00', 'Paid', 200.00, 'TN-07-CD-9101', 3, 3);

INSERT INTO ParkingTicket (EntryTime, PaymentStatus, LicensePlate, SpotID, RateID) VALUES
('2025-10-24 10:30:00', 'Unpaid', 'KA-05-AB-5678', 4, 5);

INSERT INTO ParkingTicket (EntryTime, ExitTime, PaymentStatus, TotalFee, LicensePlate, SpotID, RateID) VALUES
('2025-10-23 14:00:00', '2025-10-23 18:00:00', 'Paid', 80.00, 'KA-02-EF-1121', 5, 4);

INSERT INTO ParkingTicket (EntryTime, ExitTime, PaymentStatus, TotalFee, LicensePlate, SpotID, RateID) VALUES
('2025-10-24 08:00:00', '2025-10-24 11:00:00', 'Unpaid', 150.00, 'KA-01-MJ-1234', 2, 1);


-- 8. Populating Payment
INSERT INTO Payment (Amount, PaymentMethod, TransactionStatus, TicketID, StaffID) VALUES
(200.00, 'UPI', 'Success', 2, 2),         -- Payment for Ticket 2, processed by Staff 2
(80.00, 'Credit Card', 'Success', 4, 3),  -- Payment for Ticket 4, processed by Staff 3
(50.00, 'Cash', 'Success', 5, 2),         -- Partial payment for Ticket 5
(100.00, 'UPI', 'Failed', 5, 2),          -- Failed payment for Ticket 5
(100.00, 'AppWallet', 'Success', 5, 2);   -- Successful payment for rest of Ticket 5


/*
================================================================================
 4. DML: UPDATE AND DELETE COMMANDS (CRUD: Update, Delete)
================================================================================
*/

-- Example 1: UPDATE (Simple)
-- Update Driver Priya Singh's phone number.
UPDATE Driver
SET PhoneNumber = '9999999999'
WHERE DriverID = 4;

-- Example 2: UPDATE (To Test `ON UPDATE CASCADE`)
-- Change a vehicle's LicensePlate. The ParkingTicket table should automatically update.
UPDATE Vehicle
SET LicensePlate = 'KA-01-NEW-0001'
WHERE LicensePlate = 'KA-01-MJ-1234';

-- Example 3: DELETE (Commented out to prevent errors during testing)
-- DELETE FROM ParkingLot WHERE LotID = 3;
-- SELECT * FROM ParkingSpot WHERE LotID = 3;  -- (Will be empty)
-- SELECT * FROM Staff WHERE StaffID = 4;      -- (LotID will be NULL)

-- Example 4: DELETE (Commented out to prevent errors during testing)
-- DELETE FROM Driver WHERE DriverID = 2;
-- SELECT LicensePlate, DriverID FROM Vehicle WHERE LicensePlate = 'KA-05-AB-5678'; -- (DriverID will be NULL due to SET NULL)

-- Example 5: DELETE (Commented out to prevent errors during testing)
-- DELETE FROM ParkingTicket WHERE TicketID = 5;
-- SELECT * FROM Payment WHERE TicketID = 5; -- (Will be empty due to CASCADE)



-- -----------------------------------------------------
-- TRIGGERS, FUNCTIONS, AND PROCEDURES
-- -----------------------------------------------------

-- ---------------------------------
-- TRIGGERS (Automatic)
-- ---------------------------------

-- Trigger 1: When a new ticket is created, this automatically marks the spot as occupied.
-- ensure idempotency
DROP TRIGGER IF EXISTS trg_OnNewTicket_OccupySpot;
DELIMITER $$
CREATE TRIGGER trg_OnNewTicket_OccupySpot
AFTER INSERT ON ParkingTicket
FOR EACH ROW
BEGIN
    UPDATE ParkingSpot
    SET IsOccupied = TRUE
    WHERE SpotID = NEW.SpotID;
END$$
DELIMITER ;


-- Trigger 2: BEFORE a ticket is updated with an ExitTime, this automatically calculates the fee and frees the spot.
-- ensure idempotency
DROP TRIGGER IF EXISTS trg_OnVehicleExit_CalculateFee;
DELIMITER $$
CREATE TRIGGER trg_OnVehicleExit_CalculateFee
BEFORE UPDATE ON ParkingTicket
FOR EACH ROW
BEGIN
    DECLARE v_RatePerHour DECIMAL(10, 2);
    DECLARE v_DurationHours DECIMAL(10, 2);

    IF NEW.ExitTime IS NOT NULL AND OLD.ExitTime IS NULL THEN
        -- 1. Get the hourly rate
        SELECT RatePerHour INTO v_RatePerHour
        FROM ParkingRate
        WHERE RateID = NEW.RateID;

        -- 2. Calculate duration in hours
        SET v_DurationHours = TIMESTAMPDIFF(MINUTE, OLD.EntryTime, NEW.ExitTime) / 60.0;

        -- 3. Calculate the fee (rounding up) and set it on the ticket row being updated
        SET NEW.TotalFee = CEILING(v_DurationHours) * v_RatePerHour;

        -- 4. Free up the parking spot
        UPDATE ParkingSpot
        SET IsOccupied = FALSE
        WHERE SpotID = NEW.SpotID;
    END IF;
END$$
DELIMITER ;

-- Trigger 3: After a successful payment, this checks if the ticket is fully paid and updates the status.
-- ensure idempotency
DROP TRIGGER IF EXISTS trg_OnSuccessfulPayment_UpdateTicketStatus;
DELIMITER $$
CREATE TRIGGER trg_OnSuccessfulPayment_UpdateTicketStatus
AFTER INSERT ON Payment
FOR EACH ROW
BEGIN
    DECLARE v_TotalPaid DECIMAL(10, 2);
    DECLARE v_TotalFee DECIMAL(10, 2);

    -- We only care if the payment was successful
    IF NEW.TransactionStatus = 'Success' THEN

        -- 1. Get the ticket's TotalFee that needs to be paid
        SELECT TotalFee INTO v_TotalFee
        FROM ParkingTicket
        WHERE TicketID = NEW.TicketID;

        -- 2. Calculate the SUM of all successful payments for this ticket
        SELECT SUM(Amount) INTO v_TotalPaid
        FROM Payment
        WHERE TicketID = NEW.TicketID AND TransactionStatus = 'Success';

        -- 3. If the total paid now covers the fee, update the ticket status
        IF v_TotalPaid >= v_TotalFee THEN
            UPDATE ParkingTicket
            SET PaymentStatus = 'Paid'
            WHERE TicketID = NEW.TicketID;
        END IF;

    END IF;
END$$
DELIMITER ;


-- ---------------------------------
-- FUNCTIONS (Manual - Used in SELECT)
-- ---------------------------------

-- Function 1: Calculates the total amount of money a specific driver has ever spent.
DELIMITER $$
-- ensure idempotency
DROP FUNCTION IF EXISTS fn_GetDriverTotalSpent;
CREATE FUNCTION fn_GetDriverTotalSpent (p_DriverID INT)
RETURNS DECIMAL(10, 2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_TotalSpent DECIMAL(10, 2);

    -- Sum the TotalFee from all 'Paid' tickets for vehicles owned by the driver
    SELECT SUM(pt.TotalFee) INTO v_TotalSpent
    FROM ParkingTicket pt
    WHERE pt.PaymentStatus = 'Paid'
      AND pt.LicensePlate IN (
            -- Nested query to find all license plates for the given driver
            SELECT v.LicensePlate 
            FROM Vehicle v
            WHERE v.DriverID = p_DriverID
          );

    -- If the driver has spent nothing, return 0.00 instead of NULL
    RETURN IFNULL(v_TotalSpent, 0.00);
END$$
DELIMITER ;


-- Function 2: Returns the number of available (unoccupied) spots in a given parking lot.
DELIMITER $$
-- ensure idempotency
DROP FUNCTION IF EXISTS fn_GetAvailableSpotsCount;
CREATE FUNCTION fn_GetAvailableSpotsCount(p_LotID INT)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_AvailableCount INT;

    SELECT COUNT(*)
    INTO v_AvailableCount
    FROM ParkingSpot
    WHERE LotID = p_LotID AND IsOccupied = FALSE;

    RETURN v_AvailableCount;
END$$
DELIMITER ;


-- ---------------------------------
-- STORED PROCEDURES (Manual - Used with CALL)
-- ---------------------------------

-- Procedure 1: Safely swap a vehicle's parking spot. The transaction ensures all steps succeed or none do.
DELIMITER $$
-- ensure idempotency
DROP PROCEDURE IF EXISTS sp_SwapParkingSpots;
CREATE PROCEDURE sp_SwapParkingSpots(
    IN p_TicketID INT,
    IN p_NewSpotNumber VARCHAR(10)
)
BEGIN
    DECLARE v_OldSpotID INT;
    DECLARE v_NewSpotID INT;
    DECLARE v_LotID INT;
    DECLARE v_IsNewSpotOccupied BOOLEAN;

    -- If any error occurs, automatically roll back the transaction
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Spot swap failed. Transaction rolled back.';
    END;

    -- Find the OLD spot's ID and its LotID from the ticket
    SELECT SpotID, (SELECT LotID FROM ParkingSpot WHERE SpotID = pt.SpotID)
    INTO v_OldSpotID, v_LotID
    FROM ParkingTicket pt
    WHERE TicketID = p_TicketID;
    
    -- Find the NEW spot's ID and check if it's already occupied
    SELECT SpotID, IsOccupied
    INTO v_NewSpotID, v_IsNewSpotOccupied
    FROM ParkingSpot
    WHERE SpotNumber = p_NewSpotNumber AND LotID = v_LotID;

    -- Business Rule: Fail if the target spot is already taken
    IF v_IsNewSpotOccupied = TRUE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot swap. The new spot is already occupied.';
    END IF;

    -- Start the transaction
    START TRANSACTION;

    -- Step 1: Update the ticket to point to the new spot
    UPDATE ParkingTicket SET SpotID = v_NewSpotID WHERE TicketID = p_TicketID;
    -- Step 2: Mark the new spot as occupied
    UPDATE ParkingSpot SET IsOccupied = TRUE WHERE SpotID = v_NewSpotID;
    -- Step 3: Mark the old spot as free
    UPDATE ParkingSpot SET IsOccupied = FALSE WHERE SpotID = v_OldSpotID;

    -- If all steps succeeded, commit the changes
    COMMIT;
END$$
DELIMITER ;


-- Procedure 2: Process a vehicle's complete exit. The transaction ensures the exit and payment are recorded together.
DELIMITER $$
-- ensure idempotency
DROP PROCEDURE IF EXISTS sp_ProcessVehicleExit;
CREATE PROCEDURE sp_ProcessVehicleExit(
    IN p_TicketID INT,
    IN p_AmountPaid DECIMAL(10, 2),
    IN p_PaymentMethod ENUM('Cash', 'Credit Card', 'UPI', 'AppWallet')
)
BEGIN
    -- If any error occurs, automatically roll back the transaction
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vehicle exit process failed. Transaction rolled back.';
    END;

    -- Start the transaction
    START TRANSACTION;

    -- Step 1: Set the vehicle's exit time. This fires 'trg_OnVehicleExit_CalculateFee'
    UPDATE ParkingTicket 
    SET ExitTime = NOW() 
    WHERE TicketID = p_TicketID;

    -- Step 2: Record the payment. This fires 'trg_OnSuccessfulPayment_UpdateTicketStatus'
    INSERT INTO Payment (TicketID, Amount, PaymentMethod) 
    VALUES (p_TicketID, p_AmountPaid, p_PaymentMethod);

    -- If both steps succeeded, commit the changes
    COMMIT;
END$$
DELIMITER ;

