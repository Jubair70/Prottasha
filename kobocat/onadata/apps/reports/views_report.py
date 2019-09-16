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
import logging
import sys
import operator
import pandas
from pandas import *
from django.shortcuts import render
import numpy
import time
import datetime
from django.core.files.storage import FileSystemStorage

from django.core.urlresolvers import reverse

from django.db import (IntegrityError, transaction)
from django.db.models import ProtectedError
from django.shortcuts import redirect
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.usermodule.forms import UserForm, UserProfileForm, ChangePasswordForm, UserEditForm, OrganizationForm, \
    OrganizationDataAccessForm, ResetPasswordForm
from onadata.apps.usermodule.models import UserModuleProfile, UserPasswordHistory, UserFailedLogin, Organizations, \
    OrganizationDataAccess

from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
# Menu imports
from onadata.apps.usermodule.forms import MenuForm
from onadata.apps.usermodule.models import MenuItem
# Unicef Imports
from onadata.apps.logger.models import Instance, XForm
# Organization Roles Import
from onadata.apps.usermodule.models import OrganizationRole, MenuRoleMap, UserRoleMap
from onadata.apps.usermodule.forms import OrganizationRoleForm, RoleMenuMapForm, UserRoleMapForm, UserRoleMapfForm
from django.forms.models import inlineformset_factory, modelformset_factory
from django.forms.formsets import formset_factory

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from collections import OrderedDict
import decimal
import os
import re
from io import BytesIO
import xlsxwriter
from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML
import lxml.etree as ET
import xlwt
from django.conf import settings

from onadata.apps.dashboard.filtering_controls import *
from onadata.apps.dashboard.component_manager import *

pandas.set_option('display.max_columns', None)
pandas.set_option('display.expand_frame_repr', False)
pandas.set_option('max_colwidth', -1)


def sustainability_report(request):
    user_id = request.user.id
    username = request.user.username
    filteringControl = FilteringControls(6, username)
    controls_info = filteringControl.get_content()
    # Creating CHART/Component for each tab
    componentManager = ComponentManager(6)
    chart_content = componentManager.get_chart_content()
    js_code = ''

    # JS Code
    # Initialize Current TAB Function and filtering submission function
    # ***For String Format: {{ used instead of single {
    js_code += """
                //Function: Initializing Tab {leaf_id}
                function refresh_filter_{leaf_id}(){{
                  {controls_js}
                  {control_js_trigger}
                }}
                function reset_button_{leaf_id}(){{
                   console.log("Filter Reset");
                   $('#right_{leaf_id}').contents(':not(".reset_button")').remove();
                   refresh_filter_{leaf_id}();
                }}
                function init_tab_{leaf_id}() {{
                    console.log($("#container_{leaf_id}").data("load"));
                    openNav("right_6", this);
                    if ($("#container_{leaf_id}").data("load") == "unloaded") {{
                        refresh_filter_{leaf_id}();
                        //mpowerRequestForTable("/dashboard/generate_graph/27/", "group_enterprise", NULL,NULL);
                        //js_chart_calling_function
                        $("#form_{leaf_id}").submit();
                        $("#container_{leaf_id}").data("load", "loaded");
                    }}
                }}
                //Form Submission For Tab {leaf_id}
                $("#form_{leaf_id}").submit(function(event) {{
                    console.log(event);
                    event.preventDefault();

                    var parameters = $(this).serializeArray();
                    console.log(parameters);
                    //{js_chart_calling_function_with_param}
                    {control_js_after_form_submit}

                }} );
                """.format(leaf_id=6, controls_js=controls_info['controls_js'],
                           js_chart_calling_function_with_param=chart_content['js_chart_calling_function_with_param'],
                           control_js_after_form_submit=controls_info['control_js_after_form_submit'],
                           control_js_trigger=controls_info['control_js_trigger'])
    # ,js_chart_calling_function=chart_content['js_chart_calling_function']

    # # json_output = {, 'username': username,'user_id': user_id}
    # print json_output

    return render(request, 'reportmodule/reintegration_sustain_report.html', {'js_code': js_code,'submodule': "reintegration_sustainability", 'report_header': "Reintegration Sustainability Report"})



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
def get_districts(request):
    dv_id = request.POST.get('dv_id')
    district_list = __db_fetch_values_dict(
        "select distinct zl,zila_name from psu_mapping where dv = '" + str(dv_id) + "' order by zila_name")
    return HttpResponse(json.dumps(district_list))


