import sqlite3  # does import the database exception used in integrity checks
import tempfile  # does import tools for creating isolated test folders
import unittest  # does import the built-in testing framework
from pathlib import Path  # does import tools for temporary database and report paths
from airline import AirlineSystem  # does import the reservation operations being tested
from database import Database  # does import the database manager being tested


class ReservationTests(unittest.TestCase):  # does group checks of actual booking rules and saved results
    def setUp(self):  # does create a separate empty database before each test
        self.folder = tempfile.TemporaryDirectory()  # does create a disposable folder without touching project data
        self.path = Path(self.folder.name) / "test.db"  # does choose the temporary database location
        self.database = Database(self.path)  # does create the temporary database and its tables
        self.system = AirlineSystem(self.database)  # does create a system using the temporary database

    def tearDown(self):  # does clean up after every test
        self.database.close()  # does release the temporary database connection
        self.folder.cleanup()  # does remove the temporary folder and its files

    def create_booking_data(self):  # does create one small flight and two passengers for booking checks
        flight = self.system.add_flight("KC999", "Almaty", "Astana", "2026-11-01 10:00", 2, 30000)  # does save a two-seat test flight
        first = self.system.add_passenger("Alex Brown", "alex@example.com")  # does save the first test passenger
        second = self.system.add_passenger("Sam Lee", "sam@example.com")  # does save the second test passenger
        return flight, first, second  # does return the saved IDs for use in tests

    def test_seed_and_persistence(self):  # does check the required dataset and its persistence after reopening
        self.assertTrue(self.database.seed())  # does require sample data to be generated in an empty database
        stats = self.system.statistics()  # does calculate statistics from the generated data
        self.assertEqual((stats["flights"], stats["passengers"], stats["tickets"]), (20, 50, 40))  # does verify all required dataset counts
        expected_revenue = sum(row["price"] for row in self.system.list_tickets())  # does independently total the stored ticket prices
        self.assertEqual(stats["revenue"], expected_revenue)  # does check the required revenue calculation
        self.assertAlmostEqual(stats["occupancy"], 40 / stats["seats"] * 100)  # does check the required occupancy calculation
        self.assertFalse(self.database.seed())  # does check that repeated startup does not duplicate the dataset
        self.database.close()  # does close the database before testing persistence
        self.database = Database(self.path)  # does reopen the same saved database
        self.system = AirlineSystem(self.database)  # does reconnect the system to the reopened database
        self.assertEqual(self.system.statistics(), stats)  # does check that all stored results survived reopening
        self.assertEqual(self.database.fetch("PRAGMA foreign_key_check"), [])  # does verify the generated table relationships

    def test_seat_conflicts_and_cancellation(self):  # does check duplicate bookings, capacity limits, and seat release
        flight, first, second = self.create_booking_data()  # does prepare the small test flight and passengers
        ticket = self.system.add_ticket(flight, first, 1)  # does book the first seat
        for passenger, seat in ((second, 1), (first, 2), (second, 3)):  # does try an occupied seat, a duplicate passenger, and an out-of-range seat
            with self.assertRaises(ValueError):  # does require each invalid booking to be rejected
                self.system.add_ticket(flight, passenger, seat)  # does attempt the invalid booking
        self.assertEqual(self.system.statistics()["occupancy"], 50)  # does verify that one of two seats is occupied
        self.system.delete_record("tickets", ticket)  # does cancel the original booking
        self.assertEqual(self.system.statistics()["revenue"], 0)  # does verify that cancellation removes its value from active ticket revenue
        self.system.add_ticket(flight, second, 1)  # does verify that the cancelled seat can be booked again

    def test_updates_and_relationships(self):  # does check price history, capacity changes, and protected deletion
        flight, first, second = self.create_booking_data()  # does prepare the test records
        ticket = self.system.add_ticket(flight, first, 2)  # does book the highest seat at the original price
        self.system.update_flight(flight, "KC999", "Almaty", "Dubai", "2026-11-02 12:00", 2, 45000)  # does change the flight destination and current price
        self.assertEqual(self.system.statistics()["revenue"], 30000)  # does check that existing ticket revenue keeps the original price
        with self.assertRaises(ValueError):  # does require an invalid capacity decrease to fail
            self.system.update_flight(flight, "KC999", "Almaty", "Dubai", "2026-11-02 12:00", 1, 45000)  # does try to remove an already booked seat
        for table, record_id in (("flights", flight), ("passengers", first)):  # does check both kinds of referenced record
            with self.assertRaises(ValueError):  # does require deletion of a referenced record to fail
                self.system.delete_record(table, record_id)  # does try to delete a record with an active booking
        self.system.update_passenger(second, "Sam Updated", "updated@example.com")  # does change a passenger name and email
        self.system.update_ticket(ticket, flight, second, 1)  # does move the booking to another passenger and seat on the same flight
        self.assertEqual(self.system.list_tickets()[0]["passenger"], "Sam Updated")  # does verify the updated ticket relationship
        self.assertEqual(self.system.statistics()["revenue"], 30000)  # does verify that a same-flight ticket update preserves its price
        other_flight = self.system.add_flight("KC998", "Almaty", "Seoul", "2026-11-03 12:00", 2, 70000)  # does create another flight with a different price
        self.system.update_ticket(ticket, other_flight, second, 2)  # does move the ticket to the other flight
        self.assertEqual(self.system.statistics()["revenue"], 70000)  # does verify that changing flights uses the new flight price
        self.system.delete_record("flights", flight)  # does delete the original flight after its booking moved away
        self.system.delete_record("passengers", first)  # does delete the original passenger after their booking moved away

    def test_search_and_export(self):  # does verify both search types and the contents of the text report
        flight, first, second = self.create_booking_data()  # does prepare records for searching and reporting
        self.system.add_ticket(flight, first, 1)  # does book one seat for report calculations
        self.assertEqual(self.system.search_passengers("aLeX")[0]["id"], first)  # does check a name search with mixed letter case
        self.assertEqual(self.system.search_passengers(str(second))[0]["id"], second)  # does check a passenger ID search
        self.assertEqual(self.system.search_flights("AST")[0]["id"], flight)  # does check a partial destination search
        self.assertEqual(self.system.search_passengers("missing"), [])  # does check an unsuccessful passenger search
        self.assertEqual(self.system.search_flights("missing"), [])  # does check an unsuccessful flight search
        self.assertEqual(self.system.search_passengers("' OR 1=1 --"), [])  # does check that search input is treated as text rather than SQL
        report = self.system.export_results(Path(self.folder.name) / "results.txt")  # does export the test report to the temporary folder
        text = report.read_text(encoding="utf-8")  # does read back the actual exported file
        for expected in ("FLIGHTS", "PASSENGERS", "TICKETS", "KC999", "Alex Brown", "30000 KZT", "50.00%", "seat 1"):  # does list the required records and calculations in the report
            self.assertIn(expected, text)  # does verify that the exported file contains the expected information

    def test_input_validation_and_database_constraints(self):  # does check invalid fields and database uniqueness rules
        flight, first, second = self.create_booking_data()  # does prepare valid baseline records
        for email in ("wrong", "x@y", "x @example.com"):  # does list invalid sample email addresses
            with self.assertRaises(ValueError):  # does require invalid email input to fail
                self.system.add_passenger("Invalid Email", email)  # does attempt to save the invalid email
        for departure in ("2026-02-30 10:00", "2026-11-01 25:00", "2026-1-1 10:00"):  # does list impossible dates, times, and an incorrect format
            with self.assertRaises(ValueError):  # does require invalid departure input to fail
                self.system.add_flight("KC100", "Almaty", "Astana", departure, 2, 10000)  # does attempt to save the invalid departure
        with self.assertRaises(sqlite3.IntegrityError):  # does require duplicate passenger email addresses to fail
            self.system.add_passenger("Duplicate", "alex@example.com")  # does attempt to reuse an existing email
        with self.assertRaises(sqlite3.IntegrityError):  # does require a nonexistent passenger foreign key to fail
            self.database.execute("INSERT INTO tickets (flight_id, passenger_id, seat, price) VALUES (?, ?, ?, ?)", (flight, 999, 1, 30000))  # does try to bypass the service with an invalid database relationship
        self.assertEqual(len(self.system.list_passengers()), 2)  # does verify that failed writes did not damage valid records
        self.assertEqual(self.system.list_tickets(), [])  # does verify that the invalid database write was rolled back
        self.system.add_ticket(flight, second, 1)  # does verify that the database still accepts a valid write after an error

    def test_empty_statistics_and_existing_data(self):  # does check empty calculations and protection of a partially populated database
        self.assertEqual(self.system.statistics()["occupancy"], 0)  # does check that an empty database avoids division by zero
        self.assertEqual(self.system.statistics()["revenue"], 0)  # does check that an empty database has zero revenue
        self.system.add_passenger("Only Passenger", "only@example.com")  # does create a partially populated database
        self.assertFalse(self.database.seed())  # does check that generation does not overwrite existing user records
        self.assertEqual(self.system.statistics()["passengers"], 1)  # does verify that the existing record was preserved


if __name__ == "__main__":  # does run tests when this file is executed directly
    unittest.main()  # does start the built-in test runner
