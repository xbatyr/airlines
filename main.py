import sqlite3  # does import database error types for readable error messages
from airline import AirlineSystem  # does import the reservation operations
from database import Database  # does import the database manager


def read_text(prompt):  # does ask for a required text value
    while True:  # does repeat until the user enters non-empty text
        value = input(prompt).strip()  # does read the input and remove surrounding spaces
        if value:  # does check that the user entered some text
            return value  # does return the entered text
        print("This field cannot be empty.")  # does explain why the input must be repeated


def read_number(prompt):  # does ask for a positive whole number
    while True:  # does repeat until the user enters a valid number
        try:  # does attempt to convert the entered text to an integer
            value = int(input(prompt))  # does read and convert the user's input
            if value > 0:  # does accept only positive numbers
                return value  # does return the validated number
        except ValueError:  # does handle text that cannot be converted to an integer
            pass  # does continue to the shared validation message
        print("Enter a positive whole number.")  # does explain which input is accepted


def choose_record():  # does display the three supported record types
    print("1. Flight\n2. Passenger\n3. Ticket\n0. Back")  # does show the record submenu
    return input("Choose a record type: ").strip()  # does return the selected submenu option


def flight_input():  # does ask for all editable flight fields
    number = read_text("Flight number (KC123): ")  # does read the flight number
    origin = read_text("Origin: ")  # does read the departure city
    destination = read_text("Destination: ")  # does read the arrival city
    departure = read_text("Departure (YYYY-MM-DD HH:MM): ")  # does read the departure date and time
    seats = read_number("Total seats: ")  # does read the flight capacity
    price = read_number("Ticket price (whole KZT): ")  # does read the price in whole KZT
    return number, origin, destination, departure, seats, price  # does return the fields in the order used by the system


def passenger_input():  # does ask for the editable passenger fields
    name = read_text("Passenger name: ")  # does read the passenger name
    email = read_text("Email: ")  # does read the passenger email address
    return name, email  # does return both passenger fields


def ticket_input():  # does ask for the booking details
    flight_id = read_number("Flight ID: ")  # does read the selected flight ID
    passenger_id = read_number("Passenger ID: ")  # does read the selected passenger ID
    seat = read_number("Seat number: ")  # does read the selected seat number
    return flight_id, passenger_id, seat  # does return the booking fields


def display_records(rows):  # does print database records in a readable table
    if not rows:  # does check whether the result is empty
        print("No records found.")  # does display the required message for an empty result
        return  # does finish without trying to print missing columns
    columns = list(rows[0].keys())  # does read the column names from the first record
    widths = [max(len(column), max(len(str(row[column])) for row in rows)) for column in columns]  # does calculate enough width for each heading and value
    print(" | ".join(column.upper().ljust(width) for column, width in zip(columns, widths)))  # does print aligned column headings
    print("-+-".join("-" * width for width in widths))  # does print a line below the headings
    for row in rows:  # does visit every record in the result
        print(" | ".join(str(row[column]).ljust(width) for column, width in zip(columns, widths)))  # does print one aligned record


def add_information(system):  # does handle the add submenu
    choice = choose_record()  # does ask which kind of record to add
    if choice == "1":  # does select flight creation
        record_id = system.add_flight(*flight_input())  # does collect flight fields and save the flight
    elif choice == "2":  # does select passenger creation
        record_id = system.add_passenger(*passenger_input())  # does collect passenger fields and save the passenger
    elif choice == "3":  # does select ticket booking
        display_records(system.list_flights())  # does show flight IDs and booked seat counts
        display_records(system.list_passengers())  # does show passenger IDs before booking
        record_id = system.add_ticket(*ticket_input())  # does collect booking fields and save the ticket
    else:  # does handle returning to the menu or an unknown option
        if choice != "0":  # does detect an unknown option
            print("Invalid option.")  # does describe the invalid submenu choice
        return  # does return to the main menu
    print(f"Record saved. ID: {record_id}")  # does confirm creation and display the new ID


def show_information(system):  # does handle the display submenu
    choice = choose_record()  # does ask which kind of record to display
    if choice == "1":  # does select flights
        display_records(system.list_flights())  # does display the flight table
    elif choice == "2":  # does select passengers
        display_records(system.list_passengers())  # does display the passenger table
    elif choice == "3":  # does select tickets
        display_records(system.list_tickets())  # does display tickets with their related names
    elif choice != "0":  # does detect an option other than the supported choices or Back
        print("Invalid option.")  # does describe the invalid submenu choice


def search_information(system):  # does handle the two required search options
    print("1. Passenger by name or ID\n2. Flights by destination\n0. Back")  # does show the search submenu
    choice = input("Choose a search: ").strip()  # does read the search option
    if choice == "1":  # does select passenger search
        display_records(system.search_passengers(read_text("Passenger name or ID: ")))  # does display matching passengers or the empty-result message
    elif choice == "2":  # does select flight search
        display_records(system.search_flights(read_text("Destination: ")))  # does display matching flights or the empty-result message
    elif choice != "0":  # does detect an invalid search option
        print("Invalid option.")  # does explain the invalid choice


