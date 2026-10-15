import sqlite3
import tempfile
import unittest
from pathlib import Path

from airline import AirlineSystem
from database import Database


class ReservationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "test.db"
        self.database = Database(self.path)
        self.system = AirlineSystem(self.database)

    def tearDown(self):
        self.database.close()
        self.folder.cleanup()

    def create_booking_data(self):
        flight = self.system.add_flight(
            "KC999", "Almaty", "Astana", "2026-11-01 10:00", 2, 30000
        )
        first = self.system.add_passenger("Alex Brown", "alex@example.com")
        second = self.system.add_passenger("Sam Lee", "sam@example.com")
        return flight, first, second

    def test_seed_and_persistence(self):
        self.assertTrue(self.database.seed())
        stats = self.system.statistics()
        self.assertEqual(
            (stats["flights"], stats["passengers"], stats["tickets"]), (20, 50, 40)
        )
        expected_revenue = sum(row["price"] for row in self.system.list_tickets())
        self.assertEqual(stats["revenue"], expected_revenue)
        self.assertAlmostEqual(stats["occupancy"], 40 / stats["seats"] * 100)
        self.assertFalse(self.database.seed())
        self.database.close()
        self.database = Database(self.path)
        self.system = AirlineSystem(self.database)
        self.assertEqual(self.system.statistics(), stats)
        self.assertEqual(self.database.fetch("PRAGMA foreign_key_check"), [])

    def test_seat_conflicts_and_cancellation(self):
        flight, first, second = self.create_booking_data()
        ticket = self.system.add_ticket(flight, first, 1)
        for passenger, seat in ((second, 1), (first, 2), (second, 3)):
            with self.assertRaises(ValueError):
                self.system.add_ticket(flight, passenger, seat)
        self.assertEqual(self.system.statistics()["occupancy"], 50)
        self.system.delete_record("tickets", ticket)
        self.assertEqual(self.system.statistics()["revenue"], 0)
        self.system.add_ticket(flight, second, 1)

    def test_updates_and_relationships(self):
        flight, first, second = self.create_booking_data()
        ticket = self.system.add_ticket(flight, first, 2)
        self.system.update_flight(
            flight, "KC999", "Almaty", "Dubai", "2026-11-02 12:00", 2, 45000
        )
        self.assertEqual(self.system.statistics()["revenue"], 30000)
        with self.assertRaises(ValueError):
            self.system.update_flight(
                flight, "KC999", "Almaty", "Dubai", "2026-11-02 12:00", 1, 45000
            )
        for table, record_id in (("flights", flight), ("passengers", first)):
            with self.assertRaises(ValueError):
                self.system.delete_record(table, record_id)
        self.system.update_passenger(second, "Sam Updated", "updated@example.com")
        self.system.update_ticket(ticket, flight, second, 1)
        self.assertEqual(self.system.list_tickets()[0]["passenger"], "Sam Updated")
        self.assertEqual(self.system.statistics()["revenue"], 30000)
        other_flight = self.system.add_flight(
            "KC998", "Almaty", "Seoul", "2026-11-03 12:00", 2, 70000
        )
        self.system.update_ticket(ticket, other_flight, second, 2)
        self.assertEqual(self.system.statistics()["revenue"], 70000)
        self.system.delete_record("flights", flight)
        self.system.delete_record("passengers", first)

    def test_search_and_export(self):
        flight, first, second = self.create_booking_data()
        self.system.add_ticket(flight, first, 1)
        self.assertEqual(self.system.search_passengers("aLeX")[0]["id"], first)
        self.assertEqual(self.system.search_passengers(str(second))[0]["id"], second)
        self.assertEqual(self.system.search_flights("AST")[0]["id"], flight)
        self.assertEqual(self.system.search_passengers("missing"), [])
        self.assertEqual(self.system.search_flights("missing"), [])
        self.assertEqual(self.system.search_passengers("' OR 1=1 --"), [])
        report = self.system.export_results(Path(self.folder.name) / "results.txt")
        text = report.read_text(encoding="utf-8")
        for expected in (
            "FLIGHTS",
            "PASSENGERS",
            "TICKETS",
            "KC999",
            "Alex Brown",
            "30000 KZT",
            "50.00%",
            "seat 1",
        ):
            self.assertIn(expected, text)

    def test_input_validation_and_database_constraints(self):
        flight, first, second = self.create_booking_data()
        for email in ("wrong", "x@y", "x @example.com"):
            with self.assertRaises(ValueError):
                self.system.add_passenger("Invalid Email", email)
        for departure in ("2026-02-30 10:00", "2026-11-01 25:00", "2026-1-1 10:00"):
            with self.assertRaises(ValueError):
                self.system.add_flight("KC100", "Almaty", "Astana", departure, 2, 10000)
        with self.assertRaises(sqlite3.IntegrityError):
            self.system.add_passenger("Duplicate", "alex@example.com")
        with self.assertRaises(sqlite3.IntegrityError):
            self.database.execute(
                "INSERT INTO tickets (flight_id, passenger_id, seat, price) VALUES (?, ?, ?, ?)",
                (flight, 999, 1, 30000),
            )
        self.assertEqual(len(self.system.list_passengers()), 2)
        self.assertEqual(self.system.list_tickets(), [])
        self.system.add_ticket(flight, second, 1)

    def test_empty_statistics_and_existing_data(self):
        self.assertEqual(self.system.statistics()["occupancy"], 0)
        self.assertEqual(self.system.statistics()["revenue"], 0)
        self.system.add_passenger("Only Passenger", "only@example.com")
        self.assertFalse(self.database.seed())
        self.assertEqual(self.system.statistics()["passengers"], 1)

    def test_unicode_search(self):
        passenger = self.system.add_passenger("Әлия Иванова", "aliya@example.com")
        flight = self.system.add_flight(
            "KC888", "Алматы", "Өскемен", "2026-11-01 10:00", 2, 30000
        )
        self.assertEqual(self.system.search_passengers("ӘЛИЯ")[0]["id"], passenger)
        self.assertEqual(self.system.search_passengers("ИВАНОВА")[0]["id"], passenger)
        self.assertEqual(self.system.search_flights("ӨСКЕМЕН")[0]["id"], flight)

    def test_failed_ticket_update_keeps_original_booking(self):
        flight, first, second = self.create_booking_data()
        ticket = self.system.add_ticket(flight, first, 1)
        self.system.add_ticket(flight, second, 2)
        before = [dict(row) for row in self.system.list_tickets()]
        for passenger, seat in ((first, 2), (second, 1), (first, 3)):
            with self.subTest(passenger=passenger, seat=seat):
                with self.assertRaises(ValueError):
                    self.system.update_ticket(ticket, flight, passenger, seat)
                self.assertEqual(
                    [dict(row) for row in self.system.list_tickets()], before
                )
        self.system.update_ticket(ticket, flight, first, 1)
        self.assertEqual(self.system.booked_seats(flight), [1, 2])
        self.system.delete_record("tickets", ticket)
        self.assertEqual(self.system.booked_seats(flight), [2])

    def test_invalid_fields_and_ids(self):
        flight, first, second = self.create_booking_data()
        for value in (0, -1, True, 1.5, "1", 10**30):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.system.add_ticket(flight, first, value)
                with self.assertRaises(ValueError):
                    self.system.get_record("flights", value)
        for name in (" ", None, "Alex\nBrown", "Alex\tBrown", "Alex\x00Brown"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.system.add_passenger(name, "new@example.com")
        with self.assertRaises(ValueError):
            self.system.add_flight("KC１２３", "A", "B", "2026-11-01 10:00", 2, 30000)
        with self.assertRaises(ValueError):
            self.system.add_flight(
                "KC888", "Алматы", "АЛМАТЫ", "2026-11-01 10:00", 2, 30000
            )
        for table, record_id in (
            ("flights", 999),
            ("passengers", 999),
            ("tickets", 999),
            ("unknown", 1),
        ):
            with self.subTest(table=table), self.assertRaises(ValueError):
                self.system.delete_record(table, record_id)
        self.assertEqual(self.system.statistics()["passengers"], 2)

    def test_normalization_and_duplicate_updates(self):
        flight, first, second = self.create_booking_data()
        self.system.update_passenger(second, "  Sam Lee  ", "  SAM@EXAMPLE.COM  ")
        self.assertEqual(
            self.system.get_record("passengers", second)["email"], "sam@example.com"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.system.update_passenger(second, "Changed", "ALEX@EXAMPLE.COM")
        self.assertEqual(
            self.system.get_record("passengers", second)["name"], "Sam Lee"
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.system.add_flight(" kc999 ", "A", "B", "2026-11-01 10:00", 2, 30000)
        self.assertEqual(self.system.statistics()["flights"], 1)

    def test_export_cannot_overwrite_database(self):
        self.create_booking_data()
        with self.assertRaises(ValueError):
            self.system.export_results(self.path)
        self.assertEqual(self.database.fetch("PRAGMA integrity_check")[0][0], "ok")
        self.assertEqual(self.system.statistics()["passengers"], 2)


if __name__ == "__main__":
    unittest.main()
