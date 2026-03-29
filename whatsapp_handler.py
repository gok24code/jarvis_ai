from twilio.rest import Client
from config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER, log

class WhatsAppHandler:
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None

    def send_message(self, to_number, message_text):
        """
        Sends a WhatsApp message to the specified number.
        to_number: Recipient's phone number in E.164 format (e.g., +1234567890)
        message_text: The message to be sent.
        """
        if not self.client:
            log("Twilio client is not initialized. Check your credentials in .env file.")
            return False

        try:
            # Ensure the number starts with whatsapp:
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            from_number = TWILIO_WHATSAPP_NUMBER
            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"

            message = self.client.messages.create(
                body=message_text,
                from_=from_number,
                to=to_number
            )
            log(f"WhatsApp message sent to {to_number}. SID: {message.sid}")
            return True
        except Exception as e:
            log(f"Failed to send WhatsApp message: {e}")
            return False

    def send_to_recipients(self, recipients, message_text):
        """
        Sends a message to multiple recipients.
        recipients: A list of phone numbers.
        """
        results = []
        for recipient in recipients:
            success = self.send_message(recipient, message_text)
            results.append((recipient, success))
        return results
