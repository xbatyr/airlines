import random
import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path=None):
        if path is None:
            path = Path(__file__).parent / "project.db"
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.execute("PRAGMA foreign_keys = ON")
            # SQLite lower() only handles ASCII letters.
            self.connection.create_function("casefold", 1, str.casefold)
            self.create_tables()
        except sqlite3.Error:
            self.connection.close()
            raise

    def create_tables(self):
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS flights (
                id INTEGER PRIMARY KEY,
                number TEXT NOT NULL UNIQUE,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                departure TEXT NOT NULL,
                seats INTEGER NOT NULL CHECK (seats > 0),
                price INTEGER NOT NULL CHECK (price > 0)
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS passengers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )"""
        )
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                flight_id INTEGER NOT NULL REFERENCES flights(id),
                passenger_id INTEGER NOT NULL REFERENCES passengers(id),
                seat INTEGER NOT NULL CHECK (seat > 0),
                price INTEGER NOT NULL CHECK (price > 0),
                UNIQUE (flight_id, seat),
                UNIQUE (flight_id, passenger_id)
            )"""
        )
        self.connection.commit()

    def execute(self, sql, values=()):
        with self.connection:
            cursor = self.connection.execute(sql, values)
        return cursor.lastrowid

    def fetch(self, sql, values=()):
        return self.connection.execute(sql, values).fetchall()

    def seed(self):
        for table in ("flights", "passengers", "tickets"):
            if self.fetch(f"SELECT COUNT(*) AS total FROM {table}")[0]["total"]:
                return False
        generator = random.Random(26)
        cities = [
            "Astana",
            "Shymkent",
            "Aktau",
            "Atyrau",
            "London",
            "Istanbul",
            "Seoul",
            "Dubai",
            "Tashkent",
            "Bishkek",
        ]
        first_names = [
            "Alex",
            "Sam",
            "Dana",
            "Amir",
            "Aida",
            "Maria",
            "John",
            "Sara",
            "Ali",
            "Anna",
        ]
        last_names = ["Brown", "Lee", "Smith", "Wilson", "Taylor"]
        with self.connection:
            for index in range(20):
                seats = generator.randint(50, 100)
                price = generator.randrange(20000, 100001, 1000)
                departure = f"2026-11-{index + 1:02d} 10:00"
                self.connection.execute(
                    """INSERT INTO flights
                       (number, origin, destination, departure, seats, price)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        f"KC{100 + index}",
                        "Almaty",
                        cities[index % len(cities)],
                        departure,
                        seats,
                        price,
                    ),
                )
            for index in range(50):
                name = f"{first_names[index % 10]} {last_names[index // 10]}"
                email = f"passenger{index + 1}@example.com"
                self.connection.execute(
                    "INSERT INTO passengers (name, email) VALUES (?, ?)", (name, email)
                )
            passenger_ids = generator.sample(range(1, 51), 40)
            for index, passenger_id in enumerate(passenger_ids):
                flight_id = index % 20 + 1
                seat = index // 20 + 1
                price = self.fetch(
                    "SELECT price FROM flights WHERE id = ?", (flight_id,)
                )[0]["price"]
                self.connection.execute(
                    """INSERT INTO tickets (flight_id, passenger_id, seat, price)
                       VALUES (?, ?, ?, ?)""",
                    (flight_id, passenger_id, seat, price),
                )
        return True

    def close(self):
        self.connection.close()
