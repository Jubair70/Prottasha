import decimal
import simplejson
#from distutils.command.config import config
#from mercurial.dispatch import request

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from django.db.models import ProtectedError
from django.db import connection
from django.db.models import Max, Sum
import json
from datetime import *
from collections import OrderedDict
import re

# *************************** Utility Functions *****************************************


"""
Prepare Message for Ajax request message
@persia
"""


def getAjaxMessage(type, message):
    data = {}
    data['type'] = type
    data['messages'] = message
    return data



'''
utility function for running raw queries
'''

def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall()
    cursor.close()
    return fetchVal


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchone()
    cursor.close()
    return fetchVal[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def run_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def unicodoToString(tup):
   if isinstance(str(tup), unicode):
      return json.dumps(tup)
   else:
       return tup 
   return json.dumps(tup)


def replace_all(text, dic):
    for i, j in dic.iteritems():
        text = text.replace(i, j)
    return text

def get_filtered_query(post_dict, query):
    '''
     Final Executable Query Generator
    :param post_dict: Filtered Option with value
    :param query: Query with Filtering Option
    :return: final executable query

    EXAMPLE QUERY WITH ID FILTERING:
    Initial State : select * from logger_xform where (id::text=@id or @id is NULL)
    After select id 375: select * from logger_xform where (id::text='375' or '375' is NULL)
    IF Noting Selected": select * from logger_xform where (id::text=NULL or NULL is NULL)
    '''

    keyward_param = ""

    #Filtering Options need to be replaced in query
    #print post_dict
    for key in post_dict:

	##########zinia#########
	store_param = "@st_"+key
        param_val = post_dict.getlist(key)
        if store_param in query:
            if len(param_val) == 1:
                param_val = post_dict.get(key)
                if param_val:
                    param_val = "'" + post_dict.get(key) + "'"
            # OTHERWISE: MULTIPLE VAlUE
            else:
                coated_param_val = []
                for val in param_val:
                    coated_param_val.append(val)
                param_val = ",".join(coated_param_val)
                param_val ="'"+param_val+"'"

            query = query.replace(store_param, param_val)

        keyward_param = "@" + key
        param_val =post_dict.getlist(key)
        #print post_dict.get(key)

        #IF SINGLE VAlUE
        if len(param_val)==1:
            param_val = post_dict.get(key)
            if param_val:
                param_val="'"+ post_dict.get(key)+"'"
        #OTHERWISE: MULTIPLE VAlUE
        else :
            coated_param_val=[]
            for val in param_val:
                coated_param_val.append("'"+val+"'")
            param_val=",".join(coated_param_val)

        if keyward_param in query and param_val:
            #print keyward_param, "  ", param_val
            query = query.replace(keyward_param, param_val)

        keyward_param="@col_"+key
        if keyward_param in query:
            #print keyward_param, "  ", post_dict.get(key)
            query = query.replace(keyward_param, post_dict.get(key))

    #Left over @name need to be replace with NULL
    words_starting_with_at = re.findall(r'@\w+', query)
    for w in words_starting_with_at:
        query=query.replace(w, 'NULL')

    #print query
    return query
