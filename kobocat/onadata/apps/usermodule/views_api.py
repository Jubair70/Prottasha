#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (
    HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
# from django.utils import simplejson
import json
import decimal
import numpy as np

from django.db import (IntegrityError, transaction)
from django.db.models import ProtectedError
from django.shortcuts import redirect
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.usermodule.forms import UserForm, UserProfileForm, ChangePasswordForm, UserEditForm, OrganizationForm, \
    ResetPasswordForm
from onadata.apps.usermodule.models import UserModuleProfile, UserPasswordHistory, UserFailedLogin, Organizations

from onadata.apps.usermodule.models import OrganizationRole, MenuRoleMap, UserRoleMap

from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import pandas
from django.shortcuts import render
from collections import OrderedDict

from django.core.files.storage import FileSystemStorage
import string
import random
import zipfile
import time
from django.conf import settings
import os

from django.core.mail import send_mail, BadHeaderError
import smtplib
from onadata.apps.usermodule import views



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


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def decimal_date_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return obj
    raise TypeError

@csrf_exempt
def update_token(data):
    mac_address = data['mac_address']
    firebase_token = data['firebase_token']
    username = data['username']
    user_id = __db_fetch_single_value("select id from auth_user where username ='"+str(username)+"'")

    # check query if this mac addr and user exists
    check_query = "select id from user_device_map where mac_address = '"+str(mac_address)+"' and user_id = '"+str(user_id)+"' "
    df = pandas.DataFrame()
    df = pandas.read_sql(check_query,connection)
    if df.empty:
        # check query if this mac addr exists
        # if exist, replace the user id
        chk_qry = "select id from user_device_map where mac_address = '"+str(mac_address)+"'"
        df1 = pandas.DataFrame()
        df1 = pandas.read_sql(chk_qry,connection)

        if df1.empty:
            query = "INSERT INTO public.user_device_map( user_id,mac_address, firebase_token, created_at) VALUES ('" + str(user_id) + "' ,'" + str(mac_address) + "', '" + str(firebase_token) + "', now())"
        else:
            query = "update user_device_map set user_id='" + str(user_id) + "', created_at = now() where mac_address = '" + str(mac_address) + "'"
    else:
        id = df.id.tolist()[0]
        query = "update user_device_map set firebase_token='" + str(firebase_token) +  "', created_at = now() where mac_address = '" + str(mac_address) + "' and user_id = '"+str(user_id)+"'"
    __db_commit_query(query)
    return HttpResponse(json.dumps('Token updated'), status=200)

@csrf_exempt
def mobile_login(request):
    '''
    receives username and password and returns 200 if valid
    '''
    json_string = request.body
    data = json.loads(json_string)
    error_mes = {}

    if data:

        m_username = data['username']
        m_password = data['password']
        user = authenticate(username=m_username, password=m_password)
        if user:
            mobile_response = {}
            user = User.objects.get(username=m_username)
            user_profile = UserModuleProfile.objects.get(user_id=user.id)
            if not user.is_active:
                error_mes['code'] = 403
                error_mes['message'] = 'Your User account is disabled.'
                return HttpResponse(json.dumps(error_mes), status=403)
            role = ""
            role_q = "select (select role from usermodule_organizationrole where id = usermodule_userrolemap.role_id limit 1) role_name from usermodule_userrolemap where user_id = "+str(user_profile.id)+" limit 1"
            cursor = connection.cursor()
            cursor.execute(role_q)
            fetchVal = cursor.fetchone()
            if fetchVal:
                role = fetchVal[0]
            cursor.close()
            mobile_response['username'] = m_username
            mobile_response['name'] = user.first_name + " " + user.last_name
            mobile_response['email'] = user.email
            mobile_response['password'] = m_password

            mobile_response['role'] = role
            update_token(data)
            return HttpResponse(json.dumps(mobile_response), content_type="application/json")
        else:
            # raise Http404("No such user exists with that pin and password combination")
            error_mes['code'] = 404
            error_mes['message'] = 'No such user exists with that username and password combination'
            return HttpResponse(json.dumps(error_mes), status=404)
    else:
        error_mes['code'] = 401
        error_mes['message'] = 'Invalid Login'
        return HttpResponse(json.dumps(error_mes), status=401)

