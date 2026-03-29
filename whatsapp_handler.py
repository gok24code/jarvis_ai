import webbrowser
import pyautogui
import time
import os
import urllib.parse
from config import log

class WhatsAppHandler:
    def __init__(self):
        # WhatsApp Desktop uses the 'whatsapp://' protocol on Windows.
        pass

    def send_message(self, to_number, message_text):
        """
        Sends a WhatsApp message using the WhatsApp Desktop application URI.
        to_number: Recipient's phone number (E.164 format, e.g., +905xxxxxxxxx)
        message_text: The message content.
        """
        try:
            # Clean the number: remove 'whatsapp:' and '+' for the URI
            clean_number = to_number.replace("whatsapp:", "").replace("+", "").replace(" ", "").strip()
            
            log(f"Triggering WhatsApp Desktop for {clean_number}...")

            # URL encoding the message content
            encoded_message = urllib.parse.quote(message_text)
            
            # This URI format opens WhatsApp Desktop directly to the chat with the number
            # and pre-fills the message box.
            # For some versions, the URI is 'whatsapp://send?phone=NUMBER&text=MESSAGE'
            whatsapp_url = f"whatsapp://send?phone={clean_number}&text={encoded_message}"
            
            # Use webbrowser.open which is often more reliable for URI protocols
            webbrowser.open(whatsapp_url)
            
            # Wait for the app to open and focus (adjustable)
            # Desktop app might take time to load the chat.
            log("Waiting 8 seconds for WhatsApp Desktop to focus...")
            time.sleep(8)
            
            # Simulate 'Enter' key press to send the message.
            pyautogui.press('enter')
            
            log(f"WhatsApp Desktop command sent to {clean_number}.")
            return True
        except Exception as e:
            log(f"Failed to send WhatsApp message via Desktop app: {e}")
            print(f"[ERROR]: WhatsApp Desktop send failed: {e}")
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
            time.sleep(5)
        return results
