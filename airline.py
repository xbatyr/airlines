import re
from datetime import datetime
from pathlib import Path


class AirlineSystem:
    def __init__(self, database):
        self.database = database

    # validate a positive integer
    def positive_integer(self, value, label):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{label} must be a positive whole number.")
        return value

    # validate required text; label identifies the field in errors
    def required_text(self, value, label):
        if not isinstance(value, str):
            raise ValueError(f"{label} must be text.")
        value = value.strip()
        if not value:
            raise ValueError(f"{label} cannot be empty.")
        if not value.isprintable():
            raise ValueError(
                f"{label} must be a single line without control characters."
            )
        return value

    # find a record by ID or raise an error
    def get_record(self, table, record_id):
        if table not in ("flights", "passengers", "tickets"):
            raise ValueError("Unknown record type.")
        self.positive_integer(record_id, "ID")
        rows = self.database.fetch(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
        if not rows:
            raise ValueError("Record not found.")
        return rows[0]

    # validate and normalize flight details
    def flight_values(self, number, origin, destination, departure, seats, price):
        number = self.required_text(number, "Flight number").upper()
        if not re.fullmatch(r"[A-Z]{2}[0-9]{3,4}", number):
            raise ValueError("Flight number must look like KC123 or KC1234.")
        origin = self.required_text(origin, "Origin")
        destination = self.required_text(destination, "Destination")
        if origin.casefold() == destination.casefold():
            raise ValueError("Origin and destination must be different.")
        departure = self.required_text(departure, "Departure")
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", departure):
            raise ValueError("Departure must use YYYY-MM-DD HH:MM.")
        try:
            datetime.strptime(departure, "%Y-%m-%d %H:%M")
        except ValueError:
            raise ValueError("Departure must be a valid date and time.") from None
        self.positive_integer(seats, "Seats")
        self.positive_integer(price, "Price")
        return number, origin, destination, departure, seats, price

    # validate the name and email
    def passenger_values(self, name, email):
        name = self.required_text(name, "Name")
        email = self.required_text(email, "Email").lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Enter a valid email address, such as alex@example.com.")
        return name, email

    def add_flight(self, number, origin, destination, departure, seats, price):
        values = self.flight_values(
            number, origin, destination, departure, seats, price
        )
        return self.database.execute(
            """INSERT INTO flights (number, origin, destination, departure, seats, price)
               VALUES (?, ?, ?, ?, ?, ?)""",
            values,
        )

    def add_passenger(self, name, email):
        values = self.passenger_values(name, email)
        return self.database.execute(
            "INSERT INTO passengers (name, email) VALUES (?, ?)", values
        )

    # check references, seat range and booking conflicts
    def check_booking(self, flight_id, passenger_id, seat, ticket_id=0):
        flight = self.get_record("flights", flight_id)
        self.get_record("passengers", passenger_id)
        self.positive_integer(seat, "Seat")
        if seat > flight["seats"]:
            raise ValueError(f"Seat must be between 1 and {flight['seats']}.")
        # exclude the current ticket when updating a booking
        matches = self.database.fetch(
            """SELECT seat FROM tickets
               WHERE flight_id = ? AND id != ? AND (seat = ? OR passenger_id = ?)""",
            (flight_id, ticket_id, seat, passenger_id),
        )
        if any(row["seat"] == seat for row in matches):
            raise ValueError("This seat is already booked. Choose another seat.")
        if matches:
            raise ValueError("This passenger already has a ticket for this flight.")
        return flight

    def booked_seats(self, flight_id):
        self.get_record("flights", flight_id)
        rows = self.database.fetch(
            "SELECT seat FROM tickets WHERE flight_id = ? ORDER BY seat", (flight_id,)
        )
        return [row["seat"] for row in rows]

    def add_ticket(self, flight_id, passenger_id, seat):
        # save the current flight price with the ticket
        flight = self.check_booking(flight_id, passenger_id, seat)
        return self.database.execute(
            """INSERT INTO tickets (flight_id, passenger_id, seat, price)
               VALUES (?, ?, ?, ?)""",
            (flight_id, passenger_id, seat, flight["price"]),
        )

    # include flights without tickets and count booked seats
    def list_flights(self):
        return self.database.fetch(
            """SELECT f.*, COUNT(t.id) AS booked FROM flights f
               LEFT JOIN tickets t ON f.id = t.flight_id
               GROUP BY f.id ORDER BY f.id"""
        )

    def list_passengers(self):
        return self.database.fetch("SELECT * FROM passengers ORDER BY id")

    # join tickets with flight and passenger details
    def list_tickets(self):
        return self.database.fetch(
            """SELECT t.id, t.flight_id, f.number AS flight, f.destination,
                      t.passenger_id, p.name AS passenger, t.seat, t.price
               FROM tickets t
               JOIN flights f ON t.flight_id = f.id
               JOIN passengers p ON t.passenger_id = p.id
               ORDER BY t.id"""
        )

    # search by exact ID or part of a name, ignoring case
    def search_passengers(self, query):
        query = self.required_text(query, "Search")
        return self.database.fetch(
            """SELECT * FROM passengers
               WHERE CAST(id AS TEXT) = ? OR instr(casefold(name), casefold(?)) > 0
               ORDER BY id""",
            (query, query),
        )

    # search by destination, ignoring case
    def search_flights(self, destination):
        destination = self.required_text(destination, "Destination")
        return self.database.fetch(
            """SELECT f.*, COUNT(t.id) AS booked FROM flights f
               LEFT JOIN tickets t ON f.id = t.flight_id
               WHERE instr(casefold(f.destination), casefold(?)) > 0
               GROUP BY f.id ORDER BY f.id""",
            (destination,),
        )

    # update flight details without invalidating booked seats
    def update_flight(
        self, flight_id, number, origin, destination, departure, seats, price
    ):
        self.get_record("flights", flight_id)
        values = self.flight_values(
            number, origin, destination, departure, seats, price
        )
        # capacity must cover the highest booked seat number
        highest_seat = self.database.fetch(
            "SELECT COALESCE(MAX(seat), 0) AS highest FROM tickets WHERE flight_id = ?",
            (flight_id,),
        )[0]["highest"]
        if seats < highest_seat:
            raise ValueError(
                f"Capacity must include already booked seat {highest_seat}."
            )
        self.database.execute(
            """UPDATE flights SET number = ?, origin = ?, destination = ?,
                      departure = ?, seats = ?, price = ? WHERE id = ?""",
            values + (flight_id,),
        )

    def update_passenger(self, passenger_id, name, email):
        self.get_record("passengers", passenger_id)
        values = self.passenger_values(name, email)
        self.database.execute(
            "UPDATE passengers SET name = ?, email = ? WHERE id = ?",
            values + (passenger_id,),
        )

    def update_ticket(self, ticket_id, flight_id, passenger_id, seat):
        ticket = self.get_record("tickets", ticket_id)
        flight = self.check_booking(flight_id, passenger_id, seat, ticket_id)
        # keep the price unless the ticket moves to another flight
        price = ticket["price"] if ticket["flight_id"] == flight_id else flight["price"]
        self.database.execute(
            """UPDATE tickets SET flight_id = ?, passenger_id = ?, seat = ?, price = ?
               WHERE id = ?""",
            (flight_id, passenger_id, seat, price, ticket_id),
        )

    # delete a record; deleting a ticket cancels its booking
    def delete_record(self, table, record_id):
        self.get_record(table, record_id)
        # cancel related tickets before deleting a flight or passenger
        if table in ("flights", "passengers"):
            column = "flight_id" if table == "flights" else "passenger_id"
            if self.database.fetch(
                f"SELECT id FROM tickets WHERE {column} = ?", (record_id,)
            ):
                raise ValueError(
                    "Cancel the related tickets before deleting this record."
                )
        self.database.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))

    # calculate revenue and occupancy from active tickets
    def statistics(self):
        flights = self.database.fetch(
            "SELECT COUNT(*) AS total, COALESCE(SUM(seats), 0) AS seats FROM flights"
        )[0]
        passengers = self.database.fetch("SELECT COUNT(*) AS total FROM passengers")[0][
            "total"
        ]
        tickets = self.database.fetch(
            "SELECT COUNT(*) AS total, COALESCE(SUM(price), 0) AS revenue FROM tickets"
        )[0]
        occupancy = tickets["total"] / flights["seats"] * 100 if flights["seats"] else 0
        return {
            "flights": flights["total"],
            "passengers": passengers,
            "tickets": tickets["total"],
            "seats": flights["seats"],
            "revenue": tickets["revenue"],
            "occupancy": occupancy,
        }

    def summary_lines(self):
        stats = self.statistics()
        return [
            "AIRLINE RESERVATION SYSTEM",
            f"Flights: {stats['flights']}",
            f"Passengers: {stats['passengers']}",
            f"Active tickets: {stats['tickets']}",
            f"Total seats: {stats['seats']}",
            f"Total ticket revenue: {stats['revenue']} KZT",
            f"Seat occupancy rate: {stats['occupancy']:.2f}%",
        ]

    # export records and statistics to a text file
    def export_results(self, path=None):
        if path is None:
            path = Path(__file__).parent / "results.txt"
        path = Path(path)
        # prevent the report from overwriting the database
        database_file = self.database.fetch("PRAGMA database_list")[0]["file"]
        if database_file and path.resolve() == Path(database_file).resolve():
            raise ValueError("The report must not overwrite the database.")
        lines = self.summary_lines()
        lines.append(
            "Revenue counts active tickets; cancelling a ticket removes its price from the total."
        )
        lines.append("Occupancy = active tickets / total flight seats * 100.")
        lines.append("\nFLIGHTS")
        for flight in self.list_flights():
            occupancy = flight["booked"] / flight["seats"] * 100
            lines.append(
                f"{flight['id']} | {flight['number']} | "
                f"{flight['origin']} -> {flight['destination']} | {flight['departure']} | "
                f"{flight['booked']}/{flight['seats']} seats | "
                f"{occupancy:.2f}% | {flight['price']} KZT"
            )
        lines.append("\nPASSENGERS")
        for passenger in self.list_passengers():
            lines.append(
                f"{passenger['id']} | {passenger['name']} | {passenger['email']}"
            )
        lines.append("\nTICKETS")
        for ticket in self.list_tickets():
            lines.append(
                f"{ticket['id']} | {ticket['flight']} | {ticket['passenger']} | "
                f"seat {ticket['seat']} | {ticket['price']} KZT"
            )
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
