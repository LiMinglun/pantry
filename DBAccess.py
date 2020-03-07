import logging
import ask_sdk_core.utils as ask_utils
import os
import boto3

from boto3.dynamodb.conditions import Key
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from datetime import date
import datetime
from random import seed
from random import randint

class DBStorage():
    DB_ID =
    DB_KEY =
    def get_exp_date_str(date, food):
        return_val = {"type":"", "val":""}
        client = boto3.resource('dynamodb',aws_access_key_id=DBStorage.DB_ID, aws_secret_access_key=DBStorage.DB_KEY, region_name='us-east-2')
        table = client.Table('food_name')
        response = table.get_item(Key={'food_name': food})
        if (len(response) == 1):
            try: # connect secondary server
                table = client.Table('users_created')
                response = table.query(
                    KeyConditionExpression=Key('food_name').eq(food)
                )
                response = sorted(response['Items'], key = lambda x: int(x['vote']), reverse = True)[0]
                expiration = int(response['duration'])
                base_date = datetime.datetime.strptime(date, "%Y-%m-%d")
                exp_date = base_date + datetime.timedelta(days=expiration)
                exp_date_str = exp_date.strftime("%Y-%m-%d")
                print(response['vote'])
                if (int(response['vote']) > 0):
                    return_val = {"type" : "sys", "val": exp_date_str}
                else:
                    return_val = {"type" : "bad", "val" : ""}
            except Exception as e:
                return_val = {"type" : "bad", "val" : ""}
            return return_val
        else:
            food_category = response['Item']['category']
            table = client.Table('duration')
            response = table.get_item(Key={'category': food_category})
            expiration = int(response['Item']['fridge'])
            base_date = datetime.datetime.strptime(date, "%Y-%m-%d")
            exp_date = base_date + datetime.timedelta(days=expiration)
            exp_date_str = exp_date.strftime("%Y-%m-%d")
            return_val = {"type" : "sys", "val": exp_date_str}
            return return_val

    def set_duration_dur(duration, food):
        duration = str(duration)
        client = boto3.resource('dynamodb',aws_access_key_id=DBStorage.DB_ID, aws_secret_access_key=DBStorage.DB_KEY, region_name='us-east-2')
        table = client.Table('users_created') #secondary table
        response = table.get_item(Key={'food_name': food, 'duration': duration})
        if (len(response) == 1):
            table.put_item(
                Item={
                    'food_name': food,
                    'duration': duration,
                    'vote': '1',
                }
            )
        else:
            try:
                vote = str(int(response['Item']['vote']) + 1)
                table.update_item(
                    Key = {
                        'food_name': food,
                        'duration': duration,
                    },
                    UpdateExpression='SET vote = :val1',
                    ExpressionAttributeValues={
                        ':val1': vote
                    }
                )
            except Exception as e:
                return False
        return True

class Storage():
    def __init__(self, attr_manager):
        self.internal_arr = {}
        self.manager = attr_manager
        temp = self.manager.persistent_attributes
        if (len(temp) != 0):
            self.internal_arr = temp
 
    def set_exp(self, food_name, exp_date):
        if (food_name not in self.internal_arr):
            return False
        self.internal_arr[food_name]["exp_date"] = exp_date
        self.manager.persistent_attributes = self.internal_arr
        self.manager.save_persistent_attributes()
        return True
 
    def add_food(self, food_name, exp_date, in_fridge):
        return_flag = True
        if (food_name in self.internal_arr):
            return_flag = False
        self.internal_arr[food_name] = {"exp_date": exp_date, "fridge": in_fridge}
        self.manager.persistent_attributes = self.internal_arr
        self.manager.save_persistent_attributes()
        return return_flag
    
    def delete_food(self, food_name):
        if (food_name not in self.internal_arr):
            return False
        self.internal_arr.pop(food_name, None)
        self.manager.persistent_attributes = self.internal_arr
        self.manager.save_persistent_attributes()
        return True
 
    def get_exp_date(self, food_name):
        if (food_name not in self.internal_arr):
            return ""
        return self.internal_arr[food_name]["exp_date"]
 
    def get_all(self):
        return self.internal_arr