@csrf_exempt
def get_returnee_list(request):
    if request.GET:
        username = request.GET.get('username')
        print(username)
        user_id = __db_fetch_single_value("select id from auth_user where username = '"+str(username)+"'")
        try:
            __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = "+str(user_id))
            q = """WITH t AS 
            ( 
                   SELECT incident_id, 
                          return_from, 
                          victim_name, 
                          contact_self, 
                          sex, 
                          birth_date, 
                          victim_id, 
                          asf_victim.id id , 
                          asf_victim.created_at, 
                          asf_case.status , 
                          division, 
                          district, 
                          upazila, 
                          union_id 
                   FROM   asf_case, 
                          asf_victim 
                   WHERE  asf_case.id = asf_victim.case_id::int 
                   AND    upazila = ANY( 
                          ( 
                                 SELECT 
                                        ( 
                                               SELECT geocode 
                                               FROM   geo_data 
                                               WHERE  id = geoid limit 1) 
                                 from   usermodule_catchment_area 
                                 WHERE  user_id = """+str(user_id)+""") 
                   UNION 
                         ( 
                                SELECT geocode 
                                FROM   geo_data 
                                WHERE  field_parent_id = ANY 
                                       ( 
                                              SELECT geoid 
                                              FROM   usermodule_catchment_area 
                                              WHERE  user_id = """+str(user_id)+""") 
                                AND    field_type_id = 88)) ) 
            SELECT COALESCE(incident_id,'') iom_case_id, 
                   ( 
                          SELECT label_text 
                          FROM   vw_country 
                          WHERE  value_text = return_from) return_country, 
                   COALESCE (victim_name,'')               victim_name, 
                   COALESCE(contact_self,'')               mobile_no, 
                   CASE 
                          WHEN sex = '1' THEN 'Male' 
                          WHEN sex = '2' THEN 'Female' 
                   END                                             gender, 
                   (date_part('year',age(date(birth_date)))::text) returnee_age, 
                   victim_id::text                                 beneficiary_id, 
                   ( 
                          SELECT status 
                          FROM   iom_status 
                          WHERE  id = t.status::int), 
                   id                 AS victim_tbl_id, 
                   (created_at)::text    case_initiation_date, 
                   division              division_id, 
                   district              district_id, 
                   upazila               upazila_id, 
                   union_id 
            FROM   t
                        
            """
        except Exception:
            q = """WITH t AS 
                ( 
                       SELECT incident_id, 
                              return_from, 
                              victim_name, 
                              contact_self, 
                              sex, 
                              birth_date, 
                              victim_id, 
                              asf_victim.id id , 
                              asf_victim.created_at, 
                              asf_case.status , 
                              division, 
                              district, 
                              upazila, 
                              union_id 
                       FROM   asf_case, 
                              asf_victim 
                       WHERE  asf_case.id = asf_victim.case_id::int ) 
                SELECT COALESCE(incident_id,'') iom_case_id, 
                       ( 
                              SELECT label_text 
                              FROM   vw_country 
                              WHERE  value_text = return_from) return_country, 
                       COALESCE (victim_name,'')               victim_name, 
                       COALESCE(contact_self,'')               mobile_no, 
                       CASE 
                              WHEN sex = '1' THEN 'Male' 
                              WHEN sex = '2' THEN 'Female' 
                       END                                             gender, 
                       (Date_part('year',Age(Date(birth_date)))::text) returnee_age, 
                       victim_id::text                                 beneficiary_id, 
                       ( 
                              SELECT status 
                              FROM   iom_status 
                              WHERE  id = t.status::int), 
                       id                 AS victim_tbl_id, 
                       (created_at)::text    case_initiation_date, 
                       division              division_id, 
                       district              district_id, 
                       upazila               upazila_id, 
                       union_id 
                FROM   t
             """
    else:
        q = "select COALESCE((select incident_id from asf_case where id = case_id::int limit 1),'') iom_case_id,(select label_text from vw_country where value_text = (select return_from from asf_case where id = case_id::int limit 1)) return_country, COALESCE (victim_name,'') victim_name,coalesce(contact_self,'') mobile_no,case when sex = '1' then 'Male' when sex = '2' then 'Female' end gender, (date_part('year',age(date(birth_date)))::text) returnee_age, victim_id::text beneficiary_id,(select case when status = '1' then 'New Case' when status = '2' then 'Assigned Profiling' when status = '3' then 'Support Ongoing' when status = '4' then 'Support Completed' when status = '5' then 'Graduated' when status = '6' then 'Cancelled' when status = '7' then 'Dropout' end status from asf_case where id = case_id::int limit 1) status,id as victim_tbl_id,(asf_victim.created_at)::text  case_initiation_date from asf_victim "
    main_df = pandas.read_sql(q, connection)
    j = main_df.to_json(orient='records')
    return HttpResponse(j)


