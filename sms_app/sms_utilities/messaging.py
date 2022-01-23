# twilio imports
from twilio.rest import Client

# System imports
import urllib.parse
import os

# local imports

# Twillio setup
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_NUMBER = os.getenv('TWILIO_NUMBER')
TWILIO_CLIENT = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def decode_request(request):
    """
    Decodes the POST request from the app
    """
    return urllib.parse.parse_qs(request.body.decode('utf-8'))

def send_message(msg, phone_num):
    """
    Constructs a response message json for API to send back
    """
    response = TWILIO_CLIENT.messages.create(
            body=msg,
            to=phone_num,
            media_url=None,
            from_=TWILIO_NUMBER
            )
