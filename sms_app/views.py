# Django imports
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

# System imports
import logging
import urllib.parse
import json

# local imports 
import sms_app.sms_utilities.messaging as msgutil
from sms_app.models import User
from sms_app.nlp_engine.nlp_manager import NLP_Manager

LOGGER = logging.getLogger('friday_logger')

@csrf_exempt
def receive_msg(request):
    if request.method == 'POST':
        # decode and process request
        sms = msgutil.decode_request(request)
        phone_num = sms['From'][0]
        msg = sms['Body'][0]

        reply = process_msg(msg, phone_num)

    response = json.dumps([{'Success': 'Message sent successfully!'}])

    return HttpResponse(response, content_type='text/json')

def process_msg(received_msg, phone_num):
    # Find the user
    user = User.find_user_from_phone(phone_num)

    # if user can't be found
    if user is None:
        # Prompt for username
        msg = NLP_Manager.get_first_time_greeting_msg()
        send_msg(msg, phone_num)
        msg = NLP_Manager.get_name_prompt_msg()
        send_msg(msg, phone_num)

        # Create temp username with temp ID
        user = User(phone_number=phone_num, state=User.REG)
        user.save()
        return

    # if phone number is found

    # Initiate nlp manager with the user
    nlp_manager = NLP_Manager(user)

    LOGGER.info(received_msg)

    nlp_manager.process_message(received_msg)

    reply_queue = nlp_manager.get_response()

    for msg_type, reply in reply_queue:
        if msg_type == NLP_Manager.MESSAGE:
            LOGGER.info(reply)
            send_msg(reply, phone_num)
        elif msg_type == NLP_Manager.MEDIA:
            #TODO: send media
            pass



    #TODO: Integrate with OPENAI

def send_msg(msg, phone_num):
    msgutil.send_message(msg, phone_num)

