from database.connection import save_message_to_database
from services.whatsapp import send_message


async def message_received_handler(message:dict):
    """
    Handles incoming messages and sends a response.

    Args:
        message (str): The incoming message to handle.
    """
    # Process the incoming message and generate a response
    is_new_message = save_message_to_database(
                message_id=message["message_id"],
                sender_id=message["sender_id"],
                sender_phone_number=message["sender_phone_number"],
                message_text=message["message_text"]
            )
    if not is_new_message:
        print(f"Message with ID {message['message_id']} already exists in the database. Skipping processing.")
        return {"status": "duplicate", "payload": message}
            
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