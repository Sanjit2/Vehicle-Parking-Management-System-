How to apply and test triggers, functions, and procedures from project.sql

This file explains how to import `project.sql` into your MySQL server and verify the triggers/procedures/functions so the frontend UI (tickets swap/exit) will use them.

Prerequisites

- MySQL server running and accessible
- `mysql` CLI available (in PATH) or use MySQL Workbench / client
- Flask app configured to use the same DB (check `.env` or `app/__init__.py` for DB connection)

1. Fixes already applied

- The repository `project.sql` has been corrected for delimiter typos. It contains a `DROP DATABASE IF EXISTS parking_system; CREATE DATABASE parking_system;` header, so importing will recreate the schema and data.

2. Import `project.sql` into MySQL (PowerShell)
   Run these from the project folder (adjust credentials and host as needed):

```powershell
# Replace user, host, port, and db name as needed. 'parking_system' is the DB created by project.sql.
mysql -u root -p -h 127.0.0.1 -P 3306 < .\project.sql
```

You will be prompted for the MySQL password.

Notes:

- The SQL file drops and recreates the `parking_system` DB, so this is destructive for that DB.
- If import fails on syntax, open `project.sql` and inspect around the reported line in the import error; common issues are MySQL version incompatibilities.

3. Verify routines/triggers exist
   Connect to MySQL and run these queries (or use the mysql CLI):

```sql
-- list triggers
SHOW TRIGGERS FROM parking_system;

-- list stored procedures
SHOW PROCEDURE STATUS WHERE Db = 'parking_system';

-- list functions
SHOW FUNCTION STATUS WHERE Db = 'parking_system';

-- look for specific routines
SELECT ROUTINE_TYPE, ROUTINE_NAME
FROM information_schema.ROUTINES
WHERE ROUTINE_SCHEMA = 'parking_system'
  AND ROUTINE_NAME IN ('fn_GetAvailableSpotsCount','fn_GetDriverTotalSpent','sp_SwapParkingSpots','sp_ProcessVehicleExit');
```

Expected to see:

- Triggers: `trg_OnNewTicket_OccupySpot`, `trg_OnVehicleExit_CalculateFee`, `trg_OnSuccessfulPayment_UpdateTicketStatus`
- Functions: `fn_GetDriverTotalSpent`, `fn_GetAvailableSpotsCount`
- Procedures: `sp_SwapParkingSpots`, `sp_ProcessVehicleExit`

4. Start the Flask app
   Ensure your `.env` matches the DB credentials and start the app:

```powershell
# optional venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

5. Test triggers/procs via the UI
   A) Swap Spot (frontend)

- Open: http://localhost:5000/tickets
- Click "Swap Spot" on a ticket row. A modal should list available spots in that ticket's lot.
- Choose a spot and Confirm Swap.
- Verify the DB (or `spots.html`) shows the new spot occupied and the old spot free.

B) Exit & Pay (frontend)

- From Tickets page click "Exit & Pay" for a ticket.
- Modal will show estimated total. Confirm and process exit.
- Verify:
  - `ParkingTicket.ExitTime` is set
  - `ParkingTicket.TotalFee` is set by the DB trigger
  - A `Payment` row was inserted
  - `ParkingTicket.PaymentStatus` updated to 'Paid' if payments cover fee

6. Test endpoints directly (PowerShell)
   Examples using `Invoke-RestMethod`:

```powershell
# available spots list
Invoke-RestMethod -Uri http://localhost:5000/api/available-spots-list/1 -Method Get

# estimate exit
Invoke-RestMethod -Uri http://localhost:5000/api/estimate-exit/1 -Method Get

# swap spot (JSON body)
$body = @{ ticketId = 3; newSpotNumber = 'ML-A-050' } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/swap-spot -Method Post -Body $body -ContentType 'application/json'

# process exit
$body = @{ ticketId = 3; amountPaid = 120.00; paymentMethod = 'Cash' } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:5000/api/process-exit -Method Post -Body $body -ContentType 'application/json'
```

7. Troubleshooting

- If API calls return error about missing function/procedure, re-import `project.sql` into the same DB the Flask app uses.
- If import errors reference `DELIMITER`, ensure the SQL client supports delimiter statements. The `mysql` CLI does.
- If UI modals don't appear or buttons do nothing, open DevTools Console and check for JS errors; ensure `main.js` loads from `/static/js/main.js`.

8. Optional: re-run just stored routines (no drop)
   If you don't want to drop data, extract and run only the TRIGGER/FUNCTION/PROCEDURE blocks from `project.sql` using the MySQL client (be careful with duplicates).

---

If you want, I can also:

- Patch `project.sql` to make triggers/procedures idempotent (DROP PROCEDURE IF EXISTS / DROP FUNCTION IF EXISTS / DROP TRIGGER IF EXISTS before create) so re-import won't fail.
- Add a small Python or shell script to automate import + verification.

Tell me if you'd like me to make `project.sql` idempotent (I'll add DROP IF EXISTS lines before each object).
