# Airline Reservation System

A simple console-based Python midterm project for a team of three students.
It manages flights, passengers, and tickets in SQLite. The interface and Python
comments are in English. Every non-empty Python code line has a lowercase
English comment starting with `# does`.

## Run

Install Python 3.10 or newer. No external packages are required.

```bash
python3 main.py
```

On Windows, use `python main.py` if that is your Python command.
On the first run, an empty database receives **20 flights, 50 passengers, and
40 tickets**. Data remains saved after exiting. Sample passengers are fictional;
sample flights and prices do not represent real airline schedules or fares.

The database and export are always placed beside the source files, even if you
start the program from a different folder. To save the report, choose **7**.

## Files and classes

| File | Responsibility |
| --- | --- |
| `main.py` | Input helpers, readable tables, CRUD submenus, and the main loop |
| `database.py` | `Database`: connection, schema, safe SQL execution, sample data |
| `airline.py` | `AirlineSystem`: validation, reservation rules, CRUD, searches, calculations, export |
| `tests/test_airline.py` | Tests using separate temporary databases |
| `CONTRIBUTING.md` | Suggested team responsibilities and Git workflow |
| `docs/requirements.md` | PDF requirements mapped to the implementation and remaining submission work |
| `.github/workflows/tests.yml` | Automated checks on pushes and pull requests |
| `project.db` | Generated local database, required in the final submission |
| `results.txt` | Generated report, required in the final submission |

`project.db` and `results.txt` are ignored by Git to avoid conflicts between
teammates' local data. Each clone can generate the same starting dataset from
`Database.seed()`. **Include the actual database and report in the final ZIP**;
the generator alone does not satisfy the dataset submission requirement.

## Menu

```text
1. Add information
2. Display records
3. Search
4. Update
5. Delete or cancel
6. Show statistics
7. Export results
0. Exit
```

Add, display, update, and delete support all three record types. For updates,
the current record is shown and all replacement fields must be entered.
Search supports a passenger name/ID and a flight destination. An unsuccessful
search displays `No records found.`

## Database structure

| Table | Columns |
| --- | --- |
| `flights` | `id`, unique `number`, `origin`, `destination`, `departure`, `seats`, `price` |
| `passengers` | `id`, `name`, unique `email` |
| `tickets` | `id`, `flight_id`, `passenger_id`, `seat`, `price` |

`tickets.flight_id` references `flights.id`. `tickets.passenger_id` references
`passengers.id`. One flight has many tickets, and one passenger can have tickets
for different flights. SQLite foreign-key enforcement is enabled.

## Simple booking rules

- Flight numbers use two letters and three or four digits, such as `KC123`.
- Departure uses a valid calendar date and time: `YYYY-MM-DD HH:MM`.
- Names and cities cannot be blank; origin and destination must differ.
- Email addresses pass a simple regular-expression format check.
- IDs, capacities, seat numbers, and prices are positive whole numbers.
- Prices are in **whole KZT** to keep money calculations simple and exact.
- Seat numbers run from `1` to the flight's capacity.
- A seat can have only one active ticket, and a passenger can have only one
  active ticket for a particular flight.
- A flight's capacity cannot be reduced below its highest booked seat number.
- Cancel linked tickets before deleting their flight or passenger.
- Updating a flight price keeps previously booked ticket prices unchanged.
- Updating a ticket on the same flight keeps its original price. Moving it to
  another flight uses that flight's current price.
- Ticket cancellation deletes the ticket and releases its seat. Cancelled-ticket
  history is not stored in this simple project.

## Required calculations and extra features

**Total ticket revenue** = sum of prices of active tickets in the database.
Cancellation removes the ticket price from this total; this is a current active
booking total, not a payment or refund accounting system.

**Seat occupancy rate** = active ticket count / total flight capacity × 100.
An empty database has 0% occupancy. The report also includes occupancy per flight.

The two selected additional features are:

1. **`re`**: flight number, email, and departure-format validation.
2. **`random`**: meaningful sample capacities, prices, and passenger selection.
   A local generator with seed `26` makes the starting dataset repeatable.

`results.txt` includes the project title, all flights, passengers, and tickets,
record counts, revenue, and overall/per-flight occupancy.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests cover persistence, dataset counts, booking conflicts, cancellation,
updates, foreign keys, searches, export, invalid input, and empty statistics.
They do not modify `project.db`.

## GitHub and team setup

This folder is prepared as a local Git repository. A remote GitHub repository
has not been created or connected.

1. Create an empty repository in your GitHub account.
2. Commit the project files and connect the repository using its actual URL:

   ```bash
   git add .
   git commit -m "Add airline reservation project"
   git remote add origin https://github.com/YOUR_USERNAME/airline-reservation-system.git
   git push -u origin main
   ```

3. Invite the other two students as collaborators in the repository settings.
4. Each teammate clones the repository and runs `python3 main.py`.
5. Work in separate branches and merge reviewed pull requests. See
   [CONTRIBUTING.md](CONTRIBUTING.md) for the commands and suggested split.

Do not commit credentials or real passenger details. No online service,
GitHub token, or API key is needed to run the application.

## Final submission: still to prepare

The PDF requires submission by **October 18, 2026, 23:59**, with defense on
**October 19–21, 2026** during regular class hours.

Before creating the final ZIP:

1. Check that the submitted `project.db` still contains at least 20 flights,
   50 passengers, and 40 tickets. Deleting demo data can put it below the minimum.
2. Use menu option **7** to refresh `results.txt` from the final database.
3. Prepare `ProjectReport.pdf` (3–5 pages) with team names, description, schema,
   functions/classes, real program screenshots, results, and contributions.
4. Prepare `ProjectPresentation.pptx` (about 5–7 slides) for the defense.
5. Include `main.py`, `database.py`, `airline.py`, `project.db`, `results.txt`,
   `ProjectReport.pdf`, and `ProjectPresentation.pptx` in
   `GroupID_AirlineReservation.zip`, replacing `GroupID` with your actual group ID.
6. Submit the ZIP through the TEAMS Assignment.

The additional Python modules must be included because `main.py` imports them.
The report, presentation, and final ZIP are outside this code-first stage.