def capitalize(column):
    return re.sub('_.', lambda x: x.group()[1].upper(), column)


def index(request):
    return render(request, 'reportmodule/index.html')


def background(request):
    return render(request, 'reportmodule/background.html')


def contacts(request):
    return render(request, 'reportmodule/contacts.html')


def rsrsc(request):
    return render(request, 'reportmodule/resources.html')


def generate_chart_data(df, yaxis, xaxis, fd_type, predefined_cats=None):
    print df
    print fd_type
    if fd_type is not None and fd_type!='group':
        datasum = df.iloc[0]['denominator']
        df.drop('denominator', axis=1, inplace=True)
        xaxis.remove('denominator')
    else:
        datasum = 'NULL'
    print datasum
    categories = []
    series = [{} for _ in range(len(xaxis))]

    if predefined_cats is None:
        for index, row in df.iterrows():
            categories.append(str(row[yaxis].encode('UTF-8')))
            c = 0
            for xx in xaxis:
                percentage = round(float(row[xx]) / float(sum(df[xx])) * 100, 1) if sum(df[xx]) != 0 else 0
                if not series[c].has_key('data'):
                    series[c]['data'] = []
                series[c]['data'].append({'y': row[xx], 'percentage': percentage})
                if not series[c].has_key('name'):
                    series[c]['name'] = xx
                c = c + 1
    else:
        categories = predefined_cats
        for pc in predefined_cats:
            for index, row in df.iterrows():
                if row[yaxis] == pc:
                    c = 0
                    for xx in xaxis:
                        percentage = round(float(row[xx]) / float(sum(df[xx])) * 100, 1) if sum(df[xx]) != 0 else 0
                        if not series[c].has_key('data'):
                            series[c]['data'] = []
                        series[c]['data'].append({'y': row[xx], 'percentage': percentage})
                        if not series[c].has_key('name'):
                            series[c]['name'] = xx
                        c = c + 1

    return {'categories': categories, 'series': series, 'datasum': datasum}


def generate_pie_chart_data(df, label, value):
    dataseries = []
    for index, row in df.iterrows():
        d = []
        d.append(row[label].encode('utf-8'))
        d.append(row[value])
        dataseries.append(d)
    return dataseries


