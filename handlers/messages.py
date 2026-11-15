from datetime import date
import re
import unicodedata

from database.connection import (
    delete_pending_debt,
    delete_pending_action,
    get_all_debts,
    get_debts_from_person,
    get_debtor_names,
    get_pending_action,
    get_pending_debt,
    get_pending_selection,
    mark_debt_as_paid,
    save_debt_to_database,
    save_message_to_database,
    save_pending_action,
    save_pending_selection,
    save_pending_debt,
)
from parser.message_parser import parse_message
from services.whatsapp import send_button_message, send_message

MENU_BUTTONS = [
    {
        "type": "reply",
        "reply": {
            "id": "menu_create_debt",
            "title": "Cadastrar cobrança",
        },
    },
    {
        "type": "reply",
        "reply": {
            "id": "menu_list_debts",
            "title": "Listar cobranças",
        },
    },
    {
        "type": "reply",
        "reply": {
            "id": "menu_update_debt",
            "title": "Atualizar cobrança",
        },
    },
]


async def message_received_handler(message: dict):
    """
    Handles incoming messages and sends a response.

    Args:
        message (str): The incoming message to handle.
    """
    is_new_message = save_message_to_database(
                message_id=message["message_id"],
                sender_id=message["sender_id"],
                sender_phone_number=message["sender_phone_number"],
                message_text=message["message_text"]
            )
    if not is_new_message:
        print(f"Message with ID {message['message_id']} already exists in the database. Skipping processing.")
        return {"status": "duplicate", "payload": message}

    if "button_payload" in message:
        if message["button_payload"].startswith("menu_"):
            return await handle_menu_selection(message)
        if message["button_payload"].startswith("mark_paid_"):
            return await handle_paid_reminder(message)
        if message["button_payload"].startswith("select_person_"):
            return await handle_person_selection(message)
        return await handle_debt_confirmation(message)

    if is_greeting(message["message_text"]):
        return await send_main_menu(message)

    pending_action = get_pending_action(message["sender_phone_number"])
    pending_selection = get_pending_selection(message["sender_phone_number"])
    if pending_selection:
        return await handle_text_selection(message, pending_selection)

    if pending_action == "list_debts":
        delete_pending_action(message["sender_phone_number"])
        if message["message_text"].strip().lower() == "todas":
            return await list_all_debts(message)
        return await list_debts_for_person(message, message["message_text"].strip())
    if pending_action == "create_debt":
        parsed_message = parse_message(message)
        if (
            parsed_message["entities"]["amount"] is None
            or parsed_message["entities"]["person"] is None
        ):
            await send_message(
                message["sender_phone_number"],
                "Envie o valor e o nome. Exemplo: \"500 Fabio\".",
            )
            return {"status": "invalid_create_debt_details", "payload": message}

        delete_pending_action(message["sender_phone_number"])
        parsed_message["intent"] = "CREATE_DEBT"
    else:
        parsed_message = parse_message(message)

    print(f"Parsed message: {parsed_message}")
            
    if parsed_message["intent"] == "REGISTER_PAYMENT":
        print(f"Received payment registration message from {message['name']}.")
        save_debt_to_database(
            owner_phone_number=message["sender_phone_number"],
            debtor_name=parsed_message["entities"]["person"],
            amount=parsed_message["entities"]["amount"],
            due_date=parsed_message["entities"]["due_date"],
            status="paid"
        )
        await send_message(
            f"{message['sender_phone_number']}",
            f"Olá, {message['name']}! O pagamento de {parsed_message['entities']['amount']} de {parsed_message['entities']['person']} foi registrado com sucesso."
        )
    elif parsed_message["intent"] == "LIST_DEBTS":
        return await list_debts_for_person(
            message,
            parsed_message["entities"]["person"],
        )

    elif parsed_message["intent"] == "CREATE_DEBT":
        person_choices = find_person_choices(
            message["sender_phone_number"],
            parsed_message["entities"]["person"],
        )
        if len(person_choices) > 1:
            return await ask_person_choice(
                message,
                action="create_debt",
                payload={
                    "amount": parsed_message["entities"]["amount"],
                    "due_date": parsed_message["entities"]["due_date"],
                },
                choices=person_choices,
            )
        if person_choices:
            parsed_message["entities"]["person"] = person_choices[0]
        due_date = parsed_message["entities"]["due_date"]
        save_pending_debt(
            sender_phone_number=message["sender_phone_number"],
            debtor_name=parsed_message["entities"]["person"],
            amount=parsed_message["entities"]["amount"],
            due_date=due_date,
        )
        await send_button_message(
            phone_number=message["sender_phone_number"],
            message=(
                f"Olá, {message['name']}! Você gostaria de confirmar a cobrança de "
                f"R${parsed_message['entities']['amount']:.2f} para "
                f"{parsed_message['entities']['person']}, com vencimento em "
                f"{format_due_date(due_date)}?"
            ),
            buttons=[
                {
                    "type": "reply",
                    "reply": {
                        "id": "confirm_create_debt",
                        "title": "Confirmar Dívida"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "decline_create_debt",
                        "title": "Recusar Dívida"
                    }
                }
            ]
        )

