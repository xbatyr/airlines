import random  # does import tools for generating sample flight data
import sqlite3  # does import the built-in SQLite database tools
from pathlib import Path  # does import a tool for finding the project folder


class Database:  # does manage the database connection and stored records
    def __init__(self, path=None):  # does open the selected database or the default project database
        if path is None:  # does check whether a database path was supplied
            path = Path(__file__).parent / "project.db"  # does place the database beside the Python files
        self.connection = sqlite3.connect(path)  # does open or create the SQLite database
        self.connection.row_factory = sqlite3.Row  # does allow reading columns by their names
        self.connection.execute("PRAGMA foreign_keys = ON")  # does protect links between the tables
        self.create_tables()  # does create the three tables when they are missing

    def create_tables(self):  # does define the database structure
        self.connection.execute("CREATE TABLE IF NOT EXISTS flights (id INTEGER PRIMARY KEY, number TEXT NOT NULL UNIQUE, origin TEXT NOT NULL, destination TEXT NOT NULL, departure TEXT NOT NULL, seats INTEGER NOT NULL CHECK (seats > 0), price INTEGER NOT NULL CHECK (price > 0))")  # does store flights with capacity and ticket price in KZT
        self.connection.execute("CREATE TABLE IF NOT EXISTS passengers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE)")  # does store passenger names and unique email addresses
        self.connection.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, flight_id INTEGER NOT NULL REFERENCES flights(id), passenger_id INTEGER NOT NULL REFERENCES passengers(id), seat INTEGER NOT NULL CHECK (seat > 0), price INTEGER NOT NULL CHECK (price > 0), UNIQUE (flight_id, seat), UNIQUE (flight_id, passenger_id))")  # does link tickets to flights and passengers and prevent duplicate bookings
        self.connection.commit()  # does save the table definitions

    def execute(self, sql, values=()):  # does run a database change with safely separated values
        with self.connection:  # does save a successful change or roll back a failed change
            cursor = self.connection.execute(sql, values)  # does execute the SQL statement with its values
        return cursor.lastrowid  # does return the ID of an inserted record

    def fetch(self, sql, values=()):  # does read records without changing the database
        return self.connection.execute(sql, values).fetchall()  # does return all matching records

    def seed(self):  # does populate a completely empty database with the required sample dataset
        for table in ("flights", "passengers", "tickets"):  # does check all three known table names
            if self.fetch(f"SELECT COUNT(*) AS total FROM {table}")[0]["total"]:  # does detect an existing record in the selected table
                return False  # does leave existing user data unchanged
        generator = random.Random(26)  # does make random sample data repeatable for every teammate
        cities = ["Astana", "Shymkent", "Aktau", "Atyrau", "London", "Istanbul", "Seoul", "Dubai", "Tashkent", "Bishkek"]  # does list sample destinations
        first_names = ["Alex", "Sam", "Dana", "Amir", "Aida", "Maria", "John", "Sara", "Ali", "Anna"]  # does list fictional first names
        last_names = ["Brown", "Lee", "Smith", "Wilson", "Taylor"]  # does list fictional last names
        with self.connection:  # does save the entire dataset together or undo it if generation fails
            for index in range(20):  # does generate the required twenty flights
                seats = generator.randint(50, 100)  # does choose a sample capacity between fifty and one hundred seats
                price = generator.randrange(20000, 100001, 1000)  # does choose a sample whole-number ticket price in KZT
                departure = f"2026-11-{index + 1:02d} 10:00"  # does give each flight a different departure day
                self.connection.execute("INSERT INTO flights (number, origin, destination, departure, seats, price) VALUES (?, ?, ?, ?, ?, ?)", (f"KC{100 + index}", "Almaty", cities[index % len(cities)], departure, seats, price))  # does save one generated flight
            for index in range(50):  # does generate the required fifty passengers
                name = f"{first_names[index % 10]} {last_names[index // 10]}"  # does combine sample first and last names
                email = f"passenger{index + 1}@example.com"  # does create a unique fictional email address
                self.connection.execute("INSERT INTO passengers (name, email) VALUES (?, ?)", (name, email))  # does save one generated passenger
            passenger_ids = generator.sample(range(1, 51), 40)  # does randomly select forty different sample passengers
            for index, passenger_id in enumerate(passenger_ids):  # does generate one ticket for each selected passenger
                flight_id = index % 20 + 1  # does assign two tickets to each sample flight
                seat = index // 20 + 1  # does assign different seats to the two passengers on each flight
                price = self.fetch("SELECT price FROM flights WHERE id = ?", (flight_id,))[0]["price"]  # does read the selected flight price from the database
                self.connection.execute("INSERT INTO tickets (flight_id, passenger_id, seat, price) VALUES (?, ?, ?, ?)", (flight_id, passenger_id, seat, price))  # does save the ticket with its booking price
        return True  # does report that the sample dataset was created

    def close(self):  # does release the database connection
        self.connection.close()  # does close the SQLite database file
