import asyncio

from database.connection import get_debts_ready_for_reminder, mark_reminder_sent
from services.whatsapp import send_button_message

REMINDER_INTERVAL_SECONDS = 60


async def send_due_debt_reminders() -> None:
    for debt in get_debts_ready_for_reminder():
        result = await send_button_message(
            phone_number=debt["owner_phone_number"],
            message=(
                f"Olá! Lembrete: você tem uma cobrança de "
                f"R${debt['amount']:.2f} para {debt['debtor_name']}. "
                "Essa cobrança já foi paga?"
            ),
            buttons=[
                {
                    "type": "reply",
                    "reply": {
                        "id": f"mark_paid_{debt['id']}",
                        "title": "Já pagou",
                    },
                }
            ],
        )
        if "error" not in result:
            mark_reminder_sent(debt["id"], debt["owner_phone_number"])


async def reminder_worker() -> None:
    while True:
        await send_due_debt_reminders()
        await asyncio.sleep(REMINDER_INTERVAL_SECONDS)
