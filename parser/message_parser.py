
import re
from datetime import date, timedelta

INTENTS = {
    "REGISTER_PAYMENT": ["pagou", "recebi", "recebido", "pago"],
    "LIST_DEBTS": [
        "pendente", "pendentes", "dívida", "divida", "dívidas", "dividas",
        "cobrança", "cobranca", "cobranças", "cobrancas",
        "quem", "quanto", "?",
    ],
    "CREATE_DEBT": ["emprestei", "emprestar", "anotar", "registrar", "criar", "deve"],
}

PREPOSITIONS = ["para", "de", "do", "da", "em", "no", "na", "com", "sem", "o", "a"]

STOPWORDS = [
    *PREPOSITIONS,
    "deve", "emprestei", "emprestar", "anotar", "registrar", "criar",
    "pagou", "recebi", "recebido", "pago",
    "me",     "divida", "dividas", "cobranca", "cobrancas",
    "eu", "ele", "ela", "um", "uma",
    "reais", "real", "euros", "euro",
]

QUESTION_WORDS = ["quanto", "quem", "qual", "quais", "onde"]


def extract_due_date(message_text: str) -> str:
    match = re.search(
        r"\b(?:daqui|para)\s+(\d+)\s+dias?\b",
        message_text,
    )
    if not match:
        return date.today().isoformat()

    due_date = date.today() + timedelta(days=int(match.group(1)))
    return due_date.isoformat()


def extract_description(message_text: str) -> str | None:
    labeled = re.search(
        r"\bdescri(?:ção|cao)\s*:\s*(.+)$",
        message_text,
        re.IGNORECASE,
    )
    if labeled:
        return labeled.group(1).strip()

    separator = re.search(r"\s+-\s+(.+)$", message_text)
    return separator.group(1).strip() if separator else None


def parse_message(message):
    original_text = message.get("message_text", "")
    message_text = original_text.lower()
    words = message_text.split()
    due_date = extract_due_date(message_text)
    description = extract_description(original_text)

    # 1. Extract amounts
    amount_matches = re.findall(
        r"(?<!\w)\d+(?:[.,]\d{1,2})?(?!\w)",
        message_text
    )

    amounts = [
        float(amount.replace(",", "."))
        for amount in amount_matches
    ]

    has_number = len(amounts) > 0

    # 2. Identify intent
    scores = {intent: 0 for intent in INTENTS}

    for word in words:
        word = re.sub(r"[^\w]", "", word)

        for intent, keywords in INTENTS.items():
            if word in keywords:
                scores[intent] += 1

    if has_number and scores["CREATE_DEBT"] > 0:
        scores["CREATE_DEBT"] += 3

    if scores["REGISTER_PAYMENT"] > 0:
        scores["REGISTER_PAYMENT"] += 3

    intent = max(scores, key=scores.get)

    if scores[intent] == 0:
        intent = "UNKNOWN"
    
    # 3. Identify person
    name = None

    for i, word in enumerate(words):
        candidate = re.sub(r"[^\w]", "", word)

        if (
            candidate not in STOPWORDS
            and candidate not in QUESTION_WORDS
            and not re.search(r"\d", candidate)
        ):
            name = candidate.capitalize()
            break

    if intent == "UNKNOWN" and has_number and name:
        intent = "CREATE_DEBT"

    return {
        "intent": intent,
        "entities": {
            "amount": amounts[0] if amounts else None,
            "person": name,
            "due_date": due_date,
            "description": description,
        },
        "needs_confirmation": True
    }
