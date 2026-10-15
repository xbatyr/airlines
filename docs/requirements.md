# Midterm requirement checklist

Source: the six-page **Midterm Project (Python fall 2026).pdf** supplied by the
student. This file records assignment requirements; it is not the final report.

| Assignment requirement | Implementation / status |
| --- | --- |
| Console Python application; conditions, loops, functions, input/output | `main.py` and operations in `airline.py` |
| At least two meaningful classes | `Database` and `AirlineSystem` |
| SQLite with at least three related tables | Flights and passengers linked through tickets; foreign keys enabled |
| Add and save records | Add submenu for all three tables |
| Clearly display main records | Aligned flight, passenger, and joined ticket tables |
| Total ticket revenue | Sum of stored active ticket prices |
| Seat occupancy rate | Active tickets / total flight seats × 100 |
| At least two searches; message for no matches | Passenger name/ID, flight destination; `No records found.` |
| Update and delete/cancel; CRUD | All three record types; ticket deletion is cancellation |
| File handling and `results.txt` or `results.csv` | UTF-8 `results.txt` with main records and calculations |
| Appropriate input validation | Required text, integer input, `re` formats, calendar validation, booking and relationship checks |
| At least TWO selected additional features | `re` for validation; `random` for sample data |
| 20 flights, 50 passengers, 40 tickets | `Database.seed()` generates these counts in an empty database; actual database must be submitted |
| Menu repeats until Exit | Main `while` loop, option `0` |
| Team of three | Proposed file ownership in `CONTRIBUTING.md`; actual names/contributions still needed |
| Report PDF, 3–5 pages | Still to prepare: title/team, description, schema, functions/classes, screenshots, results, contributions |
| Mandatory presentation, about 5–7 slides | Still to prepare: objective, schema, functions, results, contributions |
| ZIP containing program, database, export, report, presentation | Still to assemble as `GroupID_AirlineReservation.zip`; include imported Python modules too |
| Submission through TEAMS | Student action, by October 18, 2026, 23:59 |
| Defense October 19–21, 2026 | Every student participates, demonstrates features, and explains code / the two extra features |

## Suggested defense demonstration

1. Show the schema and explain how tickets connect flights and passengers.
2. Display the initial 20/50/40 dataset and both calculations.
3. Add a flight and a passenger, then book a seat for that passenger.
4. Show how an occupied seat and a duplicate booking are rejected.
5. Search by passenger name/ID and by destination; show a search with no matches.
6. Update the passenger and ticket, and explain the stored booking price.
7. Cancel the ticket, then delete the new passenger and flight.
8. Export and open `results.txt`; explain overall and per-flight occupancy.
9. Explain `re`, `random`, both classes, and each teammate's actual contribution.

Do the destructive demonstration on a copy of the database or preserve the
required dataset minimums before preparing the final submission.
