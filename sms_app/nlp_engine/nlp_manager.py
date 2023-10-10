# System imports
import logging
import datetime

# local imports
from sms_app.nlp_engine.default_responses import *
from sms_app.models import *
import sms_app.gpt3_utilities.response_utilities as gpt3

LOGGER = logging.getLogger('friday_logger')

class NLP_Manager(object):
    MESSAGE = 'Message'
    MEDIA = 'Media'

    def __init__(self, user):
        """Constructor"""
        self.user = user

        self.reply_queue = list()

    # -----------------------
    # Static Public functions
    # -----------------------

    def get_first_time_greeting_msg():
        """Returns greeting for first time users"""
        msg = ("Hi there! This is Friday, your friendly budgeting assistant.")
        return msg
        
    def get_name_prompt_msg():
        """
        Returns a prompt for the user's name
        """
        msg = "I don\'t recognize this phone number, how should I refer to you?"
        return msg

    # ------------------------------
    # Public Interface for responses
    # ------------------------------
    def process_message(self, received_msg):
        """
        Main function for decifering a response from the user
        """
        # if in registration mode
        if self.user.state == User.REG:
            # Try and find name in response
            name = gpt3.find_name_from_msg(received_msg)

            # if message contains no name reprompt
            if name is None or name == 'Friday':
                msg = self._get_reprompt_for_name()
                self._add_reply_msg(msg)
                return

            # Add name to the user
            self.user.name = name
            # Change to any state, will change after
            self.user.state = User.ABO
            # Setup Budgetting categories
            self.user.setup_default_categories()

            self.user.save()

            msgs = self._get_onboarding_messages()
            for msg in msgs:
                self._add_reply_msg(msg)
            return

        # Add the user msg to conversation hist
        self.user.add_conversation_msg(received_msg, self.user.name)

        # A classification function that determines the user state
        self.user.state = gpt3.determine_conversation_category(received_msg)

        if self.user.state == User.SET:
            LOGGER.info('You are now in setup')
            msg = self._perform_setup_and_get_response(received_msg)
            self._add_reply_msg(msg)
            return

        elif self.user.state == User.DIS:
            LOGGER.info('You are now in discussion')
            msg = self._get_discussion_response(received_msg)
            self._add_reply_msg(msg)
            return

        # NOTE: Disabled for now, wasn't working well
        elif self.user.state == User.ABO:
            LOGGER.info('You are now in about')
            msg = gpt3.get_about_response(received_msg, self.user.name)
            self._add_reply_msg(msg)
            return

        elif self.user.state == User.INQ:
            LOGGER.info('You are now in inquiry')
            #Once we're in this category we need to determine whether the user wants a text response or visual response
            msg = self._get_inquiry_response(received_msg)
            self._add_reply_msg(msg)
            return
        
        elif self.user.state == User.TRA:
            LOGGER.info('You are now in transaction')
            # Once we are in this state we need to determine the category of the transaction that took place.
            msg, num = self._extract_transaction_info(received_msg)
            self._add_reply_msg(msg)
            if num != 0:
                msg2 = self._get_inquiry_response('Show me my transaction history')
                self._add_reply_msg(msg2)
            return

        # NOTE: Disabled for now, wasn't working well in this spot
        elif self.user.state == User.ASK:
            LOGGER.info('You are now in ask')
            msg = gpt3.get_elaboration_response(received_msg, self.user.name)
            self._add_reply_msg(msg)
            return


        # otherwise
            # Send greeting if first text of the day
            # discover the intent of the user
            # generate response

        # process response

    def get_response(self):
        """
        Returns the reply_queue
        """
        return self.reply_queue

    # ------------------------
    # Private helper functions
    # ------------------------

    #############################
    # Tools modifying reply_queue
    #############################
    def _add_reply_msg(self, msg):
        """
        Adds reply message to the reply queue
        """
        self.reply_queue.append((self.MESSAGE, msg))
        self.user.add_conversation_msg(msg, ConvMsg.FRIDAY)

    def _add_reply_media(self, media):
        """
        Adds reply media to the reply queue
        """
        self.reply_queue.append((self.MEDIA, media))
        # TODO: Don't add this in just yet, the app might not know what to do with it
        # self.user.add_conversation_msg(media, ConvMsg.FRIDAY)

    
    #################
    # Searching tools
    #################

    ######################
    # Categorization tools
    ######################

    ##########################
    # Budget setup
    ##########################
    def _perform_setup_and_get_response(self, msg):
        """
        Determine the type of change to the data it needs to make and
        make the associated change
        """
        intent = gpt3.determine_user_setup_intent(msg)
        if intent == 'Unclear':
            reply = gpt3.get_elaboration_response(msg, self.user.name)
            return reply
        elif intent == 'Change budget':
            # Get the budget dict from database
            in_category_dict = self.user.get_category_amount_dict()
            category_dict = gpt3.get_budget_response(msg, in_category_dict, self.user.name)
            if category_dict is None:
                reply = gpt3.get_elaboration_response(msg, self.user.name)
                return reply
            
            self.user.modify_categories_from_dict(category_dict['Categories'])
            reply = category_dict['Response']
            return reply
            
    ##########################
    # Transaction Info Tools
    ##########################
    def _extract_transaction_info(self, msg):
        """
        Log Transactions into expense records
        """
        info = gpt3.determine_transaction_info(msg)
        if info is None:
            reply = "Your transaction was not very clear... please tell me where you spent your money and how much."
            return reply
        for transaction in info:
            item = transaction['Item']
            location = transaction['Location']
            amount = transaction['Amount']
            time = transaction['Date']
            category_type = gpt3.determine_transaction_type(item, self.user.get_category_names_list())
            transaction['Category'] = category_type

            # Determine Bad transactions
            if (item == '?' and location == '?') or amount == '?':
                reply = "Your transaction was not very clear... please tell me where you spent your money and how much."
                return reply, 0


            transaction_obj = Transaction.make_transaction(self.user.phone_number,
                                                           item, category_type, amount,
                                                           location, time)
            self.user.add_transaction(transaction_obj)

        num_transactions = len(info)
        if num_transactions == 1:
            keyword = "transaction"
        else:
            keyword = "transactions"

        reply = "Awesome! I've logged %s %s into your expense records." % (num_transactions, keyword)
        return reply, num_transactions
            
    #############################
    # Expense Inquiry Tools
    #############################
    def _get_inquiry_response(self, msg):
        """
        Determine if the inquiry is visual or text based
        """
        msgs = []
        #inquiry_type = gpt3.determine_inquiry_type(msg)
        #if inquiry_type == "Visual":
        #    # send it to function that spits out all visual insights
        #    msgs.append(gpt3.get_visuals())

        #else:
        #    # send it to function that spits text response
        #    #TODO By Ridvan
        #    pass
        
        ##
        ##reply = 
        budget_list, total_spent, total_left, total_budget, overall_status = self.user.get_category_info_list(datetime.datetime.now().date().month)
        trans_hist = self.user.get_recent_transactions_dict(datetime.datetime.now().date().month, 'All')
        reply = gpt3.get_inquiry_response_alt(self.user.name, msg, budget_list, total_spent, total_left, total_budget, trans_hist, overall_status)

        return reply

    ###############################
    # Tools for generating Messages
    ###############################

    # Registration
    def _get_reprompt_for_name(self):
        """
        Try to decifer message to find name, if not found return None
        """
        msg = "I'm sorry, I don't think I understood. What would you like me to call you?"
        return msg

    # Onboarding
    def _get_category_info(self):
        """
        Sends string that contains all the categories and their allocated budget
        """
        category_dict = self.user.get_category_amount_dict()

        msg = 'Here are your categories:\n'

        for name, budget in category_dict.items():
            if budget == 'N/A':
                msg += '%s\n' % name
            else:
                msg += '%s : $%s\n' % (name, str(budget))
        
        return msg

    def _get_onboarding_messages(self):
        """
        Sends an onboarding message that describes what the API does
        """
        msgs = []
        msgs.append("Alright %s, you're all setup!\n"
                    "I am here to help you with all of your budgeting needs.\n" % self.user.name)

        msgs.append("I can help you with tracking your spending, allocating budgets, setting up "
                    "categories for budgeting, visualizing your spending with graphs, and giving reports on your spending.\n")
        msgs.append("I can also have helpful discussions about budgeting and finance with you and "
                    "provide inspiration when it comes to financial matters.")
        msgs.append("I have set you up with a few default categories for now, "
                    "you can tell me to set or adjust the budget but you don't have to.")
        msgs.append(self._get_category_info())
        msgs.append("How can I help %s?" % self.user.name)
        return msgs

    # Discussion
    def _get_discussion_response(self, msg):
        """
        Sends msg to openAI and get a response back
        """
        # Add user message to discussion hist
        # NOTE: Don't need
        # self.user.add_discussion_msg(msg, self.user.name)
        # Decode discussion history into dictionary list
        conversation_list = self.user.get_conversation()
        # Send past 20 discussion history items to the API
        response_msg = gpt3.get_discussion_response(conversation_list[-20:], self.user.name)
        # Add friday message to discussion hist
        # NOTE: Don't need
        # self.user.add_discussion_msg(response_msg, ConvMsg.FRIDAY)
        return response_msg
