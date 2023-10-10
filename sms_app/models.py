# django imports
from unicodedata import category
from django.db import models

# system imports 
import uuid
import json
import logging
import time
import datetime

LOGGER = logging.getLogger('friday_logger')

class Transaction(models.Model):
    """
    Class to save a single transaction
    """
    phone_number = models.CharField(max_length=12)
    title = models.CharField(max_length=100)
    transaction_cat = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    timestamp = models.DateTimeField()
    trans_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def make_transaction(phone_number, item, category, amount, location, timestamp):
        if item == '?':
            title = location
        elif location == '?':
            title = item
        else:
            title = '%s @ %s' % (item, location)

        try:
            date = datetime.datetime.strptime(timestamp, '%m-%d-%Y')

            if date.date() == datetime.date.today():
                timestamp = datetime.datetime.now()
            else:
                timestamp = datetime.datetime(date.year, date.month, date.day)
        except:
            timestamp = datetime.datetime.now()

        transaction = Transaction(phone_number=phone_number,
                                  title=title,
                                  transaction_cat=category,
                                  amount=amount,
                                  timestamp=timestamp)

        transaction.save()
        return transaction
        

class BudgetCategory(models.Model):
    """
    Class to save one budget category
    """
    category_name = models.CharField(max_length=100)
    budget_amount = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    cat_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