def get_filtered_query(post_dict, query):
    '''
    @Zinia
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

    for key in post_dict:
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
    print query
    return query

@csrf_exempt
def get_filters(request):
    cursor = connection.cursor()
    rsc_query = "with t as (SELECT id, rsc_name as name FROM public.usermodule_rsc) select array_to_json(array_agg(t)) from t"
    district_query = "with t as (select geo_id as id, field_name as name from vw_rsc_geo_data where field_type_id = 86 and  id::text = any (@rsc)  or (@rsc is null)) select array_to_json(array_agg(t)) from t"

    if request.method == 'POST':
        post_data = request.POST
        print post_data
        cursor.execute(get_filtered_query(post_data, district_query))
        row = cursor.fetchone()
        district_data = row[0]
        jsondata = {'district': district_data}
        return HttpResponse(json.dumps(jsondata), content_type="application/json")
    else:
        post_data = {}

    cursor.execute(get_filtered_query( post_data, rsc_query))
    row = cursor.fetchone()
    rsc_data = row[0]
    cursor.execute(get_filtered_query( post_data, district_query))
    row = cursor.fetchone()
    district_data = row[0]
    jsondata = {'rsc': rsc_data, 'district': district_data}
    print jsondata
    return HttpResponse(json.dumps(jsondata), content_type="application/json")

@login_required
def report_initial(request,sub_module):

    query = "select main_module from chart_list where sub_module = '"+sub_module+"'"
    report_header = __db_fetch_single_value(query)
    return render(request, 'reportmodule/report_board.html',{'submodule':sub_module,'report_header':report_header})


@csrf_exempt
def generate_report(request, sub_module):

    post_data = {}
    if request.method == 'POST':
        print request.POST
        post_data = request.POST
    chart_data = {}
    report_header = ""
    chart_query = "select cheight,divlength,query,ctype,sl_no,chart_title,xindicator,fd_type,cat_order,chart_object,main_module from chart_list where  query is not null  and sub_module = '" + str(
            sub_module) + "' order by sl_no asc"
    print chart_query
    chart_list = __db_fetch_values_dict(chart_query)
    # print chart_list

    for cl in chart_list:
        print cl['sl_no']
        if cl['ctype'] == 'gauge':
            query = get_filtered_query(post_data, cl['query'])
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                fetchVal = cursor.fetchone()
                if fetchVal[0] is not None:
                    g_data = round(fetchVal[0], 1)
                else:
                    g_data = float(0)
            except:
                g_data = float(0)
            cursor.close()
            chart_data[cl['sl_no']] = [g_data, str(cl['ctype']), str(cl['chart_title']), str(cl['xindicator'])]
            report_header = str(cl['main_module'])
        elif cl['ctype'] == 'column' or cl['ctype'] == 'bar':
            query = get_filtered_query(post_data, cl['query'])
            print query
            try:
                column_data_df = pandas.read_sql(query, connection)
                print column_data_df
            except Exception, e:
                print cl['chart_title']
                continue
            headers = list(column_data_df)
            cat_col = headers[0]
            headers.pop(0)
            column_data = generate_chart_data(column_data_df, cat_col, headers, cl['fd_type'], cl['cat_order'])

            filename = excel_file(column_data_df, str(cl['chart_title']), request.user.username)
            chart_data[cl['sl_no']] = [column_data, str(cl['ctype']), str(cl['chart_title']), str(cl['fd_type']),
                                       str(cl['divlength']), str(cl['cheight']),str(cl['chart_object']),filename]
            report_header = str(cl['main_module'])

        elif cl['ctype'] == 'pie':
            query = get_filtered_query(post_data, cl['query'])

            pie_data_df = pandas.read_sql(query,connection )
            headers = list(pie_data_df)
            label = headers[0]
            value = headers[1]
            pie_data = generate_pie_chart_data(pie_data_df, label, value)
            chart_data[cl['sl_no']] = [pie_data, str(cl['ctype']), str(cl['chart_title']), str(cl['fd_type'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] == 'single':
            query = get_filtered_query(post_data, cl['query'])

            cursor = connection.cursor()
            cursor.execute(query)
            fetchVal = cursor.fetchone()
            cursor.close()
            if fetchVal[0] is not None:
                s_data = round(fetchVal[0], 1)
            else:
                s_data = 0
            chart_data[cl['sl_no']] = [s_data, str(cl['ctype']), str(cl['chart_title']), str(cl['xindicator'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] == 'stacked bar':
            query = get_filtered_query(post_data, cl['query'])
            stacked_column_data_df = pandas.io.sql.read_sql(query)
            headers = list(stacked_column_data_df)
            headers.pop(0)
            stacked_data = generate_stacked_bar_chart_data(stacked_column_data_df, 'term', headers)
            chart_data[cl['sl_no']] = [stacked_data, str(cl['ctype']), str(cl['chart_title']), str(cl['fd_type']),
                                       str(cl['divlength']), str(cl['cheight'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] =='card':
            card_data = getCardData(get_filtered_query(post_data,cl['query']))
            icon_class = 'fa fa-google-wallet'
            if cl['sl_no']==1 :
                icon_class = 'fa fa-google-wallet'
            elif cl['sl_no']==2 :
                icon_class = 'fa fa-xing'
            elif cl['sl_no']==3 :
                icon_class = 'fa fa-modx'
            print icon_class
            chart_data[cl['sl_no']] = [json.dumps(card_data), str(cl['ctype']), str(cl['chart_title']),str(cl['divlength']), str(cl['chart_object']),icon_class]
            report_header = str(cl['main_module'])

        elif cl['ctype'] =='table':
            df = pandas.read_sql(get_filtered_query(post_data,cl['query']), connection,index_col=None,)
            table_data = getDashboardDatatable(df)
            print table_data
            chart_data[cl['sl_no']] = [table_data, str(cl['ctype']), str(cl['chart_title']),str(cl['divlength']), str(cl['chart_object'])]
            report_header = str(cl['main_module'])
    return HttpResponse(json.dumps(chart_data), content_type="application/json")


def getDashboardDatatable(df):
    """
    @zinia
    For generating TABLE (USing Datatable.js)
    :param query: SQL QUERY
    :return: JSON Required For Datatable.js
    JSON STRUCTURE AS EXAMPLE:
    {"data": [["Good", 11], ["Medium", 12]], "col_name": ["Qualification", "Count"]}
    PRODUCED TABLE AS EXAMPLE:
    --------------------
    Qualification | Count
    ---------------------
    Good          |  11
    Medium        |  12

    **SQL Query Output same as to be produced one
    """
    data_list = []
    col_names = []
    col_names = list(df.columns.values)
    data_list = map(list, df.values)
    print data_list, col_names

    return json.dumps({'col_name': col_names, 'data': data_list})

def getCardData(query):
    """ @zinia
    :param query: SQL QUERY
    :return: JSON Required For Card with number and details data
    """
    jsondata={}
    cursor = connection.cursor()
    #print query
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    for eachval in fetchVal:
        if eachval[0] is not None:
            jsondata['number'] = eachval[0]
            jsondata['details'] = eachval[1]
            # if len(eachval)>=3:
            #     jsondata['percentage'] = str(eachval[2])
            # else:
            #     jsondata['percentage'] = ''
    return jsondata

def generate_stacked_bar_chart_data(df, yaxis, xaxis):
    categories = []
    series = [{} for _ in range(len(xaxis))]
    for index, row in df.iterrows():
        categories.append(str(row[yaxis].encode('UTF-8')))
        c = 0
        for xx in xaxis:
            if not series[c].has_key('data'):
                series[c]['data'] = []
            series[c]['data'].append({'y': row[xx]})
            if not series[c].has_key('name'):
                if xx == 'numerator_yes':
                    series[c]['name'] = 'Yes'
                    series[c]['index'] = 2
                elif xx == 'numerator_no':
                    series[c]['name'] = 'No'
                    series[c]['index'] = 1
                elif xx == 'numerator_dn':
                    series[c]['name'] = 'Don\'t Know'
                    series[c]['index'] = 0
            c = c + 1

    return {'categories': categories, 'series': series}


def excel_file(df,title,username):
    file = 'pandas_simple_'
    if title !='':
        file = title
        file = file.replace(' ', '_')

    user_path_filename = os.path.join(settings.MEDIA_ROOT, username)
    user_path_filename = os.path.join(user_path_filename, "exported_file")
    if not os.path.exists(user_path_filename):
        os.makedirs(user_path_filename)

    filename = os.path.join(user_path_filename, file + '.xls')

    if 'denominator' in df:
        df.drop('denominator', axis=1, inplace=True)

    writer = pandas.ExcelWriter(filename, engine='xlwt')
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Sheet1',index = False)

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
    return file + '.xls'

