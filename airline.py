import re  # does import regular expressions for validating user input
from datetime import datetime  # does import tools for checking departure dates
from pathlib import Path  # does import tools for choosing an export path


class AirlineSystem:  # does provide reservation rules and the main project operations
    def __init__(self, database):  # does receive an existing database object
        self.database = database  # does keep the database available to the system methods

    def positive_integer(self, value, label):  # does check IDs, seats, and whole-number prices
        if type(value) is not int or value <= 0:  # does reject non-integers and non-positive numbers
            raise ValueError(f"{label} must be a positive whole number.")  # does describe the invalid number
        return value  # does return the validated number

    def required_text(self, value, label):  # does validate a required text field
        value = value.strip()  # does remove spaces from the beginning and end
        if not value:  # does detect an empty field
            raise ValueError(f"{label} cannot be empty.")  # does explain why the text is invalid
        return value  # does return the cleaned text

    def get_record(self, table, record_id):  # does find one existing flight, passenger, or ticket
        if table not in ("flights", "passengers", "tickets"):  # does allow only the three known table names
            raise ValueError("Unknown record type.")  # does reject an unsupported table name
        self.positive_integer(record_id, "ID")  # does validate the requested record ID
        rows = self.database.fetch(f"SELECT * FROM {table} WHERE id = ?", (record_id,))  # does search the selected table using a safe value parameter
        if not rows:  # does check whether the record exists
            raise ValueError("Record not found.")  # does explain that the requested ID does not exist
        return rows[0]  # does return the matching record

    def flight_values(self, number, origin, destination, departure, seats, price):  # does validate the editable flight fields
        number = number.strip().upper()  # does standardize the flight number
        if not re.fullmatch(r"[A-Z]{2}\d{3,4}", number):  # does require two letters followed by three or four digits
            raise ValueError("Flight number must look like KC123 or KC1234.")  # does explain the accepted flight number format
        origin = self.required_text(origin, "Origin")  # does validate the departure city
        destination = self.required_text(destination, "Destination")  # does validate the arrival city
        if origin.casefold() == destination.casefold():  # does compare city names without letter-case differences
            raise ValueError("Origin and destination must be different.")  # does reject a flight to the same city
        departure = departure.strip()  # does remove surrounding spaces from the departure date
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", departure):  # does require the displayed date and time format
            raise ValueError("Departure must use YYYY-MM-DD HH:MM.")  # does explain the expected departure format
        try:  # does attempt to check the actual calendar date and time
            datetime.strptime(departure, "%Y-%m-%d %H:%M")  # does reject impossible dates and times
        except ValueError:  # does handle a date that has the right format but an invalid value
            raise ValueError("Departure must be a valid date and time.") from None  # does give a short calendar validation message
        self.positive_integer(seats, "Seats")  # does validate the flight capacity
        self.positive_integer(price, "Price")  # does validate the ticket price in KZT
        return number, origin, destination, departure, seats, price  # does return the cleaned flight fields

    def passenger_values(self, name, email):  # does validate the editable passenger fields
        name = self.required_text(name, "Name")  # does require a passenger name
        email = email.strip().lower()  # does standardize the email address
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):  # does check a simple email address pattern
            raise ValueError("Enter a valid email address, such as alex@example.com.")  # does explain the accepted email format
        return name, email  # does return the cleaned passenger fields

    def add_flight(self, number, origin, destination, departure, seats, price):  # does create a flight after validating its fields
        values = self.flight_values(number, origin, destination, departure, seats, price)  # does check and clean the flight information
        return self.database.execute("INSERT INTO flights (number, origin, destination, departure, seats, price) VALUES (?, ?, ?, ?, ?, ?)", values)  # does save the new flight and return its ID

    def add_passenger(self, name, email):  # does create a passenger after validating their fields
        values = self.passenger_values(name, email)  # does check and clean the passenger information
        return self.database.execute("INSERT INTO passengers (name, email) VALUES (?, ?)", values)  # does save the new passenger and return their ID

    def check_booking(self, flight_id, passenger_id, seat, ticket_id=0):  # does validate a new booking or a ticket change
        flight = self.get_record("flights", flight_id)  # does require an existing flight
        self.get_record("passengers", passenger_id)  # does require an existing passenger
        self.positive_integer(seat, "Seat")  # does require a positive seat number
        if seat > flight["seats"]:  # does check whether the seat is inside the plane capacity
            raise ValueError(f"Seat must be between 1 and {flight['seats']}.")  # does display the allowed seat range
        matches = self.database.fetch("SELECT id FROM tickets WHERE flight_id = ? AND id != ? AND (seat = ? OR passenger_id = ?)", (flight_id, ticket_id, seat, passenger_id))  # does look for an occupied seat or an existing booking for this passenger
        if matches:  # does detect a booking conflict
            raise ValueError("Seat is already booked or passenger already has a ticket for this flight.")  # does explain why the ticket cannot be saved
        return flight  # does return the flight so its price can be used

    def add_ticket(self, flight_id, passenger_id, seat):  # does book one seat for one passenger
        flight = self.check_booking(flight_id, passenger_id, seat)  # does validate the flight, passenger, and seat
        return self.database.execute("INSERT INTO tickets (flight_id, passenger_id, seat, price) VALUES (?, ?, ?, ?)", (flight_id, passenger_id, seat, flight["price"]))  # does save the ticket at the current flight price

    def list_flights(self):  # does read every flight with its number of booked seats
        return self.database.fetch("SELECT f.*, COUNT(t.id) AS booked FROM flights f LEFT JOIN tickets t ON f.id = t.flight_id GROUP BY f.id ORDER BY f.id")  # does include flights without any bookings

    def list_passengers(self):  # does read every passenger
        return self.database.fetch("SELECT * FROM passengers ORDER BY id")  # does return passengers in ID order

    def list_tickets(self):  # does read tickets together with their related flight and passenger information
        return self.database.fetch("SELECT t.id, t.flight_id, f.number AS flight, f.destination, t.passenger_id, p.name AS passenger, t.seat, t.price FROM tickets t JOIN flights f ON t.flight_id = f.id JOIN passengers p ON t.passenger_id = p.id ORDER BY t.id")  # does show readable ticket details instead of only foreign keys

    def search_passengers(self, query):  # does search passengers by exact ID or part of a name
        query = self.required_text(query, "Search")  # does require a non-empty search value
        return self.database.fetch("SELECT * FROM passengers WHERE CAST(id AS TEXT) = ? OR instr(lower(name), lower(?)) > 0 ORDER BY id", (query, query))  # does match an ID or a name without treating input as SQL

    def search_flights(self, destination):  # does search flights by part of their destination
        destination = self.required_text(destination, "Destination")  # does require a non-empty destination search
        return self.database.fetch("SELECT f.*, COUNT(t.id) AS booked FROM flights f LEFT JOIN tickets t ON f.id = t.flight_id WHERE instr(lower(f.destination), lower(?)) > 0 GROUP BY f.id ORDER BY f.id", (destination,))  # does match destinations without letter-case differences

    def update_flight(self, flight_id, number, origin, destination, departure, seats, price):  # does replace the editable details of an existing flight
        self.get_record("flights", flight_id)  # does require the flight to exist
        values = self.flight_values(number, origin, destination, departure, seats, price)  # does validate the replacement flight fields
        highest_seat = self.database.fetch("SELECT COALESCE(MAX(seat), 0) AS highest FROM tickets WHERE flight_id = ?", (flight_id,))[0]["highest"]  # does find the highest seat number already booked
        if seats < highest_seat:  # does detect a capacity change that would invalidate a booked seat
            raise ValueError(f"Capacity must include already booked seat {highest_seat}.")  # does explain why the new capacity cannot be saved
        self.database.execute("UPDATE flights SET number = ?, origin = ?, destination = ?, departure = ?, seats = ?, price = ? WHERE id = ?", values + (flight_id,))  # does save the flight changes without changing existing ticket prices

    def update_passenger(self, passenger_id, name, email):  # does replace the details of an existing passenger
        self.get_record("passengers", passenger_id)  # does require the passenger to exist
        values = self.passenger_values(name, email)  # does validate the replacement passenger fields
        self.database.execute("UPDATE passengers SET name = ?, email = ? WHERE id = ?", values + (passenger_id,))  # does save the passenger changes

    def update_ticket(self, ticket_id, flight_id, passenger_id, seat):  # does change the flight, passenger, or seat of an existing ticket
        ticket = self.get_record("tickets", ticket_id)  # does require the ticket to exist
        flight = self.check_booking(flight_id, passenger_id, seat, ticket_id)  # does check the replacement booking while ignoring this ticket
        price = ticket["price"] if ticket["flight_id"] == flight_id else flight["price"]  # does keep the original price unless the passenger changes flights
        self.database.execute("UPDATE tickets SET flight_id = ?, passenger_id = ?, seat = ?, price = ? WHERE id = ?", (flight_id, passenger_id, seat, price, ticket_id))  # does save the replacement booking

    def delete_record(self, table, record_id):  # does delete a flight or passenger or cancel a ticket
        self.get_record(table, record_id)  # does validate the table and require an existing record
        if table in ("flights", "passengers"):  # does check whether the record can be referenced by tickets
            column = "flight_id" if table == "flights" else "passenger_id"  # does choose the matching foreign key column
            if self.database.fetch(f"SELECT id FROM tickets WHERE {column} = ?", (record_id,)):  # does look for tickets linked to the record
                raise ValueError("Cancel the related tickets before deleting this record.")  # does prevent deleting a flight or passenger that still has bookings
        self.database.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))  # does delete the validated record and release a seat when a ticket is cancelled

    def statistics(self):  # does calculate revenue and occupancy using stored database records
        flights = self.database.fetch("SELECT COUNT(*) AS total, COALESCE(SUM(seats), 0) AS seats FROM flights")[0]  # does count flights and add their seat capacities
        passengers = self.database.fetch("SELECT COUNT(*) AS total FROM passengers")[0]["total"]  # does count the stored passengers
        tickets = self.database.fetch("SELECT COUNT(*) AS total, COALESCE(SUM(price), 0) AS revenue FROM tickets")[0]  # does count active tickets and add their actual booking prices
        occupancy = tickets["total"] / flights["seats"] * 100 if flights["seats"] else 0  # does calculate the percentage of seats booked and avoid division by zero
        return {"flights": flights["total"], "passengers": passengers, "tickets": tickets["total"], "seats": flights["seats"], "revenue": tickets["revenue"], "occupancy": occupancy}  # does return the calculated summary

    def summary_lines(self):  # does prepare readable lines for both the console and the report
        stats = self.statistics()  # does read the current calculated summary
        return ["AIRLINE RESERVATION SYSTEM", f"Flights: {stats['flights']}", f"Passengers: {stats['passengers']}", f"Active tickets: {stats['tickets']}", f"Total seats: {stats['seats']}", f"Total ticket revenue: {stats['revenue']} KZT", f"Seat occupancy rate: {stats['occupancy']:.2f}%"]  # does format record counts and both required calculations

    def export_results(self, path=None):  # does save the project information and statistics to a text report
        if path is None:  # does check whether a custom export location was supplied
            path = Path(__file__).parent / "results.txt"  # does choose the required report filename beside the program
        lines = self.summary_lines()  # does start the report with project statistics
        lines.append("Revenue counts active tickets; cancelling a ticket removes its price from the total.")  # does explain how cancellations affect the calculation
        lines.append("Occupancy = active tickets / total flight seats * 100.")  # does explain the occupancy formula
        lines.append("\nFLIGHTS")  # does add the flight section heading
        for flight in self.list_flights():  # does include every stored flight in the report
            occupancy = flight["booked"] / flight["seats"] * 100  # does calculate the individual flight occupancy
            lines.append(f"{flight['id']} | {flight['number']} | {flight['origin']} -> {flight['destination']} | {flight['departure']} | {flight['booked']}/{flight['seats']} seats | {occupancy:.2f}% | {flight['price']} KZT")  # does format a flight with its booking count and occupancy
        lines.append("\nPASSENGERS")  # does add the passenger section heading
        for passenger in self.list_passengers():  # does include every stored passenger in the report
            lines.append(f"{passenger['id']} | {passenger['name']} | {passenger['email']}")  # does format one passenger record
        lines.append("\nTICKETS")  # does add the ticket section heading
        for ticket in self.list_tickets():  # does include every active ticket in the report
            lines.append(f"{ticket['id']} | {ticket['flight']} | {ticket['passenger']} | seat {ticket['seat']} | {ticket['price']} KZT")  # does format one ticket with readable flight and passenger details
        Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")  # does write the complete report as a UTF-8 text file
        return Path(path)  # does return the saved report location