async def handle_debt_confirmation(message: dict):
    """Processes the confirmation button for the user's pending debt."""
    pending_debt = get_pending_debt(message["sender_phone_number"])

    if not pending_debt:
        await send_message(
            message["sender_phone_number"],
            "Não encontrei nenhuma cobrança pendente para confirmar.",
        )
        return {"status": "pending_debt_not_found", "payload": message}

    if message["button_payload"] == "confirm_create_debt":
        save_debt_to_database(
            owner_phone_number=message["sender_phone_number"],
            status="debt",
            **pending_debt,
        )
        delete_pending_debt(message["sender_phone_number"])
        response = (
            f"Olá, {message['name']}! A cobrança de "
            f"R${pending_debt['amount']:.2f} para {pending_debt['debtor_name']}, "
            f"com vencimento em {format_due_date(pending_debt['due_date'])}, "
            "foi registrada com sucesso."
        )
    elif message["button_payload"] == "decline_create_debt":
        delete_pending_debt(message["sender_phone_number"])
        response = "Tudo bem, a cobrança não foi registrada."
    else:
        return {"status": "unknown_button", "payload": message}

    await send_message(message["sender_phone_number"], response)
    return {"status": "confirmation_processed", "payload": message}


async def handle_paid_reminder(message: dict):
    try:
        debt_id = int(message["button_payload"].removeprefix("mark_paid_"))
    except ValueError:
        return {"status": "invalid_paid_reminder", "payload": message}

    updated = mark_debt_as_paid(
        debt_id=debt_id,
        owner_phone_number=message["sender_phone_number"],
    )
    response = (
        "Pagamento atualizado com sucesso!"
        if updated
        else "Não encontrei essa cobrança ou ela já foi atualizada."
    )
    await send_message(message["sender_phone_number"], response)
    return {"status": "paid_reminder_processed", "payload": message}


async def handle_person_selection(message: dict):
    try:
        index = int(message["button_payload"].removeprefix("select_person_"))
    except ValueError:
        return {"status": "invalid_person_selection", "payload": message}

    pending = get_pending_selection(message["sender_phone_number"])
    if not pending:
        await send_message(
            message["sender_phone_number"],
            "Essa escolha expirou. Envie oi para abrir o menu novamente.",
        )
        return {"status": "person_selection_not_found", "payload": message}

    choices = pending["payload"]["choices"]
    if index < 0 or index >= len(choices):
        return {"status": "invalid_person_selection", "payload": message}

    person = choices[index]
    delete_pending_selection(message["sender_phone_number"])
    if pending["action"] == "list_debts":
        return await list_debts_for_person(message, person)

    return await create_debt_from_selection(message, person, pending["payload"])


async def handle_text_selection(message: dict, pending: dict):
    normalized_text = normalize_name(message["message_text"])
    choices = pending["payload"]["choices"]
    matches = [
        choice for choice in choices if normalize_name(choice) == normalized_text
    ]
    if len(matches) != 1:
        await send_message(
            message["sender_phone_number"],
            "Escolha uma das opções exibidas nos botões.",
        )
        return {"status": "invalid_person_selection", "payload": message}

    delete_pending_selection(message["sender_phone_number"])
    if pending["action"] == "list_debts":
        return await list_debts_for_person(message, matches[0])
    return await create_debt_from_selection(
        message, matches[0], pending["payload"]
    )


async def create_debt_from_selection(
    message: dict, person: str, payload: dict
):
    save_pending_debt(
        sender_phone_number=message["sender_phone_number"],
        debtor_name=person,
        amount=payload["amount"],
        due_date=payload["due_date"],
    )
    await send_button_message(
        phone_number=message["sender_phone_number"],
        message=(
            f"Olá, {message['name']}! Você gostaria de confirmar a cobrança de "
            f"R${payload['amount']:.2f} para {person}, com vencimento em "
            f"{format_due_date(payload['due_date'])}?"
        ),
        buttons=[
            {"type": "reply", "reply": {
                "id": "confirm_create_debt", "title": "Confirmar Dívida"
            }},
            {"type": "reply", "reply": {
                "id": "decline_create_debt", "title": "Recusar Dívida"
            }},
        ],
    )
    return {"status": "debt_confirmation_requested", "payload": message}


