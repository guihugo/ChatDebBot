from services.whatsapp import send_message


async def send_first_message(name: str, phone_number: str):
    """
    Sends the first message to the user using the WhatsApp API.

    Args:
        name (str): The name of the user.
        phone_number (str): The phone number of the user.
    """
    print(f"Sending first message to: {name}, phone_number: {phone_number}")
    
    await send_message(f"{phone_number}", f"Olá, {name}! Obrigado por entrar em contato. Como posso ajudá-lo hoje?")