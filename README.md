# Vehicle Parking Management System
A Flask-based parking management application with MySQL database backend, featuring automated business logic through triggers, stored procedures, and functions.

## Team Members
- **T. Lohith Srinivas** - PES2UG23CS???
- **Sanjit Dev Maheswaran** - PES2UG23CS531
- **Shreyas Kodithyala** - PES2UG23CS563

**Course:** UE23CS351A - DBMS Project  
**Institution:** PES University, Electronic City Campus  
**Semester:** AUG - DEC 2025  
**Guided by:** Prof. Shilpa S

## Features

### Parking Management
- **Real-time Spot Tracking**: Automatic spot occupancy updates via triggers
- **Fee Calculation**: Automated fee calculation based on parking duration and vehicle type
- **Spot Swapping**: Change parking spots with transaction integrity using stored procedures
- **Payment Processing**: Multiple payment methods (Cash, Credit Card, UPI, AppWallet)
- **Partial Payments**: Support for split payments with automatic status updates

### Database Features
- **8 Normalized Tables**: Driver, Vehicle, ParkingLot, ParkingSpot, Staff, ParkingRate, ParkingTicket, Payment
- **3 Automated Triggers**: 
  - Spot occupancy on ticket creation
  - Fee calculation and spot release on exit
  - Payment status updates
- **2 Custom Functions**: 
  - `fn_GetDriverTotalSpent(DriverID)` - Calculate total driver spending
  - `fn_GetAvailableSpotsCount(LotID)` - Count available spots
- **2 Stored Procedures**: 
  - `sp_SwapParkingSpots` - Transaction-safe spot swapping
  - `sp_ProcessVehicleExit` - Complete exit processing with payment

### User Features
- **Staff Dashboard**: Real-time occupancy reports and revenue tracking
- **Driver Management**: Register drivers and vehicles with validation
- **Rate Configuration**: Flexible pricing by vehicle type, spot type, and lot
- **Payment History**: Complete transaction logs with success/failure tracking
- **CRUD Operations**: Full create, read, update, delete for all entities

## Setup

### 1. Create and activate a virtual environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows CMD:**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure database connection

Update the database credentials in `.env` file or set environment variables:

**PowerShell:**
```powershell
$env:DB_HOST='localhost'
$env:DB_USER='root'
$env:DB_PASSWORD='your_password'
$env:DB_NAME='parking_system'
$env:DB_PORT='3306'
```

**Linux/Mac:**
```bash
export DB_HOST='localhost'
export DB_USER='root'
export DB_PASSWORD='your_password'
export DB_NAME='parking_system'
export DB_PORT='3306'
```

### 4. Set up the database

Make sure your MySQL database is running and execute the SQL scripts:

```bash
mysql -u root -p < project.sql
```

This creates the `parking_system` database with all tables, sample data, triggers, functions, and stored procedures.

### 5. Run the Flask application

**Option 1: Direct run**
```bash
python run.py
```

**Option 2: With virtual environment**
```powershell
.\.venv\Scripts\Activate.ps1
python run.py
```

### 6. Access the application

Open your browser at: **http://localhost:5000**

## Database Schema

**8 Tables:** Driver, Vehicle, ParkingLot, ParkingSpot, Staff, ParkingRate, ParkingTicket, Payment

**Key Relationships:**
- Driver → Vehicle (1:N)
- ParkingLot → ParkingSpot, Staff, ParkingRate (1:N)
- Vehicle, ParkingSpot, ParkingRate → ParkingTicket (1:N)
- ParkingTicket → Payment (1:N)

## Testing Database Features

**Test Triggers:**
```sql
-- Test automatic spot occupancy
INSERT INTO ParkingTicket (EntryTime, LicensePlate, SpotID, RateID) 
VALUES (NOW(), 'KA-01-MJ-1234', 2, 1);

-- Test fee calculation
UPDATE ParkingTicket SET ExitTime = NOW() WHERE TicketID = 1;
```

**Test Functions:**
```sql
-- Get driver total spending
SELECT fn_GetDriverTotalSpent(1);

-- Get available spots
SELECT fn_GetAvailableSpotsCount(1);
```

**Test Stored Procedures:**
```sql
-- Swap parking spots
CALL sp_SwapParkingSpots(1, 'ML-A-050');

-- Process vehicle exit
CALL sp_ProcessVehicleExit(1, 150.00, 'UPI');
```

## Notes

- The Flask app uses Jinja2 templates from the `app/templates/` directory
- Database connection uses mysql-connector-python
- All triggers, functions, and procedures are initialized from `init_db.sql`
- The application features transaction-safe operations with automatic rollback on errors
- Payment status automatically updates when payments cover the total fee

## Project Structure
```
PROJECT/
├── app/
│   ├── __init__.py           # Flask initialization
│   ├── routes.py             # API endpoints
│   ├── models.py             # Database models
│   ├── db_helpers.py         # Database utilities
│   ├── static/               # CSS and JavaScript
│   └── templates/            # HTML templates
├── init_db.sql               # Triggers and procedures
├── project.sql               # Complete database schema
├── requirements.txt          # Python dependencies
├── run.py                    # Application entry point
└── .env                      # Database configuration
```

## Acknowledgments

**Guided by:** Prof. Shilpa S, Assistant Professor, Department of CSE, PES University

**Institution:** PES University, Electronic City Campus  
**Course:** UE23CS351A - DBMS Project  
**Semester:** AUG - DEC 2025