async def handle_menu_selection(message: dict):
    instructions = {
        "menu_create_debt": (
            "Para cadastrar uma cobrança, envie algo como: "
            "\"O Fabio me deve 400 reais para daqui 30 dias\"."
        ),
        "menu_list_debts": (
            "Para listar as cobranças, envie o nome da pessoa. "
            "Exemplo: \"Quais são as dívidas do Fabio?\"."
        ),
        "menu_update_debt": (
            "A opção de atualizar cobrança ainda está em construção."
        ),
    }
    response = instructions.get(
        message["button_payload"],
        "Não reconheci essa opção. Envie oi para abrir o menu novamente.",
    )
    if message["button_payload"] == "menu_list_debts":
        save_pending_action(message["sender_phone_number"], "list_debts")
    elif message["button_payload"] == "menu_create_debt":
        save_pending_action(message["sender_phone_number"], "create_debt")

    await send_message(message["sender_phone_number"], response)
    return {"status": "menu_selection_processed", "payload": message}


async def list_debts_for_person(message: dict, person: str):
    person = person.strip().strip("?.!,").capitalize()
    person_choices = find_person_choices(
        message["sender_phone_number"],
        person,
    )
    if len(person_choices) > 1:
        return await ask_person_choice(
            message,
            action="list_debts",
            payload={},
            choices=person_choices,
        )
    if person_choices:
        person = person_choices[0]
    debts = get_debts_from_person(
        owner_phone_number=message["sender_phone_number"],
        debtor_name=person,
    )
    response_message = format_debts_message(
        name=message["name"],
        person=person,
        debts=debts,
    )
    await send_message(message["sender_phone_number"], response_message)
    return {"status": "debts_listed", "payload": message}


def normalize_name(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name)
    return "".join(
        char for char in normalized
        if not unicodedata.combining(char)
    ).casefold()


def find_person_choices(owner_phone_number: str, person: str) -> list[str]:
    normalized_person = normalize_name(person)
    return [
        name
        for name in get_debtor_names(owner_phone_number)
        if normalize_name(name) == normalized_person
    ]


async def ask_person_choice(
    message: dict,
    action: str,
    payload: dict,
    choices: list[str],
):
    payload = {**payload, "choices": choices}
    save_pending_selection(
        sender_phone_number=message["sender_phone_number"],
        action=action,
        payload=payload,
    )
    buttons = [
        {
            "type": "reply",
            "reply": {
                "id": f"select_person_{index}",
                "title": choice[:20],
            },
        }
        for index, choice in enumerate(choices[:3])
    ]
    await send_button_message(
        phone_number=message["sender_phone_number"],
        message="Encontrei mais de uma pessoa parecida. Qual delas você quis dizer?",
        buttons=buttons,
    )
    return {"status": "person_selection_requested", "payload": message}


async def list_all_debts(message: dict):
    debts = get_all_debts(message["sender_phone_number"])
    response_message = format_debts_message(
        name=message["name"],
        person="todas as pessoas",
        debts=debts,
    )
    await send_message(message["sender_phone_number"], response_message)
    return {"status": "all_debts_listed", "payload": message}


def is_greeting(text: str) -> bool:
    normalized_text = text.strip().lower().replace("á", "a")
    return bool(
        re.fullmatch(r"o+i+|o+l+a+|o+i+e+|hello", normalized_text)
    )


async def send_main_menu(message: dict):
    """
    Displays the available actions after a greeting.
    """
    await send_button_message(
        phone_number=message["sender_phone_number"],
        message=f"Olá, {message['name']}! O que você quer fazer hoje?",
        buttons=MENU_BUTTONS,
    )
    return {"status": "menu_sent", "payload": message}


def format_debts_message(name: str, person: str, debts: list) -> str:
    if not debts:
        return f"Olá, {name}! Não encontrei dívidas de {person}."

    lines = [
        f"Olá, {name}!",
        f"Estas são as dívidas de {person}:",
        ""
    ]
    total_open = sum(
        debt["amount"]
        for debt in debts
        if debt["status"] != "paid"
    )
    count = 1
    for debt in debts:
        status = {
            "debt": "Em aberto",
            "paid": "Pago",
        }.get(debt["status"], debt["status"] or "Pendente")
        lines.append(
            f"• Dívida #{count}\n"
            f"  Devedor: {debt['debtor_name']}\n"
            f"  Valor: R${debt['amount']:.2f}\n"
            f"  Vencimento: {format_due_date(debt['due_date'])}\n"
            f"  Status: {status}\n"
        )
        count += 1

    lines.append(f"Total em aberto: R${total_open:.2f}")
    return "\n".join(lines)


def format_due_date(due_date: str) -> str:
    try:
        return date.fromisoformat(due_date).strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return due_date