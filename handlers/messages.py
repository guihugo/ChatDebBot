from database.connection import get_debts_from_person, save_debt_to_database, save_message_to_database
from parser.message_parser import parse_message
from services.whatsapp import send_message


async def message_received_handler(message:dict):
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

    parsed_message = parse_message(message)

    print(f"Parsed message: {parsed_message}")
            
    if parsed_message["intent"] == "REGISTER_PAYMENT":
        print(f"Received payment registration message from {message['name']}.")
        save_debt_to_database(
            debtor_name=parsed_message["entities"]["person"],
            amount=parsed_message["entities"]["amount"],
            due_date="2023-12-31",  # Replace with actual due date
            status="paid"
        )
        await send_message(
            f"{message['sender_phone_number']}",
            f"Olá, {message['name']}! O pagamento de {parsed_message['entities']['amount']} de {parsed_message['entities']['person']} foi registrado com sucesso."
        )
    elif parsed_message["intent"] == "LIST_DEBTS":
        print(f"Received debt listing message from {message['name']}.")
        debts = get_debts_from_person(parsed_message["entities"]["person"])
        print(f"Debts for {parsed_message['entities']['person']}: {debts}")

        print("Sending message!")
        response_message = format_debts_message(
            name=message["name"],
            person=parsed_message["entities"]["person"],
            debts=debts
        )
        await send_message(message["sender_phone_number"], response_message)

    elif parsed_message["intent"] == "CREATE_DEBT":
        save_debt_to_database(
                    debtor_name=parsed_message["entities"]["person"],
                    amount=parsed_message["entities"]["amount"],
                    due_date="2023-12-31",  # Replace with actual due date
                    status="debt"
                )
        await send_message(
            f"{message['sender_phone_number']}",
            f"Olá, {message['name']}! A dívida de {parsed_message['entities']['amount']} com {parsed_message['entities']['person']} foi registrada com sucesso."
        )


    if message["message_text"].lower() == "oi":
        print(f"Received 'Oi' message from {message['name']}.")
        await send_first_message(message['name'], message['sender_phone_number'])

async def send_first_message(name: str, phone_number: str):
    """
    Sends the first message to the user using the WhatsApp API.

    Args:
        name (str): The name of the user.
        phone_number (str): The phone number of the user.
    """
    print(f"Sending first message to: {name}, phone_number: {phone_number}")
    
    await send_message(f"{phone_number}", f"Olá, {name}! Obrigado por entrar em contato. Como posso ajudá-lo hoje?")


def format_debts_message(name: str, person: str, debts: list) -> str:
    if not debts:
        return f"Olá, {name}! Não encontrei dívidas de {person}."

    lines = [
        f"Olá, {name}!",
        f"Estas são as dívidas de {person}:",
        ""
    ]

    for debt in debts:
        lines.append(
            f"• Dívida #{debt['id']}\n"
            f"  Valor: R${debt['amount']:.2f}\n"
            f"  Vencimento: {debt['due_date']}\n"
            f"  Status: {debt['status']}"
        )

    return "\n".join(lines)