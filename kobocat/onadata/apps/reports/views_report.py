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
    if fd_type is not None:
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
    print "Here"
    dv = "%"
    zila_name = 'All Districts'
    zl = "%"
    div_name = 'All Divisions'
    rural_urban = '%'
    zl_list = []
    post_data = {}
    if request.method == 'POST':
        print request.POST
        post_data = request.POST
    # if request.method == 'POST':
    #     dv = request.POST.get('dv')
    #     if dv != '%':
    #         div_name = __db_fetch_single_value("select div_name from psu_mapping where dv = '" + str(dv) + "' limit 1")
    #     zl = request.POST.get('zl')
    #     if zl != '%':
    #         zila_name = __db_fetch_single_value(
    #             "select zila_name from psu_mapping where zl = '" + str(zl) + "' limit 1")
    #     zl_list = __db_fetch_values_dict(
    #         "select distinct zl,zila_name from psu_mapping where dv = '" + str(dv) + "' order by zila_name")

    # div_list = __db_fetch_values_dict("select distinct on (dv) dv,div_name from psu_mapping")

    chart_data = {}
    report_header = ""
    # page_title = __db_fetch_single_value(
    #     "select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id_string = '" + str(
    #         sub_module) + "'")
    chart_query = "select cheight,divlength,query,ctype,sl_no,chart_title,xindicator,fd_type,cat_order,chart_object,main_module from chart_list where status = 1 and query is not null  and sub_module = '" + str(
            sub_module) + "' order by sl_no asc"
    print chart_query
    chart_list = __db_fetch_values_dict(chart_query)
    print chart_list

    for cl in chart_list:
        print cl['sl_no']
        if cl['ctype'] == 'gauge':
            params = ()
            param_count = cl['query'].count('%s')
            for i in range(param_count / 3):
                params = params + (dv,)
                params = params + (zl,)
                params = params + (rural_urban,)
            cursor = connection.cursor()
            try:
                cursor.execute(cl['query'].replace('"', '\''), params)
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
            # params = []
            # param_count = cl['query'].count('%s')
            # for i in range(param_count / 3):
            #     params.append(dv)
            #     params.append(zl)
            #     params.append(rural_urban)
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
            print str(cl['chart_object'])
            chart_data[cl['sl_no']] = [column_data, str(cl['ctype']), str(cl['chart_title']), str(cl['fd_type']),
                                       str(cl['divlength']), str(cl['cheight']),str(cl['chart_object'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] == 'pie':
            print 'pie'
            query = get_filtered_query(post_data, cl['query'])
            pie_data_df = pandas.read_sql(query,connection )
            headers = list(pie_data_df)
            label = headers[0]
            value = headers[1]
            pie_data = generate_pie_chart_data(pie_data_df, label, value)
            chart_data[cl['sl_no']] = [pie_data, str(cl['ctype']), str(cl['chart_title']), str(cl['fd_type'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] == 'single':
            params = ()
            param_count = cl['query'].count('%s')
            for i in range(param_count / 3):
                params = params + (dv,)
                params = params + (zl,)
                params = params + (rural_urban,)
            cursor = connection.cursor()
            cursor.execute(cl['query'].replace('"', '\''), params)
            fetchVal = cursor.fetchone()
            cursor.close()
            if fetchVal[0] is not None:
                s_data = round(fetchVal[0], 1)
            else:
                s_data = 0
            chart_data[cl['sl_no']] = [s_data, str(cl['ctype']), str(cl['chart_title']), str(cl['xindicator'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] == 'stacked bar':
            params = ()
            param_count = cl['query'].count('%s')
            for i in range(param_count / 3):
                params = params + (dv,)
                params = params + (zl,)
                params = params + (rural_urban,)

            stacked_column_data_df = pandas.io.sql.read_sql(cl['query'].replace('"', '\''), connection, params=params)
            headers = list(stacked_column_data_df)
            headers.pop(0)
            stacked_data = generate_stacked_bar_chart_data(stacked_column_data_df, 'term', headers)
            chart_data[cl['sl_no']] = [stacked_data, str(cl['ctype']), str(cl['chart_title']), str(cl['fd_type']),
                                       str(cl['divlength']), str(cl['cheight'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] =='card':
            card_data = getCardData(get_filtered_query(post_data,cl['query']))
            chart_data[cl['sl_no']] = [json.dumps(card_data), str(cl['ctype']), str(cl['chart_title']),str(cl['divlength']), str(cl['chart_object'])]
            report_header = str(cl['main_module'])

        elif cl['ctype'] =='table':
            df = pandas.read_sql(get_filtered_query(post_data,cl['query']), connection,index_col=None,)
            table_data = getDashboardDatatable(df)
            print table_data
            chart_data[cl['sl_no']] = [table_data, str(cl['ctype']), str(cl['chart_title']),str(cl['divlength']), str(cl['chart_object'])]
            report_header = str(cl['main_module'])

    if zila_name == 'All Districts' and div_name == 'All Divisions':
        page_heading = 'National'
    else:
        page_heading = 'Division: ' + div_name + '/ District: ' + zila_name


    return HttpResponse(json.dumps(chart_data), content_type="application/json")
    # return render(request, 'reportmodule/report_board.html', {
    #     'zl_list': zl_list,
    #     # 'div_list': div_list,
    #     'chart_data': chart_data,
    #     'dv': dv,
    #     'zl': zl,
    #     'page_heading': page_heading,
    #     'page_title': "",
    #     'div_name': div_name,
    #     'zila_name': zila_name,
    #     'report_header':report_header,
    # })


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


def create_dashboard(request):
    submodules = __db_fetch_values_dict("select id_string,title from logger_xform")
    if request.method == "POST":
        main_module = request.POST.get('main_module')
        sub_module = request.POST.get('sub_module')
        ctype = request.POST.get('ctype')
        chart_title = request.POST.get('chart_title')
        sl_no = request.POST.get('sl_no')
        query = request.POST.get('query')

        if main_module and sub_module and ctype and chart_title and sl_no and query:
            __db_commit_query(
                "INSERT INTO public.chart_list (main_module, sub_module, ctype, query, sl_no, status, chart_title) VALUES('" + str(
                    main_module) + "', '" + str(sub_module) + "', '" + str(ctype) + "', '" + str(query) + "', " + str(
                    sl_no) + ", 1, '" + str(chart_title) + "')")
    return render(request, 'reportmodule/create_dashbaord.html', {
        'submodules': submodules
    })


def sample_distribution(request):
    region_data = {}
    region_table = []
    district_data = __db_fetch_values(
        "with t as(select dv,zl,count(instance_id) as cnt from vw_hh_information_rnd2 where dv is not null and zl is not null group by dv,zl) select (select zila_name from psu_mapping where dv = t.dv and zl = t.zl limit 1) as zila_name,cnt from t order by cnt DESC")
    for dd in district_data:
        region_data[dd[0]] = dd[1]
        region_table.append([dd[0], dd[1]])

    return render(request, 'reportmodule/sample_distribution.html', {
        'region_data': json.dumps(region_data),
        'region_table': json.dumps(region_table)
    })


@csrf_exempt
def generate_tanahashi_model(request):
    div_list = __db_fetch_values_dict("select distinct on (dv) dv,div_name from psu_mapping")
    sector_list = __db_fetch_values_dict(
        "select distinct sector_id,sector_name from sector_module_mapping where sector_name != 'Ward Shova' order by sector_id asc")
    tanahashi_data = {}
    dv = '%'
    div_name = 'All Divisions'
    zl = '%'
    zila_name = 'All Districts'
    sector = '%'
    sector_name = 'All Programmes'
    round = '%'
    zl_list = []
    if request.method == 'POST':
        dv = request.POST.get('dv')
        if dv != '%':
            div_name = __db_fetch_single_value("select div_name from psu_mapping where dv = '" + str(dv) + "' limit 1")
        zl = request.POST.get('zl')
        if zl != '%':
            zila_name = __db_fetch_single_value(
                "select zila_name from psu_mapping where zl = '" + str(zl) + "' limit 1")
        sector = request.POST.get('sector')
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id = " + str(sector) + " limit 1")
        round = request.POST.get('round')
        zl_list = __db_fetch_values_dict(
            "select distinct zl,zila_name from psu_mapping where dv = '" + str(dv) + "' order by zila_name")

    th_df = pandas.io.sql.read_sql(
        "select sl_no,sector_id, module_id,module_name,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id =module_id) as module_title,tanahashi_proc from sector_module_mapping where tanahashi_proc is not null and sector_id::text like '" + str(
            sector) + "' order by sl_no ASC", connection)
    for index, row in th_df.iterrows():
        tooltip_data = pandas.io.sql.read_sql(
            "select indicator_type,indicator_title from tanahashi_indicators where module_id = " + str(
                row['module_id']) + "", connection)
        tanahashi_data[row['module_name']] = {}
        tanahashi_data[row['module_name']]['module_title'] = row['module_title']
        tanahashi_data[row['module_name']]['sl_no'] = row['sl_no']
        if row['tanahashi_proc'] != 'get_tanahashi_hiv':
            th_module_data = generate_tanahashi_chart_data(row['tanahashi_proc'], row['sector_id'], dv, zl, round)
            tanahashi_data[row['module_name']]['module_chart_data'] = th_module_data
            tanahashi_data[row['module_name']]['tooltip_data'] = tooltip_data
        else:
            vv = __db_fetch_single_value(
                "select * from " + str(row['tanahashi_proc']) + "(" + str(row['sector_id']) + ",'" + str(
                    dv) + "','" + str(zl) + "')")
            tanahashi_data[row['module_name']]['module_chart_data'] = float(("%0.1f" % vv))

    if zila_name == 'All Districts' and div_name == 'All Divisions' and sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name + '/ Division: ' + div_name + '/ District: ' + zila_name

    return render(request, 'reportmodule/tanahashi_model.html', {
        'zl_list': zl_list,
        'sector': sector,
        'dv': dv,
        'zl': zl,
        'sector_list': sector_list,
        'div_list': div_list,
        'page_heading': page_heading,
        'tanahashi_data': json.dumps(tanahashi_data)
    })


def generate_tanahashi_chart_data(tanahashi_proc, sector_id, dv, zl, round):
    # if round == '%':
    module_data = pandas.io.sql.read_sql(
        "select indicator_name,r2_value from " + str(tanahashi_proc) + "(" + str(sector_id) + ",'" + str(
            dv) + "','" + str(zl) + "')", connection)
    # module_data.r1_value = module_data.r1_value.round(1)
    module_data.r2_value = module_data.r2_value.round(1)
    module_data.columns = ['indicator_name', 'Round 2']
    # elif round == '1':
    #     module_data = pandas.io.sql.read_sql(
    #         "select indicator_name,r1_value from " + str(tanahashi_proc) + "(" + str(sector_id) + ",'" + str(
    #             dv) + "','" + str(zl) + "')", connection)
    #     module_data.r1_value = module_data.r1_value.round(1)
    #     module_data.columns = ['indicator_name', 'Round 1']
    # elif round == '2':
    #     module_data = pandas.io.sql.read_sql(
    #         "select indicator_name,r2_value from " + str(tanahashi_proc) + "(" + str(sector_id) + ",'" + str(
    #             dv) + "','" + str(zl) + "')", connection)
    #     module_data.r2_value = module_data.r2_value.round(1)
    #     module_data.columns = ['indicator_name', 'Round 2']

    headers = list(module_data)
    cat_col = headers[0]
    headers.pop(0)
    column_data = generate_chart_data(module_data, cat_col, headers, None)
    return column_data


@csrf_exempt
def generate_factsheet_general(request):
    dv = '-99'
    zl = '-99'
    zila_name = 'All Districts'
    div_name = 'All Divisions'
    sector_name = 'All Programmes'
    sector = '%'
    zl_list = []
    if request.method == 'POST':
        dv = request.POST.get('dv')
        zl = request.POST.get('zl')
        sector = request.POST.get('sector')

        if dv != '-99':
            div_name = __db_fetch_single_value(
                "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
        if zl != '-99':
            zila_name = __db_fetch_single_value(
                "select zila_name from psu_mapping where zl like '" + str(zl) + "' limit 1")
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

        zl_list = __db_fetch_values_dict(
            "select distinct zl,zila_name from psu_mapping where dv = '" + str(dv) + "' order by zila_name")
    div_list = __db_fetch_values_dict("select distinct on (dv) dv,div_name from psu_mapping")
    sector_list = __db_fetch_values_dict(
        "select distinct sector_id,sector_name from sector_module_mapping order by sector_id asc")

    facts_data = pandas.io.sql.read_sql(
        "with t as(select fdg.xindicator,sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,rural_value,urban_value from factsheet_data_general fdg left join sector_module_mapping smm on fdg.module_id = smm.module_id where fdg.round = 2 and fdg.dv like '" + str(
            dv) + "' and fdg.zl like '" + str(zl) + "' and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.sector_id,fdg.xindicator) select distinct on(t.xindicator) t.program,t.module,t.indicator,t.overall_value,t.rural_value,t.urban_value from t",
        connection)

    s_p = facts_data.rename(
        {'program': 'Programme', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'Overall (%)',
         'rural_value': 'Rural (%)', 'urban_value': 'Urban (%)'}, axis='columns')

    # s_p = facts_data.rename(columns=
    #     {'program': 'Programme', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'Overall',
    #      'rural_value': 'Rural', 'urban_value': 'Urban'})

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[['Overall (%)', 'Rural (%)', 'Urban (%)']].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    s_p = s_p.reset_index()

    sphtml = s_p.to_html(classes=["table", "table-bordered", "table-hover"], header=False, index=False)

    if zila_name == 'All Districts' and div_name == 'All Divisions' and sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name + '/ Division: ' + div_name + '/ District: ' + zila_name

    return render(request, 'reportmodule/factsheet_general.html', {
        'zl_list': zl_list,
        'dv': dv,
        'zl': zl,
        'sector': sector,
        'sector_list': sector_list,
        'div_list': div_list,
        'page_heading': page_heading,
        'sphtml': sphtml
    })


@csrf_exempt
def generate_factsheet_division(request):
    dv = '%'
    divs_col = ['National', 'Barishal', 'Chattogram', 'Dhaka', 'Khulna', 'Mymensingh', 'Rajshahi', 'Rangpur', 'Sylhet']
    sector = '%'
    sector_name = 'All Programmes'
    if request.method == 'POST':
        divs_col = ['National', 'Barishal', 'Chattogram', 'Dhaka', 'Khulna', 'Mymensingh', 'Rajshahi', 'Rangpur',
                    'Sylhet']
        sector = request.POST.get('sector')
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    div_list = __db_fetch_values_dict("select distinct on (dv) dv,div_name from psu_mapping")
    sector_list = __db_fetch_values_dict(
        "select distinct sector_id,sector_name from sector_module_mapping order by sector_id asc")

    facts_data = pandas.io.sql.read_sql(
        "select sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,barisal_value,chittagong_value,dhaka_value,khulna_value,mymensingh_value,rajshahi_value,rongpur_value,sylhet_value from factsheet_data_division fdg left join sector_module_mapping smm on smm.module_id = fdg.module_id where fdg.round = 2 and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.module_id,fdg.xindicator",
        connection)

    s_p = facts_data.rename(
        {'program': 'Programme', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'National',
         'barisal_value': 'Barishal', 'chittagong_value': 'Chattogram', 'dhaka_value': 'Dhaka',
         'khulna_value': 'Khulna',
         'mymensingh_value': 'Mymensingh', 'rajshahi_value': 'Rajshahi', 'rongpur_value': 'Rangpur',
         'sylhet_value': 'Sylhet'}, axis='columns')

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[divs_col].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    s_p = s_p.reset_index()

    sphtml = s_p.to_html(classes=["table", "table-bordered", "table-hover"], header=False, index=False)

    if sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name

    return render(request, 'reportmodule/factsheet_division.html', {
        'dv': dv,
        'sector': sector,
        'sector_list': sector_list,
        'div_list': div_list,
        'sphtml': sphtml,
        'page_heading': page_heading
    })


@csrf_exempt
def generate_factsheet_district(request):
    dv = '%'
    zl_col = ["National", "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura", "Brahmanbaria", "Chandpur",
              "Chattogram",
              "Chuadanga", "Cumilla", "Cox's Bazar", "Dhaka", "Dinajpur", "Faridpur", "Feni", "Gaibandha", "Gazipur",
              "Gopalganj", "Habiganj", "Joypurhat", "Jamalpur", "Jashore", "Jhalokati", "Jhenaidah", "Khagrachhari",
              "Khulna", "Kishoregonj", "Kurigram", "Kushtia", "Lakshmipur", "Lalmonirhat", "Madaripur", "Magura",
              "Manikganj", "Meherpur", "Moulvibazar", "Munshiganj", "Mymensingh", "Naogaon", "Narail", "Narayanganj",
              "Narsingdi", "Natore", "Nawabganj", "Netrokona", "Nilphamari", "Noakhali", "Pabna", "Panchagarh",
              "Patuakhali", "Pirojpur", "Rajshahi", "Rajbari", "Rangamati", "Rangpur", "Shariatpur", "Satkhira",
              "Sirajganj", "Sherpur", "Sunamganj", "Sylhet", "Tangail", "Thakurgaon"]
    sector = '%'

    div_name = 'All Divisions'
    sector_name = 'All Programmes'

    if request.method == 'POST':
        sector = request.POST.get('sector')
        dv = request.POST.get('dv')
        if dv:
            zl_col = [i[0] for i in __db_fetch_values(
                "select distinct zila_name from psu_mapping where dv like '" + str(dv) + "' order by zila_name")]
            zl_col.insert(0, 'National')

            if dv != '%':
                div_name = __db_fetch_single_value(
                    "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
            if sector != '%':
                sector_name = __db_fetch_single_value(
                    "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                        sector) + "' limit 1")

    div_list = __db_fetch_values_dict("select distinct on (dv) dv,div_name from psu_mapping")
    sector_list = __db_fetch_values_dict(
        "select distinct sector_id,sector_name from sector_module_mapping order by sector_id asc")

    facts_data = pandas.io.sql.read_sql(
        "select smm.sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,bagerhat_value, bandarban_value, barguna_value, barisal_value, bhola_value, bogra_value, brahmanbaria_value, chandpur_value, chittagong_value, chuadanga_value, comilla_value, cbazar_value, dhaka_value, dinajpur_value, faridpur_value, feni_value, gaibandha_value, gazipur_value, gopalganj_value, habiganj_value, jamalpur_value, jessore_value, jhalokati_value, jhenaidah_value, joypurhat_value, khagrachhari_value, khulna_value, kishorgonj_value, kurigram_value, kushtia_value, lakshmipur_value, lalmonirhat_value, madaripur_value, magura_value, manikganj_value, maulvibazar_value, meherpur_value, munshiganj_value, mymensingh_value, naogaon_value, narail_value, narayanganj_value, narsingdi_value, natore_value, nawabganj_value, netrakona_value, nilphamari_value, noakhali_value, pabna_value, panchagarh_value, patuakhali_value, pirojpur_value, rajbari_value, rajshahi_value, rangamati_value, rangpur_value, satkhira_value, shariatpur_value, sherpur_value, sirajganj_value, sunamganj_value, sylhet_value, tangail_value, thakurgaon_value from factsheet_data_district fdg left join sector_module_mapping smm on smm.module_id = fdg.module_id where fdg.round = 2 and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.sector_id,fdg.module_id,fdg.xindicator",
        connection)

    s_p = facts_data.rename(
        {"program": "Programme", "module": "Module", "indicator": "Indicator", "overall_value": "National",
         "bagerhat_value": "Bagerhat", "bandarban_value": "Bandarban", "barguna_value": "Barguna",
         "barisal_value": "Barishal", "bhola_value": "Bhola", "bogra_value": "Bogura",
         "brahmanbaria_value": "Brahmanbaria", "chandpur_value": "Chandpur", "chittagong_value": "Chattogram",
         "chuadanga_value": "Chuadanga", "comilla_value": "Cumilla", "cbazar_value": "Cox's Bazar",
         "dhaka_value": "Dhaka", "dinajpur_value": "Dinajpur", "faridpur_value": "Faridpur", "feni_value": "Feni",
         "gaibandha_value": "Gaibandha", "gazipur_value": "Gazipur", "gopalganj_value": "Gopalganj",
         "habiganj_value": "Habiganj", "jamalpur_value": "Jamalpur", "jessore_value": "Jashore",
         "jhalokati_value": "Jhalokati", "jhenaidah_value": "Jhenaidah", "joypurhat_value": "Joypurhat",
         "khagrachhari_value": "Khagrachhari", "khulna_value": "Khulna", "kishorgonj_value": "Kishoregonj",
         "kurigram_value": "Kurigram", "kushtia_value": "Kushtia", "lakshmipur_value": "Lakshmipur",
         "lalmonirhat_value": "Lalmonirhat", "madaripur_value": "Madaripur", "magura_value": "Magura",
         "manikganj_value": "Manikganj", "maulvibazar_value": "Moulvibazar", "meherpur_value": "Meherpur",
         "munshiganj_value": "Munshiganj", "mymensingh_value": "Mymensingh", "naogaon_value": "Naogaon",
         "narail_value": "Narail", "narayanganj_value": "Narayanganj", "narsingdi_value": "Narsingdi",
         "natore_value": "Natore", "nawabganj_value": "Nawabganj", "netrakona_value": "Netrokona",
         "nilphamari_value": "Nilphamari", "noakhali_value": "Noakhali", "pabna_value": "Pabna",
         "panchagarh_value": "Panchagarh", "patuakhali_value": "Patuakhali", "pirojpur_value": "Pirojpur",
         "rajbari_value": "Rajbari", "rajshahi_value": "Rajshahi", "rangamati_value": "Rangamati",
         "rangpur_value": "Rangpur", "satkhira_value": "Satkhira", "shariatpur_value": "Shariatpur",
         "sherpur_value": "Sherpur", "sirajganj_value": "Sirajganj", "sunamganj_value": "Sunamganj",
         "sylhet_value": "Sylhet", "tangail_value": "Tangail", "thakurgaon_value": "Thakurgaon"
         }, axis='columns')

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[zl_col].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    dis_list = s_p.columns.values

    s_p = s_p.reset_index()

    sphtml = s_p.to_html(classes=["table", "table-bordered", "table-hover"], header=False, index=False)

    if div_name == 'All Divisions' and sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name + '/ Division: ' + div_name

    return render(request, 'reportmodule/factsheet_districts.html', {
        'dv': dv,
        'sector': sector,
        'page_heading': page_heading,
        'sector_list': sector_list,
        'div_list': div_list,
        'sphtml': sphtml,
        'dis_list': json.dumps(dis_list)
    })


@csrf_exempt
def generate_demographics_info(request):
    dv = '%'
    div_name = 'All Divisions'
    zl = '%'
    zila_name = 'All Districts'
    zl_list = []
    if request.method == 'POST':
        dv = request.POST.get('dv')
        if dv != '%':
            div_name = __db_fetch_single_value(
                "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
        zl = request.POST.get('zl')
        if zl != '%':
            zila_name = __db_fetch_single_value(
                "select zila_name from psu_mapping where zl like '" + str(zl) + "' limit 1")
        zl_list = __db_fetch_values_dict(
            "select distinct zl,zila_name from psu_mapping where dv = '" + str(dv) + "' order by zila_name")

    div_list = __db_fetch_values_dict("select distinct on (dv) dv,div_name from psu_mapping")

    hh_size_data = pandas.io.sql.read_sql(
        "with q as (select count(instance_id) as cnt from vw_hh_information_rnd2 where dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "'), t as(select '1~2' as no_of_hh_member, count(*) as frequency from vw_hh_information_rnd2 where dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' and no_of_hh_member::int between 1 and 2 union all select '3~4' as no_of_hh_member, count(*) as frequency from vw_hh_information_rnd2 where dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' and no_of_hh_member::int between 3 and 4 union all select '4~5' as no_of_hh_member,count(*) as frequency from vw_hh_information_rnd2 where dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' and no_of_hh_member::int between 5 and 6 union all select '7~8' as no_of_hh_member,count(*) as frequency from vw_hh_information_rnd2 where dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' and no_of_hh_member::int between 7 and 8 union all select '=>9' as no_of_hh_member,count(*) as frequency from vw_hh_information_rnd2 where dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' and no_of_hh_member::int >= 9) select t.no_of_hh_member,t.frequency::float/q.cnt::float * 100 as frequency from t,q",
        connection)
    hh_size_data.frequency = hh_size_data.frequency.round(1)
    hh_size_headers = list(hh_size_data)
    hh_size_cat_col = hh_size_headers[0]
    hh_size_headers.pop(0)
    hh_size_chart_data = generate_chart_data(hh_size_data, hh_size_cat_col, hh_size_headers, None)

    edu_lvl_data = pandas.io.sql.read_sql(
        "WITH m AS( WITH q AS( SELECT Count(*) filter (WHERE gender = '1') AS t_m, count(*) filter (WHERE gender = '2') AS t_f FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND highest_grade_passed IS NOT NULL), s AS ( SELECT 'Illiterate' AS highest_grade_passed, 0 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('0') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Pre-primary Education' AS highest_grade_passed, 1 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('77','66') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Grade 1 ~ 5' AS highest_grade_passed, 1 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('1', '2', '3', '4', '5') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Grade 6 ~ 10' AS highest_grade_passed, 2 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('6','7','8','9','10') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'SSC/Equivalent' AS highest_grade_passed, 3 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('11','12','16') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'HSC/Equivalent' AS highest_grade_passed, 4 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('13') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Greater than HSC' AS highest_grade_passed, 4 AS ord, 'Female' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('14','15') AND gender = '2' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Illiterate' AS highest_grade_passed, 0 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('0') AND gender= '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Pre-primary Education' AS highest_grade_passed, 1 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('77','66') AND gender = '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Grade 1 ~ 5' AS highest_grade_passed, 1 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('1','2', '3', '4', '5') AND gender = '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Grade 6 ~ 10' AS highest_grade_passed, 2 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed ::int IN ('6', '7', '8', '9', '10') AND gender = '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'SSC/Equivalent' AS highest_grade_passed, 3 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('11','12','16') AND gender = '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'HSC/Equivalent' AS highest_grade_passed, 4 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('13') AND gender = '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' UNION ALL SELECT 'Greater than HSC' AS highest_grade_passed, 4 AS ord, 'Male' AS gender, count(*) AS cnt FROM vw_hh_members_information_rnd2 WHERE highest_grade_passed IN ('14','15') AND gender = '1' AND dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "') SELECT highest_grade_passed, gender, cnt, CASE WHEN gender = 'Male' THEN t_m ELSE t_f END AS total_cnt FROM q, s) SELECT m.highest_grade_passed, m.gender, m.cnt::float/m.total_cnt::float * 100 AS percentage FROM m",
        connection)
    edu_lvl_data_org = pandas.pivot_table(edu_lvl_data, values='percentage', index=['highest_grade_passed'],
                                          columns=['gender'])

    # edu_lvl_data_org = pandas.pivot_table(edu_lvl_data, values='cnt', rows=['highest_grade_passed'],
    #                                       cols=['gender'])

    edu_lvl_data_org.Male = edu_lvl_data_org.Male.round(1)
    edu_lvl_data_org.Female = edu_lvl_data_org.Female.round(1)

    edu_lvl_flattened = pandas.DataFrame(edu_lvl_data_org.to_records())

    edu_lvl_headers = list(edu_lvl_flattened)
    edu_lvl_cat_col = edu_lvl_headers[0]
    edu_lvl_headers.pop(0)
    edu_lvl_chart_data = generate_chart_data(edu_lvl_flattened, edu_lvl_cat_col, edu_lvl_headers, None,
                                             ['Illiterate', 'Pre-primary Education', 'Grade 1 ~ 5', 'Grade 6 ~ 10',
                                              'SSC/Equivalent', 'HSC/Equivalent', 'Greater than HSC'])

    age_dis_data = pandas.io.sql.read_sql(
        "WITH m AS(WITH q AS( SELECT Count(*) filter (WHERE gender = '1') AS t_m, count(*) filter (WHERE gender = '2') AS t_f FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "'), s AS ( SELECT '0 ~ 4' AS grp, 'Male' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 0 AND 4 AND gender = '1' UNION ALL SELECT '5 ~ 14' AS grp, 'Male' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 5 AND 14 AND gender = '1' UNION ALL SELECT '10 ~ 19' AS grp, 'Male' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 5 AND 14 AND gender = '1' UNION ALL SELECT '15 ~ 19' AS grp, 'Male' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 15 AND 19 AND gender = '1' UNION ALL SELECT '0 ~ 17' AS grp, 'Male' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 0 AND 17 AND gender = '1' UNION ALL SELECT '>=18' AS grp, 'Male' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int >= 18 AND gender = '1' UNION ALL SELECT '0 ~ 4' AS grp, 'Female' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 0 AND 4 AND gender = '2' UNION ALL SELECT '5 ~ 14' AS grp, 'Female' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 5 AND 14 AND gender = '2' UNION ALL SELECT '10 ~ 19' AS grp, 'Female' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 5 AND 14 AND gender = '2' UNION ALL SELECT '15 ~ 19' AS grp, 'Female' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 15 AND 19 AND gender :: int = 2 UNION ALL SELECT '0 ~ 17' AS grp, 'Female' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int BETWEEN 0 AND 17 AND gender = '2' UNION ALL SELECT '>=18' AS grp, 'Female' AS gender, count(*) AS freq FROM vw_hh_members_information_rnd2 WHERE dv LIKE '" + str(
            dv) + "' AND zl LIKE '" + str(
            zl) + "' AND age_year ::int >= 18 AND gender = '2') SELECT grp, gender, freq, CASE WHEN gender = 'Male' THEN t_m ELSE t_f END AS total_cnt FROM q, s) SELECT m.grp, m.gender, m.freq::float/m.total_cnt::float * 100 AS percentage FROM m",
        connection)
    age_dis_org = pandas.pivot_table(age_dis_data, values='percentage', index=['grp'],
                                     columns=['gender'])

    # age_dis_org = pandas.pivot_table(age_dis_data, values='percentage', rows=['grp'],
    #                                  cols=['gender'])

    age_dis_org.Male = age_dis_org.Male.round(1)
    age_dis_org.Female = age_dis_org.Female.round(1)
    age_dis_flattened = pandas.DataFrame(age_dis_org.to_records())

    age_dis_headers = list(age_dis_flattened)
    age_dis_cat_col = age_dis_headers[0]
    age_dis_headers.pop(0)
    age_dis_chart_data = generate_chart_data(age_dis_flattened, age_dis_cat_col, age_dis_headers, None,
                                             ['0 ~ 4', '5 ~ 14', '10 ~ 19', '15 ~ 19', '0 ~ 17', '>=18'])

    male_marital_data = pandas.io.sql.read_sql(
        "with t as(select value_text,value_label::json->>'English' as value_label from xform_extracted where xform_id = 518 and field_name = 'group_member/Marital_status'), s as(select count(id) as cnt, marital_status from vw_hh_members_information_rnd2 where gender = '1' and dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' group by marital_status) select t.value_label as marital_status,s.cnt as freq from t,s where t.value_text = s.marital_status order by t.value_text",
        connection)
    male_marital_chart_data = generate_pie_chart_data(male_marital_data, 'marital_status', 'freq')

    female_marital_data = pandas.io.sql.read_sql(
        "with t as(select value_text,value_label::json->>'English' as value_label from xform_extracted where xform_id = 518 and field_name = 'group_member/Marital_status'), s as(select count(id) as cnt, marital_status from vw_hh_members_information_rnd2 where gender = '2' and dv like '" + str(
            dv) + "' and zl like '" + str(
            zl) + "' group by marital_status) select t.value_label as marital_status,s.cnt as freq from t,s where t.value_text = s.marital_status order by t.value_text",
        connection)
    female_marital_chart_data = generate_pie_chart_data(female_marital_data, 'marital_status', 'freq')

    if div_name == 'All Divisions' and zila_name == 'All Districts':
        page_heading = 'National'
    else:
        page_heading = 'Division: ' + div_name + '/ District: ' + zila_name

    return render(request, 'reportmodule/demographics_info.html', {
        'dv': dv,
        'zl': zl,
        'div_list': div_list,
        'zl_list': zl_list,
        'hh_size_chart_data': json.dumps(hh_size_chart_data),
        'edu_lvl_chart_data': json.dumps(edu_lvl_chart_data),
        'age_dis_chart_data': json.dumps(age_dis_chart_data),
        'male_marital_chart_data': json.dumps(male_marital_chart_data),
        'female_marital_chart_data': json.dumps(female_marital_chart_data),
        'page_heading': page_heading
    })


def export_data_to_excel(df, title, sheetname, type, page_heading=None):
    sheetname = 'factsheet'
    pd_writer = pandas.ExcelWriter('onadata/media/reports/' + title + '.xlsx', engine='xlsxwriter')
    if type == 'ranking':
        df.to_excel(pd_writer, sheet_name=sheetname, startrow=4, index=False)
    else:
        df.to_excel(pd_writer, sheet_name=sheetname, startrow=4)
    xls_col_name = excel_column_name(len(df.columns) + 3)
    workbook = pd_writer.book
    total_fmt = workbook.add_format({'align': 'right'})
    worksheet = pd_writer.sheets[sheetname]
    merge_format = workbook.add_format({'bold': True, 'align': 'center', 'font_size': '14px'})
    print type
    if type == 'general':
        worksheet.set_column('D:F', 12, total_fmt)
        main_heading = 'Factsheet'
    elif type == 'division':
        worksheet.set_column('D:L', 12, total_fmt)
        main_heading = 'Factsheet - Division Comparison'
    elif type == 'district':
        worksheet.set_column('D:BP', 12, total_fmt)
        main_heading = 'Factsheet - District Comparison'
    elif type == 'ranking':
        main_heading = 'Ranking'
        xls_col_name = excel_column_name(len(df.columns))
        worksheet.set_column('B:B', 12, total_fmt)

    worksheet.merge_range('A1:' + str(xls_col_name) + '1',
                          'AN ASSESSMENT ON COVERAGE OF BASIC SOCIAL SERVICES IN BANGLADESH', merge_format)
    worksheet.merge_range('A2:' + str(xls_col_name) + '2', '(Accelerating SDGs)', merge_format)
    worksheet.merge_range('A3:' + str(xls_col_name) + '3', main_heading, merge_format)
    if page_heading is not None:
        worksheet.merge_range('A4:' + str(xls_col_name) + '4', page_heading, merge_format)

    pd_writer.save()

    return HttpResponse(json.dumps('/media/reports/' + title + '.xlsx'))


def excel_column_name(n):
    name = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        name = chr(r + ord('A')) + name
    return name


@csrf_exempt
def export_factsheet_general(request):
    dv = '-99'
    zl = '-99'
    sector = '%'
    zila_name = 'All Districts'
    div_name = 'All Divisions'
    sector_name = 'All Programmes'

    if request.method == 'POST':
        dv = request.POST.get('dv')
        zl = request.POST.get('zl')
        sector = request.POST.get('sector')

        if dv != '-99':
            div_name = __db_fetch_single_value(
                "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
        if zl != '-99':
            zila_name = __db_fetch_single_value(
                "select zila_name from psu_mapping where zl like '" + str(zl) + "' limit 1")
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    facts_data = pandas.io.sql.read_sql(
        "with t as(select fdg.xindicator,sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,rural_value,urban_value from factsheet_data_general fdg left join sector_module_mapping smm on fdg.module_id = smm.module_id where fdg.round = 2 and fdg.dv like '" + str(
            dv) + "' and fdg.zl like '" + str(zl) + "' and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.sector_id,fdg.xindicator) select distinct on(t.xindicator) t.program,t.module,t.indicator,t.overall_value,t.rural_value,t.urban_value from t",
        connection)

    s_p = facts_data.rename(
        {'program': 'Program', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'Overall (%)',
         'rural_value': 'Rural (%)', 'urban_value': 'Urban (%)'}, axis='columns')

    s_p = s_p.set_index(['Program', 'Module', 'Indicator'])

    s_p = s_p[['Overall (%)', 'Rural (%)', 'Urban (%)']].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    if zila_name == 'All Districts' and div_name == 'All Divisions' and sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name + '/ Division: ' + div_name + '/ District: ' + zila_name

    return export_data_to_excel(s_p, 'factsheet_general_' + cur_time,
                                str(sector_name) + '-' + str(div_name) + '-' + str(zila_name), 'general', page_heading)


@csrf_exempt
def export_factsheet_division(request):
    dv = '%'
    divs_col = ['National (%)', 'Barishal (%)', 'Chattogram (%)', 'Dhaka (%)', 'Khulna (%)', 'Mymensingh (%)',
                'Rajshahi (%)', 'Rangpur (%)', 'Sylhet (%)']
    sector = '%'
    sector_name = 'All Programmes'
    if request.method == 'POST':
        divs_col = ['National (%)', 'Barishal (%)', 'Chattogram (%)', 'Dhaka (%)', 'Khulna (%)', 'Mymensingh (%)',
                    'Rajshahi (%)', 'Rangpur (%)',
                    'Sylhet (%)']
        sector = request.POST.get('sector')
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    facts_data = pandas.io.sql.read_sql(
        "select sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,barisal_value,chittagong_value,dhaka_value,khulna_value,mymensingh_value,rajshahi_value,rongpur_value,sylhet_value from factsheet_data_division fdg left join sector_module_mapping smm on smm.module_id = fdg.module_id where fdg.round = 2 and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.module_id,fdg.xindicator",
        connection)

    s_p = facts_data.rename(
        {'program': 'Programme', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'National (%)',
         'barisal_value': 'Barishal (%)', 'chittagong_value': 'Chattogram (%)', 'dhaka_value': 'Dhaka (%)',
         'khulna_value': 'Khulna (%)',
         'mymensingh_value': 'Mymensingh (%)', 'rajshahi_value': 'Rajshahi (%)', 'rongpur_value': 'Rangpur (%)',
         'sylhet_value': 'Sylhet (%)'}, axis='columns')

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[divs_col].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    if sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name

    return export_data_to_excel(s_p, 'factsheet_division_' + cur_time, str(sector_name), 'division', page_heading)


@csrf_exempt
def export_factsheet_district(request):
    dv = '%'
    zl_col = ["National (%)", "Bagerhat (%)", "Bandarban (%)", "Barguna (%)", "Barishal (%)", "Bhola (%)", "Bogura (%)",
              "Brahmanbaria (%)", "Chandpur (%)",
              "Chattogram (%)",
              "Chuadanga (%)", "Cumilla (%)", "Cox's Bazar (%)", "Dhaka (%)", "Dinajpur (%)", "Faridpur (%)",
              "Feni (%)", "Gaibandha (%)", "Gazipur (%)",
              "Gopalganj (%)", "Habiganj (%)", "Joypurhat (%)", "Jamalpur (%)", "Jashore (%)", "Jhalokati (%)",
              "Jhenaidah (%)", "Khagrachhari (%)",
              "Khulna (%)", "Kishoregonj (%)", "Kurigram (%)", "Kushtia (%)", "Lakshmipur (%)", "Lalmonirhat (%)",
              "Madaripur (%)", "Magura (%)",
              "Manikganj (%)", "Meherpur (%)", "Moulvibazar (%)", "Munshiganj (%)", "Mymensingh (%)", "Naogaon (%)",
              "Narail (%)", "Narayanganj (%)",
              "Narsingdi (%)", "Natore (%)", "Nawabganj (%)", "Netrokona (%)", "Nilphamari (%)", "Noakhali (%)",
              "Pabna (%)", "Panchagarh (%)",
              "Patuakhali (%)", "Pirojpur (%)", "Rajshahi (%)", "Rajbari (%)", "Rangamati (%)", "Rangpur (%)",
              "Shariatpur (%)", "Satkhira (%)",
              "Sirajganj (%)", "Sherpur (%)", "Sunamganj (%)", "Sylhet (%)", "Tangail (%)", "Thakurgaon (%)"]
    sector = '%'
    div_name = 'All Divisions'
    sector_name = 'All Programmes'
    if request.method == 'POST':
        sector = request.POST.get('sector')
        dv = request.POST.get('dv')
        if dv:
            zl_col = [i[0] for i in __db_fetch_values(
                "with t as (select distinct zila_name from psu_mapping where dv like '" + str(
                    dv) + "' order by zila_name) select zila_name|| ' (%)' from t")]
            zl_col.insert(0, 'National (%)')
        if dv != '%':
            div_name = __db_fetch_single_value(
                "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    facts_data = pandas.io.sql.read_sql(
        "select smm.sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,bagerhat_value, bandarban_value, barguna_value, barisal_value, bhola_value, bogra_value, brahmanbaria_value, chandpur_value, chittagong_value, chuadanga_value, comilla_value, cbazar_value, dhaka_value, dinajpur_value, faridpur_value, feni_value, gaibandha_value, gazipur_value, gopalganj_value, habiganj_value, jamalpur_value, jessore_value, jhalokati_value, jhenaidah_value, joypurhat_value, khagrachhari_value, khulna_value, kishorgonj_value, kurigram_value, kushtia_value, lakshmipur_value, lalmonirhat_value, madaripur_value, magura_value, manikganj_value, maulvibazar_value, meherpur_value, munshiganj_value, mymensingh_value, naogaon_value, narail_value, narayanganj_value, narsingdi_value, natore_value, nawabganj_value, netrakona_value, nilphamari_value, noakhali_value, pabna_value, panchagarh_value, patuakhali_value, pirojpur_value, rajbari_value, rajshahi_value, rangamati_value, rangpur_value, satkhira_value, shariatpur_value, sherpur_value, sirajganj_value, sunamganj_value, sylhet_value, tangail_value, thakurgaon_value from factsheet_data_district fdg left join sector_module_mapping smm on smm.module_id = fdg.module_id where fdg.round = 2 and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.sector_id,fdg.module_id,fdg.xindicator",
        connection)

    s_p = facts_data.rename(
        {"program": "Programme", "module": "Module", "indicator": "Indicator", "overall_value": "National (%)",
         "bagerhat_value": "Bagerhat (%)", "bandarban_value": "Bandarban (%)", "barguna_value": "Barguna (%)",
         "barisal_value": "Barishal (%)", "bhola_value": "Bhola (%)", "bogra_value": "Bogura (%)",
         "brahmanbaria_value": "Brahmanbaria (%)", "chandpur_value": "Chandpur (%)",
         "chittagong_value": "Chattogram (%)",
         "chuadanga_value": "Chuadanga (%)", "comilla_value": "Cumilla (%)", "cbazar_value": "Cox's Bazar (%)",
         "dhaka_value": "Dhaka (%)", "dinajpur_value": "Dinajpur (%)", "faridpur_value": "Faridpur (%)",
         "feni_value": "Feni (%)",
         "gaibandha_value": "Gaibandha (%)", "gazipur_value": "Gazipur (%)", "gopalganj_value": "Gopalganj (%)",
         "habiganj_value": "Habiganj (%)", "jamalpur_value": "Jamalpur (%)", "jessore_value": "Jashore (%)",
         "jhalokati_value": "Jhalokati (%)", "jhenaidah_value": "Jhenaidah (%)", "joypurhat_value": "Joypurhat (%)",
         "khagrachhari_value": "Khagrachhari (%)", "khulna_value": "Khulna (%)", "kishorgonj_value": "Kishoregonj (%)",
         "kurigram_value": "Kurigram (%)", "kushtia_value": "Kushtia (%)", "lakshmipur_value": "Lakshmipur (%)",
         "lalmonirhat_value": "Lalmonirhat (%)", "madaripur_value": "Madaripur (%)", "magura_value": "Magura (%)",
         "manikganj_value": "Manikganj (%)", "maulvibazar_value": "Moulvibazar (%)", "meherpur_value": "Meherpur (%)",
         "munshiganj_value": "Munshiganj (%)", "mymensingh_value": "Mymensingh (%)", "naogaon_value": "Naogaon (%)",
         "narail_value": "Narail (%)", "narayanganj_value": "Narayanganj (%)", "narsingdi_value": "Narsingdi (%)",
         "natore_value": "Natore (%)", "nawabganj_value": "Nawabganj (%)", "netrakona_value": "Netrokona (%)",
         "nilphamari_value": "Nilphamari (%)", "noakhali_value": "Noakhali (%)", "pabna_value": "Pabna (%)",
         "panchagarh_value": "Panchagarh (%)", "patuakhali_value": "Patuakhali (%)", "pirojpur_value": "Pirojpur (%)",
         "rajbari_value": "Rajbari (%)", "rajshahi_value": "Rajshahi (%)", "rangamati_value": "Rangamati (%)",
         "rangpur_value": "Rangpur (%)", "satkhira_value": "Satkhira (%)", "shariatpur_value": "Shariatpur (%)",
         "sherpur_value": "Sherpur (%)", "sirajganj_value": "Sirajganj (%)", "sunamganj_value": "Sunamganj (%)",
         "sylhet_value": "Sylhet (%)", "tangail_value": "Tangail (%)", "thakurgaon_value": "Thakurgaon (%)"
         }, axis='columns')

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[zl_col].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    if div_name == 'All Divisions' and sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name + '/ Division: ' + div_name

    return export_data_to_excel(s_p, 'factsheet_district_' + cur_time, str(sector_name) + '-' + str(div_name),
                                'district', page_heading)


@csrf_exempt
def pdf_factsheet_general(request):
    dv = '-99'
    zl = '-99'
    sector = '%'
    zila_name = 'All Districts'
    div_name = 'All Divisions'
    sector_name = 'All Programmes'

    if request.method == 'POST':
        dv = request.POST.get('dv')
        zl = request.POST.get('zl')
        sector = request.POST.get('sector')
        if dv != '-99':
            div_name = __db_fetch_single_value(
                "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
        if zl != '-99':
            zila_name = __db_fetch_single_value(
                "select zila_name from psu_mapping where zl like '" + str(zl) + "' limit 1")
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    facts_data = pandas.io.sql.read_sql(
        "with t as(select fdg.xindicator,sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,rural_value,urban_value from factsheet_data_general fdg left join sector_module_mapping smm on fdg.module_id = smm.module_id where fdg.round = 2 and fdg.dv like '" + str(
            dv) + "' and fdg.zl like '" + str(zl) + "' and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.sector_id,fdg.xindicator) select distinct on(t.xindicator) t.program,t.module,t.indicator,t.overall_value,t.rural_value,t.urban_value from t",
        connection)

    s_p = facts_data.rename(
        {'program': 'Program', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'Overall (%)',
         'rural_value': 'Rural (%)', 'urban_value': 'Urban (%)'}, axis='columns')

    s_p = s_p.set_index(['Program', 'Module', 'Indicator'])

    s_p = s_p[['Overall (%)', 'Rural (%)', 'Urban (%)']].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("onadata/apps/reportmodule/templates/reportmodule/pdf_report.html")

    if zila_name == 'All Districts' and div_name == 'All Divisions' and sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name + '/ Division: ' + div_name + '/ District: ' + zila_name

    # fatrami code
    olddfdata = s_p.to_html(classes='gen_table', header=False)

    tree = ET.fromstring(olddfdata, parser=ET.HTMLParser())

    tbody = tree.find(".//tbody")
    tablenode = tbody.getparent()

    tablenode.insert(tablenode.index(tbody) + 1, ET.XML(
        '<thead> <tr style="text-align: right;"> <th>Programme</th> <th>Module</th> <th>Indicator</th> <th>Overall(%)</th> <th>Rural (%)</th> <th>Urban (%)</th></tr></thead>'))

    newdfdata = ET.tostring(tree).replace('<html><body>', '').replace('</body></html>', '')
    # fatrami code

    template_vars = {"title": "Factsheet",
                     "heading": "Factsheet</br> (" + str(
                         page_heading) + ")",
                     "dataframe_data": newdfdata}

    html_out = template.render(template_vars)
    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    HTML(string=html_out).write_pdf('onadata/media/reports/factsheet_general' + '_' + cur_time + '.pdf',
                                    stylesheets=['onadata/apps/reportmodule/static/css/pdf_style.css'])

    return HttpResponse(json.dumps('/media/reports/factsheet_general' + '_' + cur_time + '.pdf'))


@csrf_exempt
def pdf_factsheet_division(request):
    dv = '%'
    divs_col = ['National (%)', 'Barishal (%)', 'Chattogram (%)', 'Dhaka (%)', 'Khulna (%)', 'Mymensingh (%)',
                'Rajshahi (%)', 'Rangpur (%)', 'Sylhet (%)']
    sector = '%'
    sector_name = 'Sector'
    if request.method == 'POST':
        divs_col = ['National (%)', 'Barishal (%)', 'Chattogram (%)', 'Dhaka (%)', 'Khulna (%)', 'Mymensingh (%)',
                    'Rajshahi (%)', 'Rangpur (%)',
                    'Sylhet (%)']
        sector = request.POST.get('sector')
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    facts_data = pandas.io.sql.read_sql(
        "select sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,barisal_value,chittagong_value,dhaka_value,khulna_value,mymensingh_value,rajshahi_value,rongpur_value,sylhet_value from factsheet_data_division fdg left join sector_module_mapping smm on smm.module_id = fdg.module_id where fdg.round = 2 and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.module_id,fdg.xindicator",
        connection)

    s_p = facts_data.rename(
        {'program': 'Programme', 'module': 'Module', 'indicator': 'Indicator', 'overall_value': 'National (%)',
         'barisal_value': 'Barishal (%)', 'chittagong_value': 'Chattogram (%)', 'dhaka_value': 'Dhaka (%)',
         'khulna_value': 'Khulna (%)',
         'mymensingh_value': 'Mymensingh (%)', 'rajshahi_value': 'Rajshahi (%)', 'rongpur_value': 'Rangpur (%)',
         'sylhet_value': 'Sylhet (%)'}, axis='columns')

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[divs_col].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("onadata/apps/reportmodule/templates/reportmodule/pdf_report.html")

    if sector_name == 'All Programmes':
        page_heading = 'National'
    else:
        page_heading = 'Programme: ' + sector_name

    # fatrami code
    olddfdata = s_p.to_html(classes='gen_table', header=False)

    tree = ET.fromstring(olddfdata, parser=ET.HTMLParser())

    tbody = tree.find(".//tbody")
    tablenode = tbody.getparent()

    tablenode.insert(tablenode.index(tbody) + 1, ET.XML(
        '<thead> <tr style="text-align: right;"> <th>Programme</th> <th>Module</th> <th>Indicator</th> <th>National (%)</th> <th>Barishal (%)</th> <th>Chattogram (%)</th> <th>Dhaka (%)</th> <th>Khulna (%)</th> <th>Mymensingh (%)</th> <th>Rajshahi (%)</th> <th>Rangpur (%)</th> <th>Sylhet (%)</th> </tr></thead>'))

    newdfdata = ET.tostring(tree).replace('<html><body>', '').replace('</body></html>', '')
    # fatrami code


    template_vars = {"title": "Factsheet",
                     "heading": "Factsheet - Division Comparision</br>(" + str(
                         page_heading) + ")",
                     "dataframe_data": newdfdata}

    html_out = template.render(template_vars)

    HTML(string=html_out).write_pdf('onadata/media/reports/factsheet_division' + '_' + cur_time + '.pdf',
                                    stylesheets=['onadata/apps/reportmodule/static/css/pdf_style.css'])

    return HttpResponse(json.dumps('/media/reports/factsheet_division' + '_' + cur_time + '.pdf'))


@csrf_exempt
def pdf_factsheet_district(request):
    dv = '%'
    zl_col = ["National (%)", "Bagerhat (%)", "Bandarban (%)", "Barguna (%)", "Barishal (%)", "Bhola (%)", "Bogura (%)",
              "Brahmanbaria (%)", "Chandpur (%)",
              "Chattogram (%)",
              "Chuadanga (%)", "Cumilla (%)", "Cox's Bazar (%)", "Dhaka (%)", "Dinajpur (%)", "Faridpur (%)",
              "Feni (%)", "Gaibandha (%)", "Gazipur (%)",
              "Gopalganj (%)", "Habiganj (%)", "Joypurhat (%)", "Jamalpur (%)", "Jashore (%)", "Jhalokati (%)",
              "Jhenaidah (%)", "Khagrachhari (%)",
              "Khulna (%)", "Kishoregonj (%)", "Kurigram (%)", "Kushtia (%)", "Lakshmipur (%)", "Lalmonirhat (%)",
              "Madaripur (%)", "Magura (%)",
              "Manikganj (%)", "Meherpur (%)", "Moulvibazar (%)", "Munshiganj (%)", "Mymensingh (%)", "Naogaon (%)",
              "Narail (%)", "Narayanganj (%)",
              "Narsingdi (%)", "Natore (%)", "Nawabganj (%)", "Netrokona (%)", "Nilphamari (%)", "Noakhali (%)",
              "Pabna (%)", "Panchagarh (%)",
              "Patuakhali (%)", "Pirojpur (%)", "Rajshahi (%)", "Rajbari (%)", "Rangamati (%)", "Rangpur (%)",
              "Shariatpur (%)", "Satkhira (%)",
              "Sirajganj (%)", "Sherpur (%)", "Sunamganj (%)", "Sylhet (%)", "Tangail (%)", "Thakurgaon (%)"]
    sector = '%'
    div_name = 'Division'
    sector_name = 'Sector'
    if request.method == 'POST':
        sector = request.POST.get('sector')
        dv = request.POST.get('dv')
        if dv:
            zl_col = [i[0] for i in __db_fetch_values(
                "with t as (select distinct zila_name from psu_mapping where dv like '" + str(
                    dv) + "' order by zila_name) select zila_name|| ' (%)' from t")]
            zl_col.insert(0, 'National (%)')

        if dv != '%':
            div_name = __db_fetch_single_value(
                "select div_name from psu_mapping where dv like '" + str(dv) + "' limit 1")
        if sector != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector) + "' limit 1")

    facts_data = pandas.io.sql.read_sql(
        "select smm.sector_name as program,(select substring(title from '%#(#\"%#\"#)%' for '#') from logger_xform where id = fdg.module_id) as module,(select chart_title from chart_list where xindicator = fdg.xindicator) as indicator,overall_value,bagerhat_value, bandarban_value, barguna_value, barisal_value, bhola_value, bogra_value, brahmanbaria_value, chandpur_value, chittagong_value, chuadanga_value, comilla_value, cbazar_value, dhaka_value, dinajpur_value, faridpur_value, feni_value, gaibandha_value, gazipur_value, gopalganj_value, habiganj_value, jamalpur_value, jessore_value, jhalokati_value, jhenaidah_value, joypurhat_value, khagrachhari_value, khulna_value, kishorgonj_value, kurigram_value, kushtia_value, lakshmipur_value, lalmonirhat_value, madaripur_value, magura_value, manikganj_value, maulvibazar_value, meherpur_value, munshiganj_value, mymensingh_value, naogaon_value, narail_value, narayanganj_value, narsingdi_value, natore_value, nawabganj_value, netrakona_value, nilphamari_value, noakhali_value, pabna_value, panchagarh_value, patuakhali_value, pirojpur_value, rajbari_value, rajshahi_value, rangamati_value, rangpur_value, satkhira_value, shariatpur_value, sherpur_value, sirajganj_value, sunamganj_value, sylhet_value, tangail_value, thakurgaon_value from factsheet_data_district fdg left join sector_module_mapping smm on smm.module_id = fdg.module_id where fdg.round = 2 and fdg.sector_id::text like '" + str(
            sector) + "' order by smm.sl_no,fdg.sector_id,fdg.module_id,fdg.xindicator",
        connection)

    s_p = facts_data.rename(
        {"program": "Programme", "module": "Module", "indicator": "Indicator", "overall_value": "National (%)",
         "bagerhat_value": "Bagerhat (%)", "bandarban_value": "Bandarban (%)", "barguna_value": "Barguna (%)",
         "barisal_value": "Barishal (%)", "bhola_value": "Bhola (%)", "bogra_value": "Bogura (%)",
         "brahmanbaria_value": "Brahmanbaria (%)", "chandpur_value": "Chandpur (%)",
         "chittagong_value": "Chattogram (%)",
         "chuadanga_value": "Chuadanga (%)", "comilla_value": "Cumilla (%)", "cbazar_value": "Cox's Bazar (%)",
         "dhaka_value": "Dhaka (%)", "dinajpur_value": "Dinajpur (%)", "faridpur_value": "Faridpur (%)",
         "feni_value": "Feni (%)",
         "gaibandha_value": "Gaibandha (%)", "gazipur_value": "Gazipur (%)", "gopalganj_value": "Gopalganj (%)",
         "habiganj_value": "Habiganj (%)", "jamalpur_value": "Jamalpur (%)", "jessore_value": "Jashore (%)",
         "jhalokati_value": "Jhalokati (%)", "jhenaidah_value": "Jhenaidah (%)", "joypurhat_value": "Joypurhat (%)",
         "khagrachhari_value": "Khagrachhari (%)", "khulna_value": "Khulna (%)", "kishorgonj_value": "Kishoregonj (%)",
         "kurigram_value": "Kurigram (%)", "kushtia_value": "Kushtia (%)", "lakshmipur_value": "Lakshmipur (%)",
         "lalmonirhat_value": "Lalmonirhat (%)", "madaripur_value": "Madaripur (%)", "magura_value": "Magura (%)",
         "manikganj_value": "Manikganj (%)", "maulvibazar_value": "Moulvibazar (%)", "meherpur_value": "Meherpur (%)",
         "munshiganj_value": "Munshiganj (%)", "mymensingh_value": "Mymensingh (%)", "naogaon_value": "Naogaon (%)",
         "narail_value": "Narail (%)", "narayanganj_value": "Narayanganj (%)", "narsingdi_value": "Narsingdi (%)",
         "natore_value": "Natore (%)", "nawabganj_value": "Nawabganj (%)", "netrakona_value": "Netrokona (%)",
         "nilphamari_value": "Nilphamari (%)", "noakhali_value": "Noakhali (%)", "pabna_value": "Pabna (%)",
         "panchagarh_value": "Panchagarh (%)", "patuakhali_value": "Patuakhali (%)", "pirojpur_value": "Pirojpur (%)",
         "rajbari_value": "Rajbari (%)", "rajshahi_value": "Rajshahi (%)", "rangamati_value": "Rangamati (%)",
         "rangpur_value": "Rangpur (%)", "satkhira_value": "Satkhira (%)", "shariatpur_value": "Shariatpur (%)",
         "sherpur_value": "Sherpur (%)", "sirajganj_value": "Sirajganj (%)", "sunamganj_value": "Sunamganj (%)",
         "sylhet_value": "Sylhet (%)", "tangail_value": "Tangail (%)", "thakurgaon_value": "Thakurgaon (%)"
         }, axis='columns')

    s_p = s_p.set_index(['Programme', 'Module', 'Indicator'])

    s_p = s_p[zl_col].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x), axis=1)

    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("onadata/apps/reportmodule/templates/reportmodule/pdf_report.html")

    template_vars = {"title": "Factsheet",
                     "heading": "Factsheet - District (" + str(
                         sector_name) + "/" + str(div_name) + ")",
                     "dataframe_data": s_p.to_html()}

    html_out = template.render(template_vars)

    HTML(string=html_out).write_pdf('onadata/media/reports/factsheet_district' + '_' + cur_time + '.pdf',
                                    stylesheets=['onadata/apps/reportmodule/static/css/pdf_style_district.css'])

    return HttpResponse(json.dumps('/media/reports/factsheet_district' + '_' + cur_time + '.pdf'))


@csrf_exempt
def generate_ranking(request, region_type):
    page_heading = ''
    module_id = '%'
    coverage_id = '%'
    sphtml = ''
    if region_type == 'division':
        reg_id = 1
    else:
        reg_id = 2
    module_list = __db_fetch_values_dict(
        "select id as module_id,substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id in (select module_id from sector_module_mapping where tanahashi_proc is not NULL) order by id_string asc")

    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        module_name = __db_fetch_single_value(
            "select substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id = " + str(
                module_id))
        coverage_id = request.POST.get('coverage_id')

        page_heading = '(Module: ' + module_name + '/' + 'Coverage: ' + coverage_id + ')'

        if module_id != '%' and coverage_id != '%':
            ranking_data = pandas.io.sql.read_sql(
                "select region_name,result_val,ranking from public.get_ranking_data(" + str(module_id) + ", '" + str(
                    coverage_id) + "'," + str(reg_id) + ")", connection)

            ranking_data = ranking_data.rename(
                {'region_name': region_type.title(), 'result_val': 'Result (%)', 'ranking': 'Ranking'}, axis='columns')

            # ranking_data = ranking_data.rename(columns=
            #     {'region_name': region_type.title(), 'result_val': 'Result', 'ranking': 'Ranking'})

            ranking_data[['Result (%)']] = ranking_data[['Result (%)']].apply(
                lambda x: map(lambda x: '{:.1f}'.format(x), x),
                axis=1)

            sphtml = ranking_data.to_html(classes=["table", "table-bordered", "table-hover"], index=False)

    return render(request, 'reportmodule/ranking_sheet.html', {
        'module_id': module_id,
        'coverage_id': coverage_id,
        'module_list': module_list,
        'region_type': region_type,
        'sphtml': sphtml,
        'page_heading': page_heading
    })


@csrf_exempt
def export_ranking(request):
    module_id = request.POST.get('module_id')
    module_name = __db_fetch_single_value(
        "select substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id = " + str(
            module_id))
    coverage_id = request.POST.get('coverage_id')
    region_type = request.POST.get('region_type')

    page_heading = '(Module: ' + module_name + '/' + 'Coverage: ' + coverage_id + ')'

    if region_type == 'division':
        reg_id = 1
    else:
        reg_id = 2

    ranking_data = pandas.io.sql.read_sql(
        "select region_name,result_val,ranking from public.get_ranking_data(" + str(module_id) + ", '" + str(
            coverage_id) + "'," + str(reg_id) + ")", connection)

    ranking_data = ranking_data.rename(
        {'region_name': region_type.title(), 'result_val': 'Result (%)', 'ranking': 'Ranking'}, axis='columns')

    ranking_data[['Result (%)']] = ranking_data[['Result (%)']].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x),
                                                                      axis=1)
    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    return export_data_to_excel(ranking_data, 'Ranking_' + region_type.title() + '_' + cur_time, 'ranking', 'ranking',
                                page_heading)


@csrf_exempt
def pdf_ranking(request):
    module_id = request.POST.get('module_id')
    module_name = __db_fetch_single_value(
        "select substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id = " + str(
            module_id))
    coverage_id = request.POST.get('coverage_id')
    region_type = request.POST.get('region_type')

    page_heading = '(Module: ' + module_name + '/' + 'Coverage: ' + coverage_id + ')'

    if region_type == 'division':
        reg_id = 1
    else:
        reg_id = 2

    ranking_data = pandas.io.sql.read_sql(
        "select region_name,result_val,ranking from public.get_ranking_data(" + str(module_id) + ", '" + str(
            coverage_id) + "'," + str(reg_id) + ")", connection)

    ranking_data = ranking_data.rename(
        {'region_name': region_type.title(), 'result_val': 'Result (%)', 'ranking': 'Ranking'}, axis='columns')

    # ranking_data = ranking_data.rename(columns=
    #     {'region_name': region_type.title(), 'result_val': 'Result', 'ranking': 'Ranking'})

    ranking_data[['Result (%)']] = ranking_data[['Result (%)']].apply(lambda x: map(lambda x: '{:.1f}'.format(x), x),
                                                                      axis=1)
    cur_time = "{:%Y_%m_%d_%H_%M_%S}".format(datetime.datetime.now())

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("onadata/apps/reportmodule/templates/reportmodule/pdf_report.html")

    template_vars = {"title": "Ranking",
                     "heading": "Factsheet - Ranking (" + region_type.title() + ")</br>" + str(
                         page_heading) + "",
                     "dataframe_data": ranking_data.to_html(index=False, classes='rank_table')}

    html_out = template.render(template_vars)

    HTML(string=html_out).write_pdf('onadata/media/reports/factsheet_district' + '_' + cur_time + '.pdf',
                                    stylesheets=['onadata/apps/reportmodule/static/css/pdf_style.css'])

    return HttpResponse(json.dumps('/media/reports/factsheet_district' + '_' + cur_time + '.pdf'))


@csrf_exempt
def inicator_map(request):
    sector_id = '%'
    sector_name = 'All Programmes'
    module_id = '%'
    module_name = 'All Modules'
    indicator_id = '%'
    indicator_name = 'All indicators'
    dist_dict = {}
    indicator_type = 'p'
    dist_map = {"Bagerhat": "bagerhat_value", "Bandarban": "bandarban_value", "Barguna": "barguna_value",
                "Barishal": "barisal_value", "Bhola": "bhola_value", "Bogura": "bogra_value",
                "Brahmanbaria": "brahmanbaria_value", "Chandpur": "chandpur_value", "Chattogram": "chittagong_value",
                "Chuadanga": "chuadanga_value", "Cox's Bazar": "cbazar_value", "Cumilla": "comilla_value",
                "Dhaka": "dhaka_value", "Dinajpur": "dinajpur_value", "Faridpur": "faridpur_value",
                "Feni": "feni_value", "Gaibandha": "gaibandha_value", "Gazipur": "gazipur_value",
                "Gopalganj": "gopalganj_value", "Habiganj": "habiganj_value", "Jamalpur": "jamalpur_value",
                "Jashore": "jessore_value", "Jhalokati": "jhalokati_value", "Jhenaidah": "jhenaidah_value",
                "Joypurhat": "joypurhat_value", "Khagrachhari": "khagrachhari_value", "Khulna": "khulna_value",
                "Kishoregonj": "kishorgonj_value", "Kurigram": "kurigram_value", "Kushtia": "kushtia_value",
                "Lakshmipur": "lakshmipur_value", "Lalmonirhat": "lalmonirhat_value", "Madaripur": "madaripur_value",
                "Magura": "magura_value", "Manikganj": "manikganj_value", "Moulvibazar": "maulvibazar_value",
                "Meherpur": "meherpur_value", "Munshiganj": "munshiganj_value", "Mymensingh": "mymensingh_value",
                "Naogaon": "naogaon_value", "Narail": "narail_value", "Narayanganj": "narayanganj_value",
                "Narsingdi": "narsingdi_value", "Natore": "natore_value", "Nawabganj": "nawabganj_value",
                "Netrokona": "netrakona_value", "Nilphamari": "nilphamari_value", "Noakhali": "noakhali_value",
                "Pabna": "pabna_value", "Panchagarh": "panchagarh_value", "Patuakhali": "patuakhali_value",
                "Pirojpur": "pirojpur_value", "Rajbari": "rajbari_value", "Rajshahi": "rajshahi_value",
                "Rangamati": "rangamati_value", "Rangpur": "rangpur_value", "Satkhira": "satkhira_value",
                "Shariatpur": "shariatpur_value", "Sherpur": "sherpur_value", "Sirajganj": "sirajganj_value",
                "Sunamganj": "sunamganj_value", "Sylhet": "sylhet_value", "Tangail": "tangail_value",
                "Thakurgaon": "thakurgaon_value"}
    sector_list = __db_fetch_values_dict(
        "select distinct sector_id,sector_name from sector_module_mapping order by sector_id asc")
    module_list = []
    indicator_list = []
    if request.method == 'POST':
        sector_id = request.POST.get('sector')
        if sector_id != '%':
            sector_name = __db_fetch_single_value(
                "select sector_name from sector_module_mapping where sector_id::text like '" + str(
                    sector_id) + "' limit 1")
        module_id = request.POST.get('module_id')
        if module_id != '%':
            module_name = __db_fetch_single_value(
                "select substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id_string = '" + str(
                    module_id) + "'")
        indicator_id = request.POST.get('indicator_id')
        if indicator_id != '%':
            indicator_name = __db_fetch_single_value(
                "select chart_title from chart_list where xindicator = '" + str(indicator_id) + "'")

        indicator_type = __db_fetch_single_value(
            "select indicator_type from chart_list where xindicator = '" + indicator_id + "'")

        module_list = __db_fetch_values_dict(
            "select (select id_string from logger_xform where id = module_id) as module_id,(select substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id = module_id) from sector_module_mapping where sector_id = " + str(
                sector_id))

        indicator_list = __db_fetch_values_dict(
            "select xindicator,chart_title from chart_list where sub_module = '" + module_id + "' and ctype = 'gauge' order by xindicator ASC")

        ind_vals = pandas.io.sql.read_sql(
            "select * from factsheet_data_district where xindicator = '" + indicator_id + "' limit 1", connection)
        dis_vals = ind_vals.iloc[0]

        dist_dict['National'] = dis_vals['overall_value']
        for idx in dist_map:
            dist_dict[idx] = round(dis_vals[dist_map[idx]], 1)

    if sector_name == 'All Programmes' and module_name == 'All Modules' and indicator_name == 'All indicators':
        page_heading = ''
    else:
        page_heading = '<table class="table table-striped"><tbody><tr><th>Programme</th><td>' + str(
            sector_name) + '</td></tr><tr><th>Module</th><td>' + str(
            module_name) + '</td></tr><tr><th>Indicator</th><td>' + str(indicator_name) + '</td></tr></tbody></table>'

    return render(request, 'reportmodule/fact_sheet_map.html', {
        'indicator_list': indicator_list,
        'module_list': module_list,
        'sector_id': sector_id,
        'module_id': module_id,
        'indicator_id': indicator_id,
        'sector_list': sector_list,
        'dist_dict': json.dumps(dist_dict),
        'indicator_type': indicator_type,
        'page_heading': page_heading
    })


@csrf_exempt
def get_modules_by_sector(request):
    sector = request.POST.get('sector')
    module_list = __db_fetch_values_dict(
        "select (select id_string from logger_xform where id = module_id) as module_id,(select substring(title from '%#(#\"%#\"#)%' for '#') as module_name from logger_xform where id = module_id) from sector_module_mapping where sector_id = " + str(
            sector))
    return HttpResponse(json.dumps(module_list))


@csrf_exempt
def get_indicator_list_by_module(request):
    module_id = request.POST.get('module_id')
    indicator_list = __db_fetch_values_dict(
        "select xindicator,chart_title from chart_list where sub_module = '" + module_id + "' and ctype = 'gauge' order by xindicator ASC")
    return HttpResponse(json.dumps(indicator_list))

