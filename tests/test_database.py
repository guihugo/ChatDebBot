import os
import tempfile
import unittest

from database import connection


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(delete=False)
        self.database_file.close()
        connection.DATABASE_PATH = self.database_file.name
        connection.initialize_database()

    def tearDown(self):
        os.unlink(self.database_file.name)

    def test_debts_are_isolated_by_owner(self):
        connection.save_debt_to_database(
            "user-a", "Fabio", 400, "2026-12-15", "debt"
        )
        connection.save_debt_to_database(
            "user-b", "Fabio", 900, "2026-12-15", "debt"
        )

        debts = connection.get_debts_from_person("user-a", "Fabio")

        self.assertEqual(len(debts), 1)
        self.assertEqual(debts[0]["amount"], 400)

    def test_all_debts_only_returns_the_owner_debts(self):
        connection.save_debt_to_database(
            "user-a", "Fabio", 400, "2026-12-15", "debt"
        )
        connection.save_debt_to_database(
            "user-a", "Maria", 100, "2026-12-16", "paid"
        )
        connection.save_debt_to_database(
            "user-b", "Joao", 900, "2026-12-15", "debt"
        )

        debts = connection.get_all_debts("user-a")

        self.assertEqual(
            [debt["debtor_name"] for debt in debts],
            ["Fabio"],
        )

    def test_paid_reminder_updates_only_the_owner_debt(self):
        connection.save_debt_to_database(
            "user-a", "Fabio", 400, "2026-12-15", "debt"
        )
        debt_id = connection.get_debts_from_person("user-a", "Fabio")[0]["id"]

        self.assertTrue(connection.mark_debt_as_paid(debt_id, "user-a"))
        self.assertFalse(connection.mark_debt_as_paid(debt_id, "user-b"))
        self.assertEqual(
            connection.get_debts_from_person("user-a", "Fabio"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