@csrf_exempt
def get_returnee_form(request):
    username = request.GET.get('username')
    returnee_id = request.GET.get('returneeid')
    q = "select id, xml xml_url,json->>'_xform_id_string' form_id,(select title  from  logger_xform where id = xform_id limit 1) form_name,json->>'meta/instanceID' instance_id,TO_CHAR((json->>'_submission_time')::timestamptz, 'yyyy-MM-dd HH:mm:ss') created_date from logger_instance where json->>'victim_tbl_id' = '"+str(returnee_id)+"'"
    json_data_response = []
    cursor = connection.cursor()
    cursor.execute(q)
    tmp_db_value = cursor.fetchall()
    if tmp_db_value is not None:
        for every in tmp_db_value:
            instance_data_json = {}
            instance_data_json['xml_content'] = str(every[1].encode('utf-8'))
            instance_data_json['form_name'] = str(every[3])
            instance_data_json['form_id'] = str(every[2])
            instance_data_json['instance_id'] = str(every[4])
            instance_data_json['created_date'] = str(every[5])
            json_data_response.append(instance_data_json)
    cursor.close()
    return HttpResponse(json.dumps(json_data_response))

'''
@csrf_exempt
def get_returnee_info(request):

    returnee_id = request.GET.get('returneeid')

    q = "select COALESCE((select incident_id from asf_case where id = case_id::int limit 1),'') iom_case_id,(select label_text from vw_country where value_text = (select return_from from asf_case where id = case_id::int limit 1)) return_country, COALESCE (victim_name,'') victim_name,coalesce(contact_self,'') mobile_no,case when sex = '1' then 'Male' when sex = '2' then 'Female' end gender, (date_part('year',age(date(birth_date)))::text) returnee_age, victim_id::text beneficiary_id,(select case when status = '1' then 'New Case' when status = '2' then 'Assigned Profiling' when status = '3' then 'Support Ongoing' when status = '4' then 'Support Completed' when status = '5' then 'Graduated' when status = '6' then 'Cancelled' when status = '7' then 'Dropout' end status from asf_case where id = case_id::int limit 1) status from asf_victim where id ='"+returnee_id+"' limit 1"

    main_df = pandas.read_sql(q, connection)

    j = main_df.to_json(orient='records')

    return HttpResponse(j)
'''

