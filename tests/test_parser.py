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

    def test_extracts_labeled_description(self):
        result = parse_message(
            {"message_text": "500 Fabio para 30 dias descrição: almoço"}
        )

        self.assertEqual(result["entities"]["description"], "almoço")

    def test_extracts_description_after_dash(self):
        result = parse_message({"message_text": "500 Fabio - compra do mercado"})

        self.assertEqual(result["entities"]["description"], "compra do mercado")

    def test_accepts_due_date_without_daqui(self):
        result = parse_message({"message_text": "Jorge me deve 200 para 30 dias"})

        self.assertEqual(
            result["entities"]["due_date"],
            (date.today() + timedelta(days=30)).isoformat(),
        )

    def test_parses_short_debt_format_with_description(self):
        result = parse_message(
            {"message_text": "500 Gabriel para 20 dias - Aeroporto"}
        )

        self.assertEqual(result["intent"], "CREATE_DEBT")
        self.assertEqual(result["entities"]["person"], "Gabriel")
        self.assertEqual(result["entities"]["amount"], 500.0)
        self.assertEqual(result["entities"]["description"], "Aeroporto")

    def test_recognizes_debt_listing_phrases_without_using_question_word_as_name(self):
        result = parse_message({"message_text": "Quem me deve?"})

        self.assertEqual(result["intent"], "LIST_DEBTS")
        self.assertIsNone(result["entities"]["person"])

    def test_recognizes_debt_listing_without_accent(self):
        result = parse_message({"message_text": "Dividas de Fabio"})

        self.assertEqual(result["intent"], "LIST_DEBTS")
        self.assertEqual(result["entities"]["person"], "Fabio")

    def test_does_not_parse_multiline_note_as_debt(self):
        result = parse_message({
            "message_text":
                "Léo da empresa Executive service\n"
                "Valor por van:\n\n"
                "13/11 - R$ 1.500,00\n"
                "14/11"
        })

        self.assertEqual(result["intent"], "UNKNOWN")

    def test_does_not_parse_exact_multiline_van_note_as_debt(self):
        result = parse_message({
            "message_text":
                "Léo da empresa Executive service\n"
                "Valor por van:\n\n"
                "13/11 - R$ 1.500,00\n"
                "14/11 - R$ 1.500,00\n"
                "15/11 - R$ 1.000,00\n"
                "16/11 - R$ 650,00\n\n"
                "Total: R$ 4.650,00\n\n"
                "——————————\n\n"
                "Total R$ 9.300,00. Vencimento 30’dias"
        })

        self.assertEqual(result["intent"], "CREATE_DEBT")
        self.assertEqual(result["entities"]["amount"], 9300.0)
        self.assertEqual(result["entities"]["person"], "Léo")
        self.assertEqual(
            result["entities"]["description"],
            "Executive service - Valor por van",
        )
        self.assertEqual(
            result["entities"]["due_date"],
            (date.today() + timedelta(days=30)).isoformat(),
        )

    def test_parses_brazilian_currency_amount(self):
        result = parse_message({
            "message_text": "Léo me deve R$ 1.500,00"
        })

        self.assertEqual(result["intent"], "CREATE_DEBT")
        self.assertEqual(result["entities"]["person"], "Léo")
        self.assertEqual(result["entities"]["amount"], 1500.0)


if __name__ == "__main__":
    unittest.main()
