import unittest

from handlers.messages import (
    format_debts_message,
    format_due_date,
    is_all_debts_question,
    is_all_debts_request,
    is_greeting,
    normalize_name,
)


class MessageFormattingTests(unittest.TestCase):
    def test_formats_status_and_open_total(self):
        result = format_debts_message(
            "Gui",
            "todas as pessoas",
            [
                {
                    "debtor_name": "Fabio",
                    "amount": 400,
                    "due_date": "2026-12-15",
                    "status": "debt",
                },
                {
                    "debtor_name": "Maria",
                    "amount": 100,
                    "due_date": "2026-12-16",
                    "status": "paid",
                },
            ],
        )

        self.assertIn("Status: Em aberto", result)
        self.assertIn("Status: Pago", result)
        self.assertIn("Total em aberto: R$400.00", result)

    def test_formats_dates_for_users(self):
        self.assertEqual(format_due_date("2026-12-15"), "15/12/2026")
        self.assertEqual(format_due_date("invalid"), "invalid")

    def test_recognizes_greeting_variations(self):
        for greeting in ("oi", "Ooi", "Oiii", "Olá", "oie", "hello"):
            with self.subTest(greeting=greeting):
                self.assertTrue(is_greeting(greeting))

    def test_normalizes_accents_for_name_comparison(self):
        self.assertEqual(normalize_name("Fábio"), normalize_name("Fabio"))

    def test_recognizes_all_debts_commands(self):
        for request in ("Todos", "Todas", "todas as dívidas"):
            with self.subTest(request=request):
                self.assertTrue(is_all_debts_request(request))

    def test_recognizes_all_debts_questions(self):
        self.assertTrue(is_all_debts_question("Quem me deve?"))


if __name__ == "__main__":
    unittest.main()
