import argparse
import sqlite3
from pathlib import Path

from airline import AirlineSystem
from database import Database


def read_text(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def read_number(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
        except ValueError:
            pass
        print("Enter a positive whole number.")


def choose_record():
    print("1. Flight\n2. Passenger\n3. Ticket\n0. Back")
    return input("Choose a record type: ").strip()


def flight_input():
    number = read_text("Flight number (KC123): ")
    origin = read_text("Origin: ")
    destination = read_text("Destination: ")
    departure = read_text("Departure (YYYY-MM-DD HH:MM): ")
    seats = read_number("Total seats: ")
    price = read_number("Ticket price (whole KZT): ")
    return number, origin, destination, departure, seats, price


def passenger_input():
    name = read_text("Passenger name: ")
    email = read_text("Email: ")
    return name, email


def ticket_input(system):
    flight_id = read_number("Flight ID: ")
    flight = system.get_record("flights", flight_id)
    booked = system.booked_seats(flight_id)
    print(f"Seat range: 1-{flight['seats']}")
    print("Booked seats: " + (", ".join(map(str, booked)) if booked else "none"))
    passenger_id = read_number("Passenger ID: ")
    seat = read_number("Seat number: ")
    return flight_id, passenger_id, seat


def display_records(rows):
    if not rows:
        print("No records found.")
        return
    columns = list(rows[0].keys())
    widths = [
        max(len(column), max(len(str(row[column])) for row in rows))
        for column in columns
    ]
    print(
        " | ".join(
            column.upper().ljust(width) for column, width in zip(columns, widths)
        )
    )
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(
            " | ".join(
                str(row[column]).ljust(width) for column, width in zip(columns, widths)
            )
        )


def add_information(system):
    choice = choose_record()
    if choice == "1":
        record_id = system.add_flight(*flight_input())
    elif choice == "2":
        record_id = system.add_passenger(*passenger_input())
    elif choice == "3":
        display_records(system.list_flights())
        display_records(system.list_passengers())
        record_id = system.add_ticket(*ticket_input(system))
    else:
        if choice != "0":
            print("Invalid option.")
        return
    print(f"Record saved. ID: {record_id}")


def show_information(system):
    choice = choose_record()
    if choice == "1":
        display_records(system.list_flights())
    elif choice == "2":
        display_records(system.list_passengers())
    elif choice == "3":
        display_records(system.list_tickets())
    elif choice != "0":
        print("Invalid option.")


def search_information(system):
    print("1. Passenger by name or ID\n2. Flights by destination\n0. Back")
    choice = input("Choose a search: ").strip()
    if choice == "1":
        display_records(system.search_passengers(read_text("Passenger name or ID: ")))
    elif choice == "2":
        display_records(system.search_flights(read_text("Destination: ")))
    elif choice != "0":
        print("Invalid option.")


def update_information(system):
    choice = choose_record()
    tables = {"1": "flights", "2": "passengers", "3": "tickets"}
    if choice not in tables:
        if choice != "0":
            print("Invalid option.")
        return
    record_id = read_number("Record ID to update: ")
    display_records([system.get_record(tables[choice], record_id)])
    print("Enter all replacement fields.")
    if choice == "1":
        system.update_flight(record_id, *flight_input())
    elif choice == "2":
        system.update_passenger(record_id, *passenger_input())
    else:
        system.update_ticket(record_id, *ticket_input(system))
    print("Record updated.")


def delete_information(system):
    choice = choose_record()
    tables = {"1": "flights", "2": "passengers", "3": "tickets"}
    if choice not in tables:
        if choice != "0":
            print("Invalid option.")
        return
    record_id = read_number("Record ID to delete or cancel: ")
    display_records([system.get_record(tables[choice], record_id)])
    if input("Type yes to confirm: ").strip().lower() == "yes":
        system.delete_record(tables[choice], record_id)
        print("Record deleted or ticket cancelled.")
    else:
        print("Deletion cancelled.")


def main(database_path=None, report_path=None):
    try:
        database = Database(database_path)
    except (OSError, sqlite3.Error) as error:
        print(f"Cannot open the database: {error}")
        return 1
    if report_path is None and database_path is not None:
        report_path = Path(database_path).with_suffix(".results.txt")
    try:
        if database.seed():
            print("Sample data created: 20 flights, 50 passengers, 40 tickets.")
        system = AirlineSystem(database)
        while True:
            print(
                "\nAIRLINE RESERVATION SYSTEM\n"
                "1. Add information\n2. Display records\n3. Search\n"
                "4. Update\n5. Delete or cancel\n6. Show statistics\n"
                "7. Export results\n0. Exit"
            )
            choice = input("Choose an option: ").strip()
            try:
                if choice == "1":
                    add_information(system)
                elif choice == "2":
                    show_information(system)
                elif choice == "3":
                    search_information(system)
                elif choice == "4":
                    update_information(system)
                elif choice == "5":
                    delete_information(system)
                elif choice == "6":
                    print("\n".join(system.summary_lines()))
                elif choice == "7":
                    print(f"Report saved: {system.export_results(report_path)}")
                elif choice == "0":
                    print("Goodbye!")
                    break
                else:
                    print("Invalid option.")
            except ValueError as error:
                print(f"Error: {error}")
            except sqlite3.IntegrityError:
                print(
                    "Error: duplicate flight number, email, or booking, or an invalid database relationship."
                )
            except (OSError, sqlite3.Error) as error:
                print(f"Cannot complete the operation: {error}")
    except (OSError, sqlite3.Error) as error:
        print(f"Cannot load the database: {error}")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nProgram closed.")
    finally:
        database.close()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Airline reservation console app")
    parser.add_argument("--database", type=Path, help="use a separate SQLite database")
    parser.add_argument("--report", type=Path, help="save the text report to this path")
    args = parser.parse_args()
    raise SystemExit(main(args.database, args.report))