class ConvMsg(models.Model):
    """
    Class to save the conversation history of a user
    """
    FRIDAY = 'Friday'
    MESSAGE = 'Message'
    MEDIA = 'Media'

    # History is list stored as json, default empty list
    message = models.TextField()
    msg_type = models.CharField(max_length=20, default=MESSAGE)
    author = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=12)
    timestamp = models.DateTimeField(auto_now_add=True, editable=False)
    conv_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class User(models.Model):
    REG = 'Registration'
    SET = 'Modify budget category'
    DIS = 'Chat about anything'
    ABO = 'Info about app'
    INQ = 'Account inquiry'
    TRA = 'Track expense'
    ASK = 'Missing command need to elaborate'

    # Identification info
    name = models.CharField(max_length=50, blank=True)

    phone_number = models.CharField(max_length=12)

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # State of the conversation at that moment
    state = models.CharField(max_length=30, default=REG)

    # Conversation history for discussion only
    discuss_history = models.ManyToManyField(ConvMsg, related_name='discussion_history')

    # Complete conversation history
    conv_history = models.ManyToManyField(ConvMsg, related_name='conversation_history')

    # Budget Categories the user has
    budget_categories = models.ManyToManyField(BudgetCategory, related_name='budget_categories')

    # Transactions the user has
    transactions = models.ManyToManyField(Transaction, related_name='transactions')

    # -----------------------
    # Public Instance Methods
    # -----------------------

    ####################################
    # For modifying the discussion stack
    ####################################
    def add_discussion_msg(self, msg, sender):
        conv = ConvMsg(message=msg, author=sender, phone_number=self.phone_number)
        conv.save()
        self.discuss_history.add(conv)
        self.save()

    def add_discussion_media(self, media, sender):
        conv = ConvMsg(message=media,
                       msg_type=ConvMsg.MEDIA,
                       author=sender,
                       phone_number=self.phone_number)
        conv.save()

        self.discuss_history.add(conv)
        self.save()

    def get_discussion(self):
        in_discussion_set = set(self.discuss_history.all())
        curated_discussion_list = list()

        # Create list for the discussion
        for conv_item in in_discussion_set:
            msg = conv_item.message
            author = conv_item.author
            timestamp = conv_item.timestamp
            curated_discussion_list.append({'Timestamp': timestamp,
                                            'Author': author, 'Message': msg})
        
        # sort the curated discussion list by time
        curated_discussion_list.sort(key=lambda x:x['Timestamp'])

        return curated_discussion_list

    ##############################################
    # For modifying the conversation history stack
    ##############################################
    def add_conversation_msg(self, msg, sender):
        conv = ConvMsg(message=msg, author=sender, phone_number=self.phone_number)
        conv.save()
        self.conv_history.add(conv)
        self.save()

    def add_conversation_media(self, media, sender):
        conv = ConvMsg(message=media,
                       msg_type=ConvMsg.MEDIA,
                       author=sender,
                       phone_number=self.phone_number)
        conv.save()

        self.conv_history.add(conv)
        self.save()

    def get_conversation(self):
        in_conversation_set = set(self.conv_history.all())
        curated_conversation_list = list()

        # Create list for the discussion
        for conv_item in in_conversation_set:
            msg = conv_item.message
            author = conv_item.author
            timestamp = conv_item.timestamp
            curated_conversation_list.append({'Timestamp': timestamp,
                                            'Author': author, 'Message': msg})
        
        # sort the curated discussion list by time
        curated_conversation_list.sort(key=lambda x:x['Timestamp'])

        return curated_conversation_list

    #####################################
    # For modifying the budget categories
    #####################################
    def setup_default_categories(self):
        # Setup categories and put them into the user information
        categories = []
        categories.append(BudgetCategory(category_name="Housing"))
        categories.append(BudgetCategory(category_name="Transportation"))
        categories.append(BudgetCategory(category_name="Food"))
        categories.append(BudgetCategory(category_name="Entertainment"))
        categories.append(BudgetCategory(category_name="Supplies"))
        categories.append(BudgetCategory(category_name="Clothing"))
        categories.append(BudgetCategory(category_name="Health"))

        for item in categories:
            item.save()
            self.budget_categories.add(item)
            self.save()

    def get_category_amount_dict(self):
        categories = set(self.budget_categories.all())
        # Set of categories to return
        out_category_dict = dict()

        for category in categories:
            amount = float(category.budget_amount)
            if amount == 0:
                amount = "N/A"
            out_category_dict[category.category_name] = str(amount)
        
        return out_category_dict

    def get_category_info_list(self, month):
        categories = set(self.budget_categories.all())
        # Set of categories to return
        out_category_list = list()

        total_spent = 0
        total_left = 0
        total_budget = 0

        for category in categories:
            info_dict = dict()
            amount = float(category.budget_amount)
            category_name = category.category_name
            spent = float(self.get_transactions_total(month, category_name))
            info_dict['Category'] = category_name
            info_dict['Spent'] = spent
            if amount != 0:
                left = amount - spent

                total_spent += spent
                total_budget += amount
                total_left += left

                if left < -50:
                    status = 'Severely over budget'
                elif left < 0:
                    status = 'Slightly over budget'
                elif left < 20:
                    status = 'Approaching budget'
                else:
                    status = 'Safe'
            
                if left < 0:
                    left = 0

                info_dict['Allocated Budget'] = amount
                info_dict['Left to spend'] = left
                info_dict['Status'] = status
            
            out_category_list.append(info_dict)

        if total_left < -50:
            overall_status = 'Severely over budget'
        elif total_left < 0:
            overall_status = 'Slightly over budget'
        elif total_left < 20:
            overall_status = 'Approaching budget'
        else:
            overall_status = 'Safe'
        
        if total_left < 0:
            total_left = 0

        return out_category_list, total_spent, total_left, total_budget, overall_status

    def get_category_names_list(self):
        categories = set(self.budget_categories.all())
        # Set of categories to return
        out_category_list = list()

        for category in categories:
            out_category_list.append(category.category_name)
        
        return out_category_list
    
    def modify_categories_from_dict(self, category_dict):
        for cat in self.budget_categories.all():
            cat.delete()
        self.budget_categories.clear()
        for name, amount in category_dict.items():
            if amount == 'N/A':
                category = BudgetCategory(category_name=name)
            else:
                amount = float(amount)
                category = BudgetCategory(category_name=name, budget_amount=amount)
            category.save()
            self.budget_categories.add(category)
            self.save()

    ##############
    # Transactions
    ##############
    def add_transaction(self, transaction):
        """
        Adds the transaction to the user
        """
        self.transactions.add(transaction)
        self.save()

    def get_recent_transactions_dict(self, month, category):
        """
        Gets recent transactions in a list of dict elements
        """
        transaction_list = list()

        # Find all the transactions in that category
        # If all, then get all transactions
        transaction_query_set = self.transactions.all()

        for transaction in transaction_query_set:
            date = transaction.timestamp
            transaction_cat = transaction.transaction_cat
            if category == 'All':
                pass
            elif category != transaction_cat:
                continue
            if date.date().month == month:
                pass
            else:
                continue

            title = transaction.title
            amount = transaction.amount
            transaction_list.append({'Title': title,
                                     'Amount': amount,
                                     'Category': transaction_cat,
                                     'Date': date.date(),
                                     'DateTime': date})
        
        transaction_list.sort(key=lambda x:x['Date'])

        return transaction_list
            
    def get_transactions_total(self, month, category):
        """
        Gets recent transactions in a list of dict elements
        """
        total = 0

        # Find all the transactions in that category
        # If all, then get all transactions
        transaction_query_set = self.transactions.all()

        for transaction in transaction_query_set:
            transaction_cat = transaction.transaction_cat
            date = transaction.timestamp
            if category == 'All':
                pass
            elif category != transaction_cat:
                continue

            if date.date().month == month:
                pass
            else:
                continue

            total += transaction.amount
        
        return total

    # -----------------------
    # Static Public functions
    # -----------------------

    def find_user_from_phone(phone_num):
        """
        Tries to find using phone num, returns None if not found
        """
        try:
            user = User.objects.get(phone_number=phone_num)
        except:
            return None

        return user