def update_information(system):  # does handle updates for all three record types
    choice = choose_record()  # does ask which kind of record to update
    tables = {"1": "flights", "2": "passengers", "3": "tickets"}  # does connect submenu choices to the known tables
    if choice not in tables:  # does check for Back or an unknown choice
        if choice != "0":  # does detect an unknown choice
            print("Invalid option.")  # does explain the invalid choice
        return  # does return to the main menu
    record_id = read_number("Record ID to update: ")  # does read the record ID
    display_records([system.get_record(tables[choice], record_id)])  # does display the current record before collecting replacement values
    print("Enter all replacement fields.")  # does explain that the full record details must be entered
    if choice == "1":  # does select a flight update
        system.update_flight(record_id, *flight_input())  # does collect and save the replacement flight fields
    elif choice == "2":  # does select a passenger update
        system.update_passenger(record_id, *passenger_input())  # does collect and save the replacement passenger fields
    else:  # does select a ticket update
        system.update_ticket(record_id, *ticket_input())  # does collect and save the replacement booking fields
    print("Record updated.")  # does confirm that the changes were saved


def delete_information(system):  # does handle record deletion and ticket cancellation
    choice = choose_record()  # does ask which kind of record to delete
    tables = {"1": "flights", "2": "passengers", "3": "tickets"}  # does connect submenu choices to the known tables
    if choice not in tables:  # does check for Back or an unknown choice
        if choice != "0":  # does detect an unknown choice
            print("Invalid option.")  # does explain the invalid choice
        return  # does return to the main menu
    record_id = read_number("Record ID to delete or cancel: ")  # does read the selected record ID
    display_records([system.get_record(tables[choice], record_id)])  # does display the exact record being deleted
    if input("Type yes to confirm: ").strip().lower() == "yes":  # does require confirmation inside the program before deleting a record
        system.delete_record(tables[choice], record_id)  # does delete the record after checking related bookings
        print("Record deleted or ticket cancelled.")  # does confirm the successful operation
    else:  # does handle a decision to keep the record
        print("Deletion cancelled.")  # does confirm that the record was kept


def main():  # does start the application and run the console menu
    database = Database()  # does open the project's SQLite database
    try:  # does keep the database cleanup active while the program runs
        if database.seed():  # does create sample data only when all three tables are empty
            print("Sample data created: 20 flights, 50 passengers, 40 tickets.")  # does report the generated dataset
        system = AirlineSystem(database)  # does create the reservation system using the opened database
        while True:  # does keep the menu running until the user chooses Exit
            print("\nAIRLINE RESERVATION SYSTEM\n1. Add information\n2. Display records\n3. Search\n4. Update\n5. Delete or cancel\n6. Show statistics\n7. Export results\n0. Exit")  # does display all required main operations
            choice = input("Choose an option: ").strip()  # does read the main menu option
            try:  # does handle invalid input and failed operations without ending the menu
                if choice == "1":  # does select the add operation
                    add_information(system)  # does open the add submenu
                elif choice == "2":  # does select the display operation
                    show_information(system)  # does open the display submenu
                elif choice == "3":  # does select the search operation
                    search_information(system)  # does open the search submenu
                elif choice == "4":  # does select the update operation
                    update_information(system)  # does open the update submenu
                elif choice == "5":  # does select deletion or cancellation
                    delete_information(system)  # does open the delete submenu
                elif choice == "6":  # does select the required statistics
                    print("\n".join(system.summary_lines()))  # does display revenue, occupancy, and record counts
                elif choice == "7":  # does select the text report export
                    print(f"Report saved: {system.export_results()}")  # does save the report and display its location
                elif choice == "0":  # does select Exit
                    print("Goodbye!")  # does display the exit message
                    break  # does stop the main menu loop
                else:  # does handle an unsupported menu choice
                    print("Invalid option.")  # does ask the user to choose a valid menu option
            except ValueError as error:  # does catch validation and missing-record errors
                print(f"Error: {error}")  # does display the specific validation message
            except sqlite3.IntegrityError:  # does catch database uniqueness and relationship errors
                print("Error: duplicate flight number, email, or booking, or an invalid database relationship.")  # does explain why the database rejected the change
            except (OSError, sqlite3.OperationalError) as error:  # does catch file export and database access failures
                print(f"Cannot complete the operation: {error}")  # does display the file or database problem
    except (KeyboardInterrupt, EOFError):  # does handle Ctrl+C or a closed input stream
        print("\nProgram closed.")  # does display a clean shutdown message
    finally:  # does run cleanup after normal exit or an error
        database.close()  # does close the database connection


if __name__ == "__main__":  # does run the menu only when this file is started directly
    main()  # does launch the console application