@csrf_exempt
def get_returnee_info(request):
    returnee_id = request.GET.get('returneeid')
    q = "select COALESCE((select incident_id from asf_case where id = case_id::int limit 1),'') iom_case_id,(select label_text from vw_country where value_text = (select return_from from asf_case where id = case_id::int limit 1)) return_country, COALESCE (victim_name,'') victim_name,coalesce(contact_self,'') mobile_no,case when sex = '1' then 'Male' when sex = '2' then 'Female' end gender, (date_part('year',age(date(birth_date)))::text) returnee_age, victim_id::text beneficiary_id,(select case when status = '1' then 'New Case' when status = '2' then 'Assigned Profiling' when status = '3' then 'Support Ongoing' when status = '4' then 'Support Completed' when status = '5' then 'Graduated' when status = '6' then 'Cancelled' when status = '7' then 'Dropout' end status from asf_case where id = case_id::int limit 1) status,id as victim_tbl_id, (asf_victim.created_at)::text case_initiation_date from asf_victim where id ='"+returnee_id+"' limit 1"
    tmp_db_value = __db_fetch_values_dict(q)
    if tmp_db_value is not None:
        for temp in tmp_db_value:
            instance_data_json = {}
            instance_data_json['iom_case_id'] = str(temp['iom_case_id'])
            instance_data_json['return_country'] = str(temp['return_country'])
            instance_data_json['victim_name'] = str(temp['victim_name'])
            instance_data_json['mobile_no'] = str(temp['mobile_no'])
            instance_data_json['returnee_age'] = str(temp['returnee_age'])
            instance_data_json['gender'] = str(temp['gender'])
            instance_data_json['beneficiary_id'] = str(temp['beneficiary_id'])
            instance_data_json['status'] = str(temp['status'])
            instance_data_json['victim_tbl_id'] = str(temp['victim_tbl_id'])
            instance_data_json['case_initiation_date'] = str(temp['case_initiation_date'])

    return HttpResponse(json.dumps(instance_data_json))

@csrf_exempt
def get_user_schedule(request):
    userid = request.GET.get('username')

    '''
    lgeoid = views.__db_fetch_values_dict("select _hh_uid as id from get_hchouseholdlist('" + userid + "')")
    hh_list = [i['id'] for i in lgeoid]
    if len(hh_list) == 0:
        hh_list = "['']"
    '''

    q = "SELECT (select victim_id  from asf_victim where id=schedule.beneficiary_id limit 1) beneficiary_id,beneficiary_id as victim_tbl_id, (select COALESCE (victim_name,'') victim_name from asf_victim where id=schedule.beneficiary_id limit 1) member_name,to_char(schedule_date,'yyyy-mm-dd') schedule_date,(SELECT id_string FROM logger_xform where id=schedule.scheduled_form_id) form_id,(SELECT title FROM logger_xform where id=schedule.scheduled_form_id) form_name,id schedule_id  , schedule_user_id,submitted_instance_id,priority FROM schedule where status='ACTIVE' and date(schedule_date) <= current_date  order by id"
    print q

    main_df = pandas.read_sql(q, connection)
    print main_df
    j = main_df.to_json(orient='records')
    return HttpResponse(j)

@csrf_exempt
def get_event_data(request):
    username = request.GET.get('username')
    user = get_object_or_404(User, username__iexact=str(username))
    user_id = user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = "+str(user_id))
        q = "select * from get_event_api_data(' and upazila = any(select upz_code from get_user_upazila("+str(user_id)+"))')"
    except Exception:
        q = "select * from get_event_api_data('')"
    main_df = pandas.read_sql(q, connection)
    j = main_df.to_json(orient='records')
    return HttpResponse(j)


@csrf_exempt
def get_event_followup_form(request):
    username = request.GET.get('username')
    event_id = request.GET.get('event_id')
    q = "select id, xml xml_url,json->>'_xform_id_string' form_id,(select title  from  logger_xform where id = xform_id limit 1) form_name,json->>'meta/instanceID' instance_id,TO_CHAR((json->>'_submission_time')::timestamptz, 'yyyy-MM-dd HH:mm:ss') created_date from logger_instance where json->>'event_id' = '"+str(event_id)+"'"
    json_data_response = []
    cursor = connection.cursor()
    cursor.execute(q)
    tmp_db_value = cursor.fetchall()
    if tmp_db_value is not None:
        for every in tmp_db_value:
            instance_data_json = {}
            instance_data_json['xml_content'] = str(every[1].encode('utf-8'))
            instance_data_json['form_name'] = str(every[3])
            instance_data_json['form_id'] = str(every[2])
            instance_data_json['instance_id'] = str(every[4])
            instance_data_json['created_date'] = str(every[5])
            json_data_response.append(instance_data_json)
    cursor.close()
    return HttpResponse(json.dumps(json_data_response))
