import unittest
from datetime import date, timedelta

from parser.message_parser import parse_message


class MessageParserTests(unittest.TestCase):
    def test_parses_debt_with_amount_person_and_relative_due_date(self):
        result = parse_message(
            {"message_text": "O Fabio me deve 400 reais para daqui 30 dias"}
        )

        self.assertEqual(result["intent"], "CREATE_DEBT")
        self.assertEqual(result["entities"]["person"], "Fabio")
        self.assertEqual(result["entities"]["amount"], 400.0)
        self.assertEqual(
            result["entities"]["due_date"],
            (date.today() + timedelta(days=30)).isoformat(),
        )

    def test_defaults_due_date_to_today(self):
        result = parse_message({"message_text": "Fabio pagou 100"})

        self.assertEqual(result["intent"], "REGISTER_PAYMENT")
        self.assertEqual(result["entities"]["due_date"], date.today().isoformat())

    def test_parses_decimal_amount_with_comma(self):
        result = parse_message({"message_text": "devo 12,50 para Fabio"})

        self.assertEqual(result["entities"]["amount"], 12.5)


if __name__ == "__main__":
    unittest.main()
