
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
        match = re.search(
            r"\bvencimento\s+(\d+)\s*[’'`]?dias?\b",
            message_text,
            re.IGNORECASE,
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


def parse_brazilian_amount(amount: str) -> float:
    normalized = amount.replace(".", "").replace(",", ".")
    return float(normalized)


def extract_financial_person_and_description(original_text: str) -> tuple[str | None, str | None]:
    lines = [line.strip() for line in original_text.splitlines() if line.strip()]
    if not lines:
        return None, None

    first_line = lines[0]
    person_match = re.match(
        r"^([A-Za-zÀ-ÖØ-öø-ÿ]+)",
        first_line,
    )
    person = person_match.group(1).capitalize() if person_match else None

    description_parts = []
    company_match = re.search(
        r"\b(?:da\s+empresa|empresa)\s+(.+)$",
        first_line,
        re.IGNORECASE,
    )
    if company_match:
        description_parts.append(company_match.group(1).strip(" .:-"))

    for line in lines[1:]:
        if re.match(r"(?i)^valor\s+por\s+", line):
            description_parts.append(
                line.rstrip(":").strip()
            )
            break

    description = " - ".join(description_parts) if description_parts else None
    return person, description


def parse_message(message):
    original_text = message.get("message_text", "")

    currency_amounts = re.findall(
        r"R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?",
        original_text,
        re.IGNORECASE,
    )
    date_lines = re.findall(r"(?<!\d)\d{1,2}/\d{1,2}(?!\d)", original_text)
    normalized_text = original_text.casefold()
    looks_like_financial_statement = (
        len(currency_amounts) >= 2
        or (
            len(date_lines) >= 2
            and any(
                keyword in normalized_text
                for keyword in ("total", "valor por", "vencimento")
            )
        )
    )
    if looks_like_financial_statement:
        amount_matches = re.findall(
            r"\btotal\b\s*:?\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)",
            original_text,
            re.IGNORECASE,
        )
        amounts = [
            parse_brazilian_amount(amount)
            for amount in amount_matches
        ]
        person, description = extract_financial_person_and_description(original_text)
        return {
            "intent": "CREATE_DEBT" if amounts and person else "UNKNOWN",
            "entities": {
                "amount": max(amounts) if amounts else None,
                "person": person,
                "due_date": extract_due_date(original_text),
                "description": description,
            },
            "needs_confirmation": True,
        }

    if "\n" in original_text and not re.match(
        r"^\s*(?:R\$\s*)?\d[\d.,]*\s+\S",
        original_text,
        re.IGNORECASE,
    ):
        return {
            "intent": "UNKNOWN",
            "entities": {
                "amount": None,
                "person": None,
                "due_date": date.today().isoformat(),
                "description": extract_description(original_text),
            },
            "needs_confirmation": True,
        }

    message_text = original_text.lower()
    words = message_text.split()
    due_date = extract_due_date(message_text)
    description = extract_description(original_text)

    # 1. Extract amounts
    amount_matches = re.findall(
        r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)",
        original_text,
        re.IGNORECASE,
    )
    if not amount_matches:
        amount_matches = re.findall(
            r"(?<![\d/])(\d+(?:[.,]\d{1,2})?)(?![\d/])",
            message_text,
        )

    amounts = []
    for amount in amount_matches:
        normalized = amount.replace(".", "").replace(",", ".")
        amounts.append(float(normalized))

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

    is_short_debt_format = bool(
        re.match(
            r"^\s*(?:R\$\s*)?\d[\d.,]*\s+[^\d\n]+(?:\s+para\s+\d+\s+dias?)?",
            original_text,
            re.IGNORECASE,
        )
    )
    if intent == "UNKNOWN" and has_number and name and is_short_debt_format:
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
