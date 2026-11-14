def message_status_handler(status: dict):
    print(f"Message ID: {status['id']}")
    print(f"Status: {status['status']}")
    print(f"Recipient: {status['recipient_id']}")