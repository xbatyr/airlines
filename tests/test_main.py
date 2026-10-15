import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "main.py"


class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "demo.db"

    def run_app(self, lines, *options):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--database",
                str(self.path),
                *map(str, options),
            ],
            input="\n".join(lines) + ("\n" if lines else ""),
            text=True,
            capture_output=True,
            cwd=self.folder.name,
            timeout=15,
        )

    def test_defense_demo_and_persistence(self):
        result = self.run_app(
            [
                "2",
                "1",
                "1",
                "1",
                "KC900",
                "Almaty",
                "Karaganda",
                "2026-11-25 14:30",
                "2",
                "30000",
                "1",
                "2",
                "Demo Student",
                "demo@example.com",
                "1",
                "3",
                "21",
                "51",
                "1",
                "1",
                "3",
                "21",
                "1",
                "1",
                "1",
                "3",
                "21",
                "51",
                "2",
                "3",
                "1",
                "demo",
                "3",
                "2",
                "karaganda",
                "3",
                "1",
                "missing-person",
                "4",
                "2",
                "51",
                "Demo Updated",
                "updated@example.com",
                "4",
                "1",
                "21",
                "KC900",
                "Almaty",
                "Karaganda",
                "2026-11-25 14:30",
                "2",
                "45000",
                "4",
                "3",
                "41",
                "21",
                "51",
                "2",
                "5",
                "1",
                "21",
                "yes",
                "6",
                "7",
                "0",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for message in (
            "Booked seats: none",
            "Booked seats: 1",
            "This seat is already booked",
            "This passenger already has a ticket",
            "No records found.",
            "Cancel the related tickets",
            "Goodbye!",
        ):
            self.assertIn(message, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        report = self.path.with_suffix(".results.txt").read_text(encoding="utf-8")
        self.assertIn("Demo Updated | seat 2 | 30000 KZT", report)
        self.assertIn("45000 KZT", report)
        self.assertIn("Active tickets: 41", report)
        reopened = self.run_app(
            [
                "6",
                "5",
                "3",
                "41",
                "yes",
                "5",
                "2",
                "51",
                "yes",
                "5",
                "1",
                "21",
                "yes",
                "6",
                "0",
            ]
        )
        self.assertEqual(reopened.returncode, 0, reopened.stderr)
        self.assertNotIn("Sample data created", reopened.stdout)
        self.assertIn("Active tickets: 40", reopened.stdout)
        with sqlite3.connect(self.path) as connection:
            counts = [
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("flights", "passengers", "tickets")
            ]
            self.assertEqual(counts, [20, 50, 40])
            self.assertEqual(
                connection.execute("PRAGMA foreign_key_check").fetchall(), []
            )

    def test_invalid_input_and_cancelled_deletion(self):
        result = self.run_app(
            [
                "wrong",
                "1",
                "2",
                "",
                "Temporary Passenger",
                "temp@example.com",
                "5",
                "2",
                "text",
                "0",
                "-1",
                "51",
                "no",
                "6",
                "0",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for message in (
            "Invalid option.",
            "This field cannot be empty.",
            "Enter a positive whole number.",
            "Deletion cancelled.",
            "Passengers: 51",
        ):
            self.assertIn(message, result.stdout)

    def test_closed_input(self):
        result = self.run_app([])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Program closed.", result.stdout)

    def test_missing_database_directory(self):
        self.path = Path(self.folder.name) / "missing" / "demo.db"
        result = self.run_app(["0"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot open the database", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_corrupt_database(self):
        self.path.write_text("This is not a SQLite database.", encoding="utf-8")
        result = self.run_app(["0"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot open the database", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_export_error_returns_to_menu(self):
        missing_report = Path(self.folder.name) / "missing" / "report.txt"
        result = self.run_app(["7", "6", "0"], "--report", missing_report)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Cannot complete the operation", result.stdout)
        self.assertIn("Active tickets: 40", result.stdout)
        self.assertIn("Goodbye!", result.stdout)


if __name__ == "__main__":
    unittest.main()
