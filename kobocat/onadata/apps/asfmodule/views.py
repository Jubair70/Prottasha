from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (
    HttpResponseForbidden, HttpResponseRedirect, HttpResponseNotFound,
    HttpResponseBadRequest, HttpResponse)
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
from django.shortcuts import render
import numpy
import time
import datetime
from django.core.files.storage import FileSystemStorage

from django.core.urlresolvers import reverse
import pandas as pd

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
from django.template.loader import render_to_string
import os
from onadata.apps.usermodule.views import error_page
import decimal
from pyfcm import FCMNotification

# FOR Export
from onadata.libs.utils.user_auth import has_permission, get_xform_and_perms, \
    helper_auth_helper, has_edit_permission

from onadata.libs.utils.export_tools import (
    generate_export,
    should_create_new_export,
    kml_export_data,
    newset_export_for)
from onadata.apps.viewer.models.export import Export
from onadata.libs.utils.logger_tools import response_with_mimetype_and_name, \
    disposition_ext_and_date
from onadata.libs.exceptions import NoRecordsFoundError
from onadata.apps.usermodule.views_project import get_own_and_partner_orgs_usermodule_users, get_permissions

push_service = FCMNotification(api_key="AIzaSyAel9fbkTbt1Ms6-eka5QFuMotyw_0bKeE")


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


def quryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchone()
    cursor.close()
    return value


def index(request):
    id_string = 'child_marriage_prevention_reg'
    query = "SELECT id, uuid  FROM logger_xform where id_string = 'child_marriage_prevention_reg'"
    queryResult = quryExecution(query)
    xform_id = queryResult[0]
    form_uuid = str(queryResult[1])
    username = request.user.username
    select_data = json.dumps(__db_fetch_values_dict(
        "select replace(field_name,'/','__') as field_name,value_text,value_label as bn_label from xform_extracted where xform_id = (select id from public.logger_xform where id_string = '" + str(
            id_string) + "') and field_type in ('select one','select all that apply') "))
    print()
    return render(request, "asfmodule/index.html",
                  {'id_string': id_string, 'xform_id': xform_id,
                   'form_uuid': form_uuid, 'username': username, 'select_data': select_data,
                   })
    # return render(request, 'asfmodule/index.html')


def profile_view(request, victim_id):
    current_user = UserModuleProfile.objects.get(user_id=request.user.id)
    role = UserRoleMap.objects.get(user=current_user.pk)
    role_id = role.role.pk
    query = """ SELECT distinct '<div class="row"> <div class="col-lg-11"> <div class="clearfix"></div> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default"><div class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a> </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a ng-click="load_forms_list('|| category_id ||')"  class="btn btn-success" id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  >Forms</a>' else '' end  ||'</div>' as form_str FROM rolewiseform rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id AND role_id = """ + str(
        role_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)

    id_string = 'child_marriage_prevention_reg'
    query = "SELECT id, uuid  FROM logger_xform where id_string = 'child_marriage_prevention_reg'"
    queryResult = quryExecution(query)
    xform_id = queryResult[0]
    form_uuid = str(queryResult[1])
    username = request.user.username

    return render(request, 'asfmodule/profile_view_test.html',
                  {'main_str': main_str, 'victim_id': victim_id, 'id_string': id_string, 'xform_id': xform_id,
                   'form_uuid': form_uuid, 'username': username})


@login_required
def delete_data(request):
    form_id = request.GET.get('form_id')
    log_ins_id = request.GET.get('log_ins_id')
    redirect_url = request.GET.get('redirect_url')
    query = "update logger_instance set deleted_at = now() where id = " + str(log_ins_id)
    __db_commit_query(query)
    print type(form_id)
    if int(form_id) in [684, 704, 714, 715, 747, 748, 751]:
        ben_id = __db_fetch_single_value(
            "select json->>'victim_tbl_id' as ben_id from logger_instance where id = " + str(log_ins_id))
        if ben_id:
            form_func_data = __db_fetch_values_dict("""
            with t3 as (with t2 as(with t as(select id,json->>'victim_tbl_id' as victim_tbl_id,xform_id from logger_instance where deleted_at is null)
         select id,xform_id from t where victim_tbl_id = '""" + str(ben_id) + """'
         union all
         select case_id::int, 703 as xform_id from asf_victim where id = """ + str(ben_id) + """)
         select id,xform_id from t2 where xform_id in (select form_id from form_function))
         select t3.*,form_function.function_name from t3
         left join form_function
         on form_function.form_id = t3.xform_id
         order by t3.id asc
            """)
            if form_func_data:
                __db_commit_query(
                    "update asf_victim set social_reintegration_id = null, services_reintegration_plan_id = null, referral_id = null, referral_services_for = null, referral_type = null, referral_organization_type = null, referral_followup_id = null, psychosocial_assessment_id = null, psychosocial_problem_identified = null, psychosocial_followup_id = null, direct_inkind_support_id = null, inkind_support_received = null where id = " + str(
                        ben_id))
                for ffd in form_func_data:
                    __db_commit_query("select " + str(ffd['function_name']) + "(" + str(ffd['id']) + ")")

    messages.success(request, '<i class="fa fa-check-circle"></i> Data has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect(redirect_url)


@csrf_exempt
def get_forms_data(request):
    category_id = request.POST.get('category_id')
    victim_id = request.POST.get('victim_id')
    user_id = request.user.id
    query = """ WITH t AS(SELECT (SELECT title FROM logger_xform WHERE id = form_id), form_id,rf.can_edit,rf.can_delete FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND category_id = """ + str(
        category_id) + """ AND fc.form_id = rf.xform_id AND user_id = """ + str(
        user_id) + """) , t1 AS (SELECT logger_instance.id log_ins_id, json ->> 'victim_tbl_id' :: text victim_id, * FROM t, logger_instance WHERE t.form_id = logger_instance.xform_id and deleted_at is null ORDER BY date_created ASC) SELECT '<div class="panel panel-default" ><div class="panel-heading forms_data_panel_heading" role="tab" id="heading' ||log_ins_id ||'"><h4 class="panel-title forms_data_panel_title"><a id="data_id_' ||log_ins_id ||'" class="collapsed" onclick="load_forms_data(' ||log_ins_id ||',''data_view' || log_ins_id ||''',1)" role="button" data-toggle="collapse" href="#collapse' || log_ins_id ||'" aria-expanded="false" aria-controls="collapse' ||log_ins_id ||'">' || To_char(date_created :: DATE, 'DD/MM/YYYY') ||'</a><span style="margin-left:30%">' || Replace(Greatest(title, Rpad(title, 32, ' ')) :: text, ' ', '&nbsp;') ||'</span>' || case when can_edit = 1 then '<a onclick="load_forms_edit_mode(' || xform_id ||',' || log_ins_id || ')" class="pull-right" style="cursor:pointer;margin-right: -5px;margin-left: 11px;" data-toggle="modal" data-target="#myModal"><i class="fa fa-pencil"></i></a>' else '' end || case when can_delete = 1 then '<a onclick="delete_forms_data(' || xform_id ||',' || log_ins_id || ')" class="pull-right" style="cursor:pointer" data-toggle="modal" data-target="#myModal"><i class="fa fa-trash"></i></a>' else '' end || '</h4></div><div id="collapse' || log_ins_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading' || log_ins_id ||'"><div class="panel-body"><div class="ribbon" id="data_view' || log_ins_id ||'"></div></div></div></div>' AS form_str FROM t1 WHERE victim_id LIKE '%""" + str(
        victim_id) + """%' """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    return HttpResponse(main_str)


@csrf_exempt
def get_data_view(request):
    username = request.user
    logger_id = request.POST.get('logger_id')
    query = """ select * from public.get_data_detail_view(""" + str(logger_id) + """) order by  _re_sl,_sl_no """
    form_data_matrix = json.dumps(__db_fetch_values_dict(query))
    root = "root" + str(logger_id)
    rendered = render_to_string('asfmodule/data_view.html', {
        'form_data_matrix': form_data_matrix,
        'username': username,
        'root': root
    })
    rendered = json.dumps(rendered)
    # print(rendered)
    return HttpResponse(rendered)


@csrf_exempt
def get_forms_list(request):
    category_id = request.POST.get('category_id')
    victim_id = request.POST.get('victim_id')
    user_id = request.user.id
    query = """  WITH t
             AS (SELECT (SELECT title
                         FROM   logger_xform
                         WHERE  id = form_id),
                        form_id,
                        category_id,
                        orders,
                        submission_times
                 FROM   vwrolewiseformpermission rf,
                        forms_categories_relation fc
                 WHERE  ( rf.can_submit = 1 )
                        AND category_id = """ + str(category_id) + """
                        AND fc.form_id = rf.xform_id
                        AND user_id = """ + str(user_id) + """),
             fre
             AS (SELECT xform_id,
                        Count(id) frequency
                 FROM   logger_instance
                 WHERE  ( json ->> 'victim_tbl_id' ) :: INT = """ + str(victim_id) + """
                        AND deleted_at IS NULL
                        AND xform_id = ANY (SELECT form_id
                                            FROM   t)
                 GROUP  BY xform_id),
             t1
             AS (SELECT CASE
                          WHEN (t.form_id = ANY (SELECT form_id
                                                FROM   forms_categories_relation
                                                WHERE  submission_times = 1)
                               AND Coalesce(frequency, 0) < submission_times)
                                THEN
        '<a class="btn btn-outline form-group form-control" onclick="load_forms_html('
        || form_id
        || ')" >'
        || title
        || '</a><br>'
        WHEN t.form_id = ANY (SELECT form_id
                              FROM   forms_categories_relation
                              WHERE  submission_times = 1)
             AND Coalesce(frequency, 0) >= submission_times THEN ''
        when (t.form_id::int = (select id from logger_xform where id_string = 'referral_followup') and (select count(*) from vw_referral where  ("json"->>'victim_tbl_id')::int = """ + str(
        victim_id) + """ limit 1 ) = 0) then ''
        when  (t.form_id = (select id from logger_xform where id_string = 'reintegration_sustainability') and (select count(*) from vw_reintegration_sustainability where report_month =  case
        when to_char(now(),'MM')::int between 1 and 3 then to_char(now(),'YYYY') || '-03-31'
        when to_char(now(),'MM')::int between 4 and 6 then to_char(now(),'YYYY') || '-06-30'
        when to_char(now(),'MM')::int between 7 and 9 then to_char(now(),'YYYY') || '-09-30'
        when to_char(now(),'MM')::int between 10 and 12 then to_char(now(),'YYYY') || '-12-30'
        end  and victim_tbl_id = """ + str(victim_id) + """ limit 1 ) > 0)
        then ''
        ELSE
        '<a class="btn btn-outline form-group form-control" onclick="load_forms_html('
        || form_id
        || ')" >'
        || title
        || '</a><br>'
        END AS popup_str
         FROM   t
                left join fre
                       ON t.form_id = fre.xform_id
         ORDER  BY category_id,
                   orders)
        SELECT *
        FROM   t1  """
    print(query)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    # main_str = """ <ul class="list-group"> """
    # for each in df['popup_str']:
    #     main_str += """ <li class="list-group-item"> """ + str(each) + """ </li> """
    # main_str += """ </ul> """
    main_str = ""
    for each in df['popup_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    return HttpResponse(main_str)


@csrf_exempt
def get_events_forms_list(request):
    category_id = request.POST.get('category_id')
    event_id = request.POST.get('event_id')
    user_id = request.user.id
    query = """  WITH t AS(SELECT (SELECT title FROM logger_xform WHERE id = form_id), form_id, category_id, orders, submission_times FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_submit = 1) AND category_id = """ + str(
        category_id) + """ AND fc.form_id = rf.xform_id AND user_id = """ + str(
        user_id) + """), fre as (select xform_id,count(id) frequency from logger_instance where (json->>'event_id')::int = """ + str(
        event_id) + """ and deleted_at is null and xform_id = any(select form_id from t) group by xform_id ), t1 AS (select case when t.form_id = any(select form_id from forms_categories_relation where submission_times = 1 ) and coalesce(frequency,0) < submission_times and Now() :: DATE >=(SELECT ( json ->> 'event/event_start_time') :: DATE event_date FROM logger_instance WHERE id = """ + str(
        event_id) + """ AND deleted_at IS NULL) then '<a class="btn btn-outline form-group form-control" onclick="load_forms_html(' || form_id || ')" >' || title || '</a><br>' when t.form_id = any(select form_id from forms_categories_relation where submission_times = 1 ) and coalesce(frequency,0) >= submission_times or now()::date < (SELECT (json->>'event/event_start_time')::date event_date from logger_instance WHERE  id = """ + str(
        event_id) + """ AND deleted_at IS NULL) then '' else '<a class="btn btn-outline form-group form-control" onclick="load_forms_html(' || form_id || ')" >' || title || '</a><br>' end AS popup_str FROM t left join fre on t.form_id = fre.xform_id ORDER BY category_id, orders) SELECT * FROM t1 """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    # print(query)
    # main_str = """ <ul class="list-group"> """
    # for each in df['popup_str']:
    #     main_str += """ <li class="list-group-item"> """ + str(each) + """ </li> """
    # main_str += """ </ul> """
    main_str = ""
    for each in df['popup_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    return HttpResponse(main_str)


@csrf_exempt
def get_forms_html(request):
    form_id = request.GET.get('form_id')
    query = """ select *,(select title from logger_xform where id = form_id limit 1) from odk_web_forms_html where form_id =  """ + str(
        form_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    form_html = df.form_html.tolist()[0]
    dom_tree = df.dom_tree.tolist()[0]
    angular_containers = df.angular_containers.tolist()[0]
    title = df.title.tolist()[0]
    data = {
        'form_html': form_html,
        'dom_tree': dom_tree,
        'angular_containers': angular_containers,
        'title': title

    }
    return HttpResponse(json.dumps(data))


@csrf_exempt
def get_districts(request):
    field_parent_id = request.POST.get('div')
    query = "select id,geocode,field_name from geo_data where field_type_id = 86 and field_parent_id = (select id from geo_data where geocode = '" + str(
        field_parent_id) + "')"
    print(query)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@csrf_exempt
def get_upazilas(request):
    field_parent_id = request.POST.get('dist')
    query = "select id,geocode,field_name from geo_data where field_type_id = 88 and field_parent_id = (select id from geo_data where geocode = '" + str(
        field_parent_id) + "')"
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@csrf_exempt
def get_unions(request):
    field_parent_id = request.POST.get('upz')
    query = "select id,geocode,field_name from geo_data where field_type_id = 89 and field_parent_id = (select id from geo_data where geocode = '" + str(
        field_parent_id) + "')"
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


@csrf_exempt
def get_wards(request):
    field_parent_id = request.POST.get('uni')
    query = "select id,geocode,field_name from geo_data where field_type_id = 92 and field_parent_id = " + str(
        field_parent_id)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


def incident_id_generator():
    current_year = datetime.datetime.now().year
    # current year last incident id
    qry = "select incident_id::bigint from asf_case where date_part('year', created_at)='" + str(
        current_year) + "' order by id desc"
    df = pandas.read_sql(qry, connection)
    if not df.empty:
        incident_id = df.incident_id.tolist()[0]
        incident_id += 1
    else:
        incident_id = str(current_year) + '001'
    return incident_id


@login_required
def case_list(request):
    query = "select geocode as id ,field_name from geo_data where field_type_id = 85 order by geocode"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    query = "select id,status from iom_status"
    df = pandas.read_sql(query, connection)
    status_list = zip(df.id.tolist(), df.status.tolist())
    rsc_list = __db_fetch_values_dict("select * from usermodule_rsc")
    return render(request, 'asfmodule/case_list.html',
                  {'divisions': divisions, 'status_list': status_list, 'rsc_list': rsc_list})


@login_required
def delete_case(request, victim_tbl_id):
    qry = "select update_deleted_at_case(" + str(victim_tbl_id) + ")"
    __db_fetch_single_value(qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> Data has been deleted successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_list/')


@csrf_exempt
def get_case_list(request):
    rsc_id = request.POST.get('rsc_id')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    gender = request.POST.get('gender')
    status = request.POST.get('status')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = "with finaltbl as(SELECT COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = 703 limit 1),0) can_delete,( SELECT ( SELECT role FROM PUBLIC.usermodule_organizationrole WHERE id = role_id limit 1)role_name FROM usermodule_userrolemap WHERE user_id = ( SELECT id FROM usermodule_usermoduleprofile WHERE user_id= " + str(
            user_id) + ")  limit 1), id, case_id,( SELECT incident_id FROM asf_case WHERE id = case_id::int limit 1) iom_case_no, victim_name, CASE WHEN sex = '1' THEN 'Male' WHEN sex = '2' THEN 'Female' ELSE 'Other' END sex, COALESCE(victim_age,'') victim_age, COALESCE(victim_id,'') returnee_id, ( SELECT ( SELECT status FROM iom_status WHERE id = asf_case.status::int limit 1) status FROM asf_case WHERE id = case_id::int limit 1) status, to_char( ( SELECT created_at::date FROM asf_case WHERE id = case_id::int limit 1),'DD/MM/YYYY') case_initation_date, iom_reference,coalesce((select username from auth_user where id = (select assaign_to::int from asf_case where id = case_id::int limit 1)),'') assaign_to,coalesce(contact_self,'') contact_self,coalesce(contact_emergency,'')contact_emergency,(select (select username from auth_user where id = created_by) from asf_case where id = asf_victim.case_id::int) case_initiator,(select get_profile_completion_date(asf_victim.id::text)) as profile_completion_date,(select rsc from vw_victim where id = asf_victim.id) as rsc FROM asf_victim WHERE created_at:: date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(
            to_date) + "','DD/MM/YYYY') AND deleted_at is null and sex LIKE '" + str(
            gender) + "' AND case_id::int = ANY ( SELECT id FROM (with t as(select district as geo_id,* from asf_case) select t.*,rsc_catchment_area.rsc_id::text from t left join rsc_catchment_area on rsc_catchment_area.geo_id::text = t.geo_id where t.id in (select id from logger_instance where xform_id = 703 and deleted_at is null)) case_final WHERE division LIKE '" + str(
            division) + "' AND district LIKE '" + str(district) + "' AND upazila LIKE '" + str(
            upazila) + "' AND status LIKE '" + str(
            status) + "' and rsc_id like '" + str(
            rsc_id) + "' and upazila in ((select (SELECT geocode FROM geo_data WHERE id = geoid limit 1) from usermodule_catchment_area where user_id = " + str(
            user_id) + ") union (select geocode from geo_data where field_parent_id = any (select geoid from usermodule_catchment_area where user_id = " + str(
            user_id) + ") and field_type_id = 88))) order by id desc) select can_delete,role_name,id,case_id,iom_case_no,victim_name,sex,victim_age, case when status in ('New Case','Assigned Profiling') then '' else returnee_id end as returnee_id,status,case_initation_date,iom_reference,assaign_to,contact_self,contact_emergency,case_initiator,coalesce(profile_completion_date,'') as profile_completion_date,rsc from finaltbl"
    except Exception:
        query = "with finaltbl as(select COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = 703 limit 1),0) can_delete, (select (SELECT role FROM public.usermodule_organizationrole WHERE id = role_id limit 1)role_name  from usermodule_userrolemap where user_id = (select id from usermodule_usermoduleprofile where user_id= " + str(
            user_id) + ")  limit 1),id,case_id,(select incident_id from asf_case where id = case_id::int limit 1) iom_case_no, victim_name,case when sex = '1' then 'Male' when sex = '2' then 'Female' else 'Other' end sex,coalesce(victim_age,'') victim_age, coalesce(victim_id,'') returnee_id,(select (select status from iom_status where id = asf_case.status::int limit 1) status from asf_case where id = case_id::int limit 1) status, to_char((select created_at::date from asf_case where id = case_id::int limit 1),'DD/MM/YYYY') case_initation_date,iom_reference,coalesce((select username from auth_user where id = (select assaign_to::int from asf_case where id = case_id::int limit 1)),'') assaign_to,coalesce(contact_self,'') contact_self,coalesce(contact_emergency,'')contact_emergency,(select (select username from auth_user where id = created_by) from asf_case where id = asf_victim.case_id::int) case_initiator,(select get_profile_completion_date(asf_victim.id::text)) as profile_completion_date,(select rsc from vw_victim where id = asf_victim.id) as rsc from asf_victim where created_at:: date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(
            to_date) + "','DD/MM/YYYY') AND  deleted_at is null and  sex like '" + str(
            gender) + "' and case_id::int = any(select id from (with t as(select district as geo_id,* from asf_case) select t.*,rsc_catchment_area.rsc_id::text from t left join rsc_catchment_area on rsc_catchment_area.geo_id::text = t.geo_id where t.id in (select id from logger_instance where xform_id = 703 and deleted_at is null)) case_final where division like '" + str(
            division) + "' and district like '" + str(district) + "' and upazila like '" + str(
            upazila) + "' and status like '" + str(status) + "'  and rsc_id like '" + str(
            rsc_id) + "') order by id desc) select can_delete,role_name,id,case_id,iom_case_no,victim_name,sex,victim_age, case when status in ('New Case','Assigned Profiling') then '' else returnee_id end as returnee_id,status,case_initation_date,iom_reference,assaign_to,contact_self,contact_emergency,case_initiator,coalesce(profile_completion_date,'') as profile_completion_date,rsc from finaltbl"

    case_info = __db_fetch_values_dict("""with t2 as(with t as(with t1 as(select asf_case.status from asf_case
            inner join asf_victim
            on asf_victim.case_id::int4 = asf_case.id
            left join rsc_catchment_area
            on rsc_catchment_area.geo_id::text = asf_case.district
            where asf_case.id in (select id from logger_instance where xform_id = 703 and deleted_at is null)
            and DATE(asf_victim.created_at) between symmetric to_date('""" + str(
        from_date) + """','DD/MM/YYYY') and to_date('""" + str(to_date) + """','DD/MM/YYYY')
            and asf_case.status like '""" + str(status) + """'
            and asf_victim.sex like '""" + str(gender) + """'
            and asf_case.division like '""" + str(division) + """'
            and asf_case.district like '""" + str(district) + """'
            and asf_case.upazila like '""" + str(upazila) + """'
            and rsc_catchment_area.rsc_id::text like '""" + str(rsc_id) + """')
            select status,count(*) as cnt from t1
            group by status)
            select iom_status.status,coalesce(cnt,0) as cnt from t
            right join iom_status
            on iom_status.id = t.status::int4)
            select 'Total Case' as status, sum(cnt) as cnt from t2
            union all
            select * from t2
        """)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    ret_obj = {'case_data': data, 'case_info': case_info}
    return HttpResponse(json.dumps(ret_obj, default=decimal_date_default))


@login_required
def add_case_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='returnee_case_initiation'")
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    return render(request, 'asfmodule/add_case_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server})


@login_required
def insert_case_form(request):
    incident_id = request.POST.get('incident_id')
    incident_date = request.POST.get('incident_date')
    incident_description = request.POST.get('incident_description')
    incident_rural_or_urban = request.POST.get('incident_rural_or_urban')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    ward = request.POST.get('ward')
    incidence_address = request.POST.get('incidence_address')
    incidence_post_office = request.POST.get('incidence_post_office')
    information_source = request.POST.get('information_source')
    source_organization_name = request.POST.get('source_organization_name')
    source_name = request.POST.get('source_name')
    source_designation = request.POST.get('source_designation')
    source_address = request.POST.get('source_address')
    source_phone = request.POST.get('source_phone')
    print_media_name = request.POST.get('print_media_name')
    print_media_page_number = request.POST.get('print_media_page_number')
    print_media_reporter_name = request.POST.get('print_media_reporter_name')
    print_media_publishing_date = request.POST.get('print_media_publishing_date')
    electronic_media_name = request.POST.get('electronic_media_name')
    electronic_media_telecast_date = request.POST.get('electronic_media_telecast_date')
    incident_type = request.POST.get('incident_type')
    burn_type = request.POST.get('burn_type')
    incident_cause = request.POST.get('incident_cause')
    people_affected = request.POST.get('people_affected')
    people_died = request.POST.get('people_died')
    if request.FILES:
        myfile = request.FILES['coverage_picture']
        url = "onadata/media/uploaded_files/"
        userName = request.user
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        coverage_picture = "onadata/media/uploaded_files/" + myfile.name
    else:
        coverage_picture = ''

    victim_id_list = request.POST.getlist('victim_id')
    victim_name_list = request.POST.getlist('victim_name')
    victim_sex_list = request.POST.getlist('victim_sex')
    victim_contact_list = request.POST.getlist('victim_contact')
    victim_address_list = request.POST.getlist('victim_address')

    created_by = request.user.id

    insert_qry = "INSERT INTO public.asf_case(incident_id, incident_date, incident_description, incident_rural_or_urban, division, district, upazila, union_id, ward, incidence_address, incidence_post_office, information_source, source_organization_name, source_name, source_designation, source_address, source_phone, print_media_name, print_media_page_number, print_media_reporter_name, print_media_publishing_date, electronic_media_name, electronic_media_telecast_date, coverage_picture, incident_type, burn_type, incident_cause, people_affected, people_died, created_by,status) values ('" + str(
        incident_id) + "', '" + str(incident_date) + "' , '" + str(incident_description) + "', '" + str(
        incident_rural_or_urban) + "', '" + str(division) + "', '" + str(district) + "', '" + str(
        upazila) + "', '" + str(union) + "', '" + str(ward) + "', '" + str(incidence_address) + "', '" + str(
        incidence_post_office) + "', '" + str(information_source) + "', '" + str(
        source_organization_name) + "', '" + str(source_name) + "', '" + str(source_designation) + "', '" + str(
        source_address) + "', '" + str(source_phone) + "', '" + str(print_media_name) + "', '" + str(
        print_media_page_number) + "', '" + str(print_media_reporter_name) + "', '" + str(
        print_media_publishing_date) + "', '" + str(electronic_media_name) + "', '" + str(
        electronic_media_telecast_date) + "', '" + str(coverage_picture) + "', '" + str(incident_type) + "', '" + str(
        burn_type) + "', '" + str(incident_cause) + "', '" + str(people_affected) + "', '" + str(
        people_died) + "', " + str(created_by) + ",'New') returning id"
    case_id = __db_fetch_single_value(insert_qry)

    for victim_id, victim_name, victim_sex, victim_contact, victim_address in zip(victim_id_list, victim_name_list,
                                                                                  victim_sex_list, victim_contact_list,
                                                                                  victim_address_list):
        ins_qry = "insert into asf_victim(case_id,victim_id,victim_name,sex,mobile,current_address, current_division, current_district, current_upazila, current_union, current_ward, current_postoffice)values('" + str(
            case_id) + "','" + str(victim_id) + "','" + str(victim_name) + "','" + str(victim_sex) + "','" + str(
            victim_contact) + "','" + str(victim_address) + "', '" + str(division) + "', '" + str(
            district) + "', '" + str(upazila) + "', '" + str(union) + "', '" + str(ward) + "', '" + str(
            incidence_post_office) + "')"
        __db_commit_query(ins_qry)
    return HttpResponseRedirect('/asf/case_list/')


@login_required
def case_detail(request, case_id):
    qry = "select incident_id,to_char(incident_date::DATE ,'DD/MM/YYYY') incident_date,incident_description,(select field_name from geo_data where id = division::bigint limit 1)division, (select field_name from geo_data where id = district::bigint limit 1)district, (select field_name from geo_data where id = upazila::bigint limit 1)upazila, case when union_id ='' then '' else (select field_name from geo_data where id = union_id::bigint limit 1) end union_name,status from asf_case where id =" + str(
        case_id)
    df = pandas.read_sql(qry, connection)
    if df.empty:
        return error_page(request, "No Data")

    incident_id = df.incident_id.tolist()[0] if len(df.incident_id.tolist()) else ''
    incident_date = df.incident_date.tolist()[0] if len(df.incident_date.tolist()) else ''
    incident_description = df.incident_description.tolist()[0] if len(df.incident_description.tolist()) else ''
    division = df.division.tolist()[0] if len(df.division.tolist()) else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) else ''
    union_name = df.union_name.tolist()[0] if len(df.union_name.tolist()) else ''
    status = df.status.tolist()[0] if len(df.status.tolist()) else ''

    return render(request, "asfmodule/case_detail.html", {
        'case_id': case_id,
        'incident_id': incident_id,
        'incident_date': incident_date,
        'incident_description': incident_description,
        'division': division,
        'district': district,
        'upazila': upazila,
        'union_name': union_name,
        'status': status
    })


@csrf_exempt
def update_case_status(request, case_id):
    status = request.POST.get('status')
    update_qry = "update asf_case set status = '" + str(status) + "' where id=" + str(case_id)
    __db_commit_query(update_qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> Case status has been updated successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_detail/' + str(case_id))


@csrf_exempt
def get_victim_list(request):
    case_id = request.POST.get('case_id')
    query = "select id,victim_id,victim_name,mobile,sex,status,(select status from asf_case where id = case_id::int limit 1) case_status from asf_victim where case_id::int = " + str(
        case_id)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def add_victim(request, case_id):
    qry = "select victim_id::bigint from asf_victim where case_id::int = " + str(
        case_id) + " order by victim_id::bigint desc"
    df = pandas.read_sql(qry, connection)

    victim_id = df.victim_id.tolist()[0]
    victim_id += 1

    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())

    return render(request, 'asfmodule/add_victim_form.html', {
        'victim_id': victim_id, 'divisions': divisions, 'case_id': case_id
    })


@login_required
def insert_victim(request, case_id):
    victim_id = request.POST.get('victim_id')
    victim_name = request.POST.get('victim_name')
    victim_sex = request.POST.get('victim_sex')
    birth_date = request.POST.get('birth_date')
    victim_age = request.POST.get('victim_age')
    mobile = request.POST.get('mobile')
    mobile2 = request.POST.get('mobile2')
    any_nid_brn_passport = request.POST.get('any_nid_brn_passport')
    nid_brn_passport = request.POST.get('nid_brn_passport')
    education = request.POST.get('education')
    occupation = request.POST.get('occupation')
    maritial_status = request.POST.get('maritial_status')
    father_name = request.POST.get('father_name')
    mother_name = request.POST.get('mother_name')
    spouse_name = request.POST.get('spouse_name')
    current_division = request.POST.get('current_division')
    current_district = request.POST.get('current_district')
    current_upazila = request.POST.get('current_upazila')
    current_union = request.POST.get('current_union')
    current_ward = request.POST.get('current_ward')
    current_address = request.POST.get('current_address')
    current_postoffice = request.POST.get('current_postoffice')
    present_permanent_address_same = request.POST.get('present_permanent_address_same')
    permanent_division = request.POST.get('permanent_division')
    permanent_district = request.POST.get('permanent_district')
    permanent_upazila = request.POST.get('permanent_upazila')
    permanent_union = request.POST.get('permanent_union')
    permanent_ward = request.POST.get('permanent_ward')
    permanent_address = request.POST.get('permanent_address')
    permanent_postoffice = request.POST.get('permanent_postoffice')
    injury_details = request.POST.get('injury_details')
    notified_within_24h = request.POST.get('notified_within_24h')
    verification_within_24h = request.POST.get('verification_within_24h')
    brought_asf_within_48h = request.POST.get('brought_asf_within_48h')

    if request.FILES:
        myfile = request.FILES['picture']
        url = "onadata/media/uploaded_files/"
        userName = request.user
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        picture = "onadata/media/uploaded_files/" + myfile.name
    else:
        picture = ''

    created_by = request.user.id
    insert_qry = "INSERT INTO public.asf_victim (victim_id, victim_name, sex, birth_date, victim_age, mobile, mobile2, any_nid_brn_passport, nid_brn_passport, education, occupation, maritial_status, father_name, mother_name, spouse_name, picture, current_division, current_district, current_upazila, current_union, current_ward, current_address, current_postoffice, present_permanent_address_same,permanent_division,permanent_district, permanent_upazila, permanent_union, permanent_ward, permanent_address, permanent_postoffice, injury_details, notified_within_24h, verification_within_24h, brought_asf_within_48h, created_by, case_id) VALUES('" + str(
        victim_id) + "', '" + str(victim_name) + "', '" + str(victim_sex) + "', '" + str(birth_date) + "', '" + str(
        victim_age) + "', '" + str(mobile) + "', '" + str(mobile2) + "', '" + str(any_nid_brn_passport) + "', '" + str(
        nid_brn_passport) + "', '" + str(education) + "', '" + str(occupation) + "', '" + str(
        maritial_status) + "', '" + str(father_name) + "', '" + str(mother_name) + "', '" + str(
        spouse_name) + "', '" + str(picture) + "', '" + str(current_division) + "', '" + str(
        current_district) + "', '" + str(current_upazila) + "', '" + str(current_union) + "', '" + str(
        current_ward) + "', '" + str(current_address) + "', '" + str(current_postoffice) + "', '" + str(
        present_permanent_address_same) + "', '" + str(permanent_division) + "', '" + str(
        permanent_district) + "', '" + str(permanent_upazila) + "', '" + str(permanent_union) + "', '" + str(
        permanent_ward) + "', '" + str(permanent_address) + "', '" + str(permanent_postoffice) + "', '" + str(
        injury_details) + "', '" + str(notified_within_24h) + "', '" + str(verification_within_24h) + "', '" + str(
        brought_asf_within_48h) + "' , " + str(created_by) + ", '" + str(case_id) + "')"
    __db_commit_query(insert_qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> New Victim has been added successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_detail/' + str(case_id) + '/')


@login_required
def edit_victim(request, victim_tbl_id):
    qry = "select * from asf_victim where id = " + str(victim_tbl_id)
    df = pandas.read_sql(qry, connection)
    victim_id = df.victim_id.tolist()[0] if len(df.victim_id.tolist()) and df.victim_id.tolist()[0] is not None  else ''
    victim_name = df.victim_name.tolist()[0] if len(df.victim_name.tolist()) and df.victim_name.tolist()[
                                                                                     0] is not None  else ''
    victim_sex = df.sex.tolist()[0] if len(df.sex.tolist()) and df.sex.tolist()[0] is not None  else ''
    birth_date = df.birth_date.tolist()[0] if len(df.birth_date.tolist()) and df.birth_date.tolist()[
                                                                                  0] is not None  else ''
    victim_age = df.victim_age.tolist()[0] if len(df.victim_age.tolist()) and df.victim_age.tolist()[
                                                                                  0] is not None  else ''
    mobile = df.mobile.tolist()[0] if len(df.mobile.tolist()) and df.mobile.tolist()[0] is not None  else ''
    mobile2 = df.mobile2.tolist()[0] if len(df.mobile2.tolist()) and df.mobile2.tolist()[0] is not None  else ''
    any_nid_brn_passport = df.any_nid_brn_passport.tolist()[0] if len(df.any_nid_brn_passport.tolist()) and \
                                                                  df.any_nid_brn_passport.tolist()[
                                                                      0] is not None  else ''
    nid_brn_passport = df.nid_brn_passport.tolist()[0] if len(df.nid_brn_passport.tolist()) and \
                                                          df.nid_brn_passport.tolist()[0] is not None  else ''
    education = df.education.tolist()[0] if len(df.education.tolist()) and df.education.tolist()[0] is not None  else ''
    occupation = df.occupation.tolist()[0] if len(df.occupation.tolist()) and df.occupation.tolist()[
                                                                                  0] is not None  else ''
    maritial_status = df.maritial_status.tolist()[0] if len(df.maritial_status.tolist()) and \
                                                        df.maritial_status.tolist()[0] is not None  else ''
    father_name = df.father_name.tolist()[0] if len(df.father_name.tolist()) and df.father_name.tolist()[
                                                                                     0] is not None  else ''
    mother_name = df.mother_name.tolist()[0] if len(df.mother_name.tolist()) and df.mother_name.tolist()[
                                                                                     0] is not None  else ''
    spouse_name = df.spouse_name.tolist()[0] if len(df.spouse_name.tolist()) and df.spouse_name.tolist()[
                                                                                     0] is not None  else ''
    picture = df.picture.tolist()[0] if len(df.picture.tolist()) and df.picture.tolist()[0] is not None  else ''

    current_division = df.current_division.tolist()[0] if len(df.current_division.tolist()) and \
                                                          df.current_division.tolist()[0] is not None  else '%'
    current_district = df.current_district.tolist()[0] if len(df.current_district.tolist()) and \
                                                          df.current_district.tolist()[0] is not None  else '%'
    current_upazila = df.current_upazila.tolist()[0] if len(df.current_upazila.tolist()) and \
                                                        df.current_upazila.tolist()[0] is not None  else '%'
    current_union = df.current_union.tolist()[0] if len(df.current_union.tolist()) and df.current_union.tolist()[
                                                                                           0] is not None  else '%'
    current_ward = df.current_ward.tolist()[0] if len(df.current_ward.tolist()) and df.current_ward.tolist()[
                                                                                        0] is not None  else '%'
    current_address = df.current_address.tolist()[0] if len(df.current_address.tolist()) and \
                                                        df.current_address.tolist()[0] is not None  else ''
    current_postoffice = df.current_postoffice.tolist()[0] if len(df.current_postoffice.tolist()) and \
                                                              df.current_postoffice.tolist()[0] is not None  else ''
    present_permanent_address_same = df.present_permanent_address_same.tolist()[0] if len(
        df.present_permanent_address_same.tolist()) and df.present_permanent_address_same.tolist()[
                                                            0] is not None  else ''
    permanent_division = df.permanent_division.tolist()[0] if len(df.permanent_division.tolist()) and \
                                                              df.permanent_division.tolist()[0] is not None  else '%'
    permanent_district = df.permanent_district.tolist()[0] if len(df.permanent_district.tolist()) and \
                                                              df.permanent_district.tolist()[0] is not None  else '%'
    permanent_upazila = df.permanent_upazila.tolist()[0] if len(df.permanent_upazila.tolist()) and \
                                                            df.permanent_upazila.tolist()[0] is not None  else '%'
    permanent_union = df.permanent_union.tolist()[0] if len(df.permanent_union.tolist()) and \
                                                        df.permanent_union.tolist()[0] is not None  else '%'
    permanent_ward = df.permanent_ward.tolist()[0] if len(df.permanent_ward.tolist()) and df.permanent_ward.tolist()[
                                                                                              0] is not None  else '%'
    permanent_address = df.permanent_address.tolist()[0] if len(df.permanent_address.tolist()) and \
                                                            df.permanent_address.tolist()[0] is not None  else ''
    permanent_postoffice = df.permanent_postoffice.tolist()[0] if len(df.permanent_postoffice.tolist()) and \
                                                                  df.permanent_postoffice.tolist()[
                                                                      0] is not None  else ''
    injury_details = df.injury_details.tolist()[0] if len(df.injury_details.tolist()) and df.injury_details.tolist()[
                                                                                              0] is not None  else ''
    notified_within_24h = df.notified_within_24h.tolist()[0] if len(df.notified_within_24h.tolist()) and \
                                                                df.notified_within_24h.tolist()[0] is not None  else ''
    verification_within_24h = df.verification_within_24h.tolist()[0] if len(df.verification_within_24h.tolist()) and \
                                                                        df.verification_within_24h.tolist()[
                                                                            0] is not None  else ''
    brought_asf_within_48h = df.brought_asf_within_48h.tolist()[0] if len(df.brought_asf_within_48h.tolist()) and \
                                                                      df.brought_asf_within_48h.tolist()[
                                                                          0] is not None  else ''

    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 86 and field_parent_id::text like '" + str(
        current_division) + "'"
    df = pandas.read_sql(query, connection)
    current_districts = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 86 and field_parent_id::text like '" + str(
        permanent_division) + "'"
    df = pandas.read_sql(query, connection)
    permanent_districts = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id::text like '" + str(
        current_district) + "'"
    df = pandas.read_sql(query, connection)
    current_upazilas = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 88 and field_parent_id::text like '" + str(
        permanent_district) + "'"
    df = pandas.read_sql(query, connection)
    permanent_upazilas = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 89 and field_parent_id::text like '" + str(
        current_upazila) + "'"
    df = pandas.read_sql(query, connection)
    current_unions = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 89 and field_parent_id::text like '" + str(
        permanent_upazila) + "'"
    df = pandas.read_sql(query, connection)
    permanent_unions = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 92 and field_parent_id::text like '" + str(
        current_union) + "'"
    df = pandas.read_sql(query, connection)
    current_wards = zip(df.id.tolist(), df.field_name.tolist())

    query = "select id,field_name from geo_data where field_type_id = 92 and field_parent_id::text like '" + str(
        permanent_union) + "'"
    df = pandas.read_sql(query, connection)
    permanent_wards = zip(df.id.tolist(), df.field_name.tolist())

    return render(request, 'asfmodule/edit_victim_form.html', {
        'divisions': divisions,
        'current_districts': current_districts,
        'permanent_districts': permanent_districts,
        'permanent_division': permanent_division,
        'current_upazilas': current_upazilas,
        'permanent_upazilas': permanent_upazilas,
        'current_unions': current_unions,
        'permanent_unions': permanent_unions,
        'current_wards': current_wards,
        'permanent_wards': permanent_wards,
        'victim_tbl_id': victim_tbl_id,
        'victim_id': victim_id,
        'victim_name': victim_name,
        'victim_sex': victim_sex,
        'birth_date': birth_date,
        'victim_age': victim_age,
        'mobile': mobile,
        'mobile2': mobile2,
        'any_nid_brn_passport': any_nid_brn_passport,
        'nid_brn_passport': nid_brn_passport,
        'education': education,
        'occupation': occupation,
        'maritial_status': maritial_status,
        'father_name': father_name,
        'mother_name': mother_name,
        'spouse_name': spouse_name,
        'picture': picture,
        'current_division': current_division,
        'current_district': current_district,
        'current_upazila': current_upazila,
        'current_union': current_union,
        'current_ward': current_ward,
        'current_address': current_address,
        'current_postoffice': current_postoffice,
        'present_permanent_address_same': present_permanent_address_same,
        'permanent_district': permanent_district,
        'permanent_upazila': permanent_upazila,
        'permanent_union': permanent_union,
        'permanent_ward': permanent_ward,
        'permanent_address': permanent_address,
        'permanent_postoffice': permanent_postoffice,
        'injury_details': injury_details,
        'notified_within_24h': notified_within_24h,
        'verification_within_24h': verification_within_24h,
        'brought_asf_within_48h': brought_asf_within_48h
    })


@login_required
def update_victim(request, victim_tbl_id):
    case_id = __db_fetch_single_value("select case_id from asf_victim where id = " + str(victim_tbl_id))
    victim_id = request.POST.get('victim_id')
    victim_name = request.POST.get('victim_name')
    victim_sex = request.POST.get('victim_sex')
    birth_date = request.POST.get('birth_date')
    victim_age = request.POST.get('victim_age')
    mobile = request.POST.get('mobile')
    mobile2 = request.POST.get('mobile2')
    any_nid_brn_passport = request.POST.get('any_nid_brn_passport')
    nid_brn_passport = request.POST.get('nid_brn_passport')
    education = request.POST.get('education')
    occupation = request.POST.get('occupation')
    maritial_status = request.POST.get('maritial_status')
    father_name = request.POST.get('father_name')
    mother_name = request.POST.get('mother_name')
    spouse_name = request.POST.get('spouse_name')
    current_division = request.POST.get('current_division')
    current_district = request.POST.get('current_district')
    current_upazila = request.POST.get('current_upazila')
    current_union = request.POST.get('current_union')
    current_ward = request.POST.get('current_ward')
    current_address = request.POST.get('current_address')
    current_postoffice = request.POST.get('current_postoffice')
    present_permanent_address_same = request.POST.get('present_permanent_address_same')
    print(present_permanent_address_same)
    permanent_division = request.POST.get('permanent_division')
    permanent_district = request.POST.get('permanent_district')
    permanent_upazila = request.POST.get('permanent_upazila')
    permanent_union = request.POST.get('permanent_union')
    permanent_ward = request.POST.get('permanent_ward')
    permanent_address = request.POST.get('permanent_address')
    permanent_postoffice = request.POST.get('permanent_postoffice')
    injury_details = request.POST.get('injury_details')
    notified_within_24h = request.POST.get('notified_within_24h')
    verification_within_24h = request.POST.get('verification_within_24h')
    brought_asf_within_48h = request.POST.get('brought_asf_within_48h')

    if request.FILES:
        myfile = request.FILES['picture']
        url = "onadata/media/uploaded_files/"
        userName = request.user
        fs = FileSystemStorage(location=url)
        myfile.name = str(datetime.datetime.now()) + "_" + str(userName) + "_" + str(myfile.name)
        filename = fs.save(myfile.name, myfile)
        picture = "onadata/media/uploaded_files/" + myfile.name
    else:
        picture = ''

    created_by = request.user.id

    updt_qry = "UPDATE public.asf_victim SET victim_id='" + str(victim_id) + "', victim_name='" + str(
        victim_name) + "', sex='" + str(victim_sex) + "', birth_date='" + str(birth_date) + "', victim_age='" + str(
        victim_age) + "', mobile='" + str(mobile) + "', mobile2='" + str(mobile2) + "', any_nid_brn_passport='" + str(
        any_nid_brn_passport) + "', nid_brn_passport='" + str(nid_brn_passport) + "', education='" + str(
        education) + "', occupation='" + str(occupation) + "', maritial_status='" + str(
        maritial_status) + "', father_name='" + str(father_name) + "', mother_name='" + str(
        mother_name) + "', spouse_name='" + str(spouse_name) + "', picture='" + str(
        picture) + "', current_division='" + str(current_division) + "', current_district='" + str(
        current_district) + "', current_upazila='" + str(current_upazila) + "', current_union='" + str(
        current_union) + "', current_ward='" + str(current_ward) + "', current_address='" + str(
        current_address) + "', current_postoffice='" + str(
        current_postoffice) + "', present_permanent_address_same='" + str(
        present_permanent_address_same) + "', permanent_division='" + str(
        permanent_division) + "', permanent_district='" + str(permanent_district) + "', permanent_upazila='" + str(
        permanent_upazila) + "', permanent_union='" + str(permanent_union) + "', permanent_ward='" + str(
        permanent_ward) + "', permanent_address='" + str(permanent_address) + "', permanent_postoffice='" + str(
        permanent_postoffice) + "', injury_details='" + str(injury_details) + "', notified_within_24h='" + str(
        notified_within_24h) + "', verification_within_24h='" + str(
        verification_within_24h) + "', brought_asf_within_48h='" + str(
        brought_asf_within_48h) + "', created_by = '" + str(created_by) + "' where id = " + str(victim_tbl_id)
    __db_commit_query(updt_qry)
    messages.success(request, '<i class="fa fa-check-circle"></i> Victim Info has been updated successfully!',
                     extra_tags='alert-success crop-both-side')
    return HttpResponseRedirect('/asf/case_detail/' + str(case_id) + '/')


def send_push_notification(user_id, incident_id):
    print(user_id, incident_id)
    query = "select firebase_token from user_device_map where user_id = '" + str(user_id) + "'"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    if df.empty:
        return HttpResponse(json.dumps('Token Not Found'), status=404)
    else:
        firebase_token = df.firebase_token.tolist()[0]
        registration_id = []
        registration_id.append(firebase_token)
        full_name = __db_fetch_single_value(
            "select first_name || ' ' || last_name from auth_user where id = " + str(user_id))
        message_title = 'IOM-BD'
        message_body = 'Hi, ' + full_name + '.<br>You are requested to complete Case ID ' + incident_id + ' Beneficiary profiling'
        data_message = {
            "title": message_title,
            "message": message_body
        }

        result = push_service.notify_multiple_devices(registration_ids=registration_id, data_message=data_message)

        if result['success']:
            return HttpResponse(json.dumps('Notification Sent Successfully '), status=200)
        else:
            return HttpResponse(json.dumps('Notification Sent Failed '), status=22)


@login_required
def victim_status(request, victim_tbl_id):
    if request.POST:
        case_id = __db_fetch_single_value("select case_id from asf_victim where id = " + str(victim_tbl_id))
        assaign_to = request.POST.get('assaign_to')
        incident_id = __db_fetch_single_value("select incident_id from asf_case where id = " + str(case_id))
        updt_qry = "UPDATE public.asf_case SET assaign_to='" + str(assaign_to) + "',status='2' where id = " + str(
            case_id)
        __db_commit_query(updt_qry)
        send_push_notification(assaign_to, incident_id)
        messages.success(request, '<i class="fa fa-check-circle"></i> User has been assaigned successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/asf/case_list/')
    user_id = request.user.id
    role = __db_fetch_single_value(
        "select (SELECT role FROM public.usermodule_organizationrole WHERE id = role_id limit 1)role_name  from usermodule_userrolemap where user_id = (select id from usermodule_usermoduleprofile where user_id= " + str(
            user_id) + ")")
    qry = "with t as( select(select user_id from usermodule_usermoduleprofile where id = usermodule_userrolemap.user_id) ,(select (select first_name || ' ' || last_name from auth_user where id = user_id limit 1) username from usermodule_usermoduleprofile where id = usermodule_userrolemap.user_id) from usermodule_userrolemap where role_id = (select id from usermodule_organizationrole where role = 'Field Officer'))select user_id,username from t "

    if role == 'RSC Manager':
        qry += "where user_id =any (select user_id from usermodule_usermoduleprofile where rsc_name_id = (select rsc_name_id from usermodule_usermoduleprofile where user_id= " + str(
            user_id) + "))"

    df = pandas.read_sql(qry, connection)
    users = zip(df.user_id.tolist(), df.username.tolist())
    return render(request, 'asfmodule/victim_status_form.html', {'victim_tbl_id': victim_tbl_id, 'users': users})


@login_required
def victim_status_from_web(request, victim_tbl_id):
    if request.POST:
        status = request.POST.get('status')
        case_id = __db_fetch_single_value("select case_id from asf_victim where id = " + str(victim_tbl_id))
        updt_qry = "UPDATE public.asf_case SET status='" + str(status) + "' where id = " + str(case_id)
        __db_commit_query(updt_qry)
        messages.success(request, '<i class="fa fa-check-circle"></i> Status has been changed successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/asf/case_list/')

    user_id = request.user.id
    qry = "select id,status from iom_status where id > 2 "
    df = pandas.read_sql(qry, connection)
    status_list = zip(df.id.tolist(), df.status.tolist())
    return render(request, 'asfmodule/victim_status_from_web.html',
                  {'victim_tbl_id': victim_tbl_id, 'status_list': status_list})


@login_required
def refer_victim(request, victim_id, victim_tbl_id):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='referral'")
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    return render(request, 'asfmodule/victim_refer_form.html',
                  {'victim_id': victim_id, 'victim_tbl_id': victim_tbl_id, 'username': username,
                   'server_address': server_address, 'form_id': form_id, 'form_builder_server': form_builder_server})


@login_required
def victim_profile(request, victim_tbl_id):
    qry = "select asf_case.id as returnee_case_id,asf_case.incident_id,asf_case.division,asf_case.district,asf_case.upazila,asf_case.union_id,asf_case.ward,asf_case.created_by,asf_case.created_at,asf_case.post_office,asf_case.village,asf_case.date_return,asf_case.return_from,asf_case.status,asf_case.assaign_to,asf_case.post_arrival_support_service,asf_case.post_arrival_support_meet_greet,asf_case.post_arrival_support_info_provision,asf_case.post_arrival_support_pocket_money,asf_case.post_arrival_support_shelter_accommodation,asf_case.post_arrival_support_onward_trasportation,asf_case.post_arrival_support_health_assistance,asf_case.post_arrival_support_food_nutrition,asf_case.post_arrival_support_other_assistance,asf_case.post_arrival_support_other_assistance_name,asf_case.deleted_at,asf_victim.id,asf_victim.victim_id,asf_victim.victim_name,asf_victim.sex,asf_victim.birth_date,asf_victim.victim_age,asf_victim.education,asf_victim.maritial_status,asf_victim.father_name,asf_victim.mother_name,asf_victim.created_by,asf_victim.case_id,asf_victim.created_at,asf_victim.beneficiary_reference_no,asf_victim.birth_country,asf_victim.nationality,asf_victim.religion,asf_victim.contact_self,asf_victim.contact_emergency,asf_victim.occupation_in_host_country,asf_victim.occupation_in_host_country_other,asf_victim.staying_duration_year,asf_victim.staying_duration_month,asf_victim.returnee_documents,asf_victim.passport,asf_victim.travel_pass,asf_victim.smart_card,asf_victim.nid,asf_victim.birth_registration,asf_victim.travel_document,asf_victim.accompanying_child,asf_victim.iom_reference,asf_victim.post_arrival_support_received,asf_victim.meet_greet,asf_victim.info_provision,asf_victim.pocket_money,asf_victim.shelter_accommodation,asf_victim.onward_trasportation,asf_victim.health_assistance,asf_victim.food_nutrition,asf_victim.other_assistance,asf_victim.other_assistance_name,asf_victim.retunrnee_identified_by,asf_victim.religion_other,asf_victim.permanent_post_office,asf_victim.permanent_village,asf_victim.beneficiary_picture,asf_victim.gps,asf_victim.updated_by,asf_victim.temp_victim_id,asf_victim.updated_at,asf_victim.id_status,asf_victim.direct_inkind_support_id,asf_victim.inkind_support_received,asf_victim.services_reintegration_plan_id,asf_victim.profile_update_date,asf_victim.social_reintegration_id,asf_victim.social_reintegration_support_received,asf_victim.referral_id,asf_victim.referral_services_for,asf_victim.referral_type,asf_victim.referral_organization_type,asf_victim.psychosocial_problem_identified,asf_victim.psychosocial_followup_id,asf_victim.psychological_counseling_type,asf_victim.psychosocial_assessment_id,asf_victim.counselor_psychosocial_id,asf_victim.referral_followup_id,asf_victim.referral_followup_status,asf_victim.deleted_at,asf_victim.sex_other,asf_victim.sex,asf_victim.birth_date,asf_victim.permanent_division,asf_victim.permanent_district,asf_victim.permanent_upazila,asf_victim.permanent_union,asf_victim.permanent_ward,(select label_text return_from from vw_country where value_text = return_from limit 1),case when sex = '1' then 'Male' when sex = '2' then 'Female' else 'Other' end sex,birth_date::date,date_return::date,(select field_name from geo_data where geocode = division limit 1) division,(select field_name from geo_data where geocode = district limit 1) district,(select field_name from geo_data where geocode = upazila limit 1) upazila,(select field_name from geo_data where geocode = union_id limit 1) union_id, ward ,(select field_name from geo_data where geocode = asf_victim.permanent_division limit 1) permanent_division,(select field_name from geo_data where geocode = asf_victim.permanent_district limit 1) permanent_district,(select field_name from geo_data where geocode = asf_victim.permanent_upazila limit 1) permanent_upazila,(select field_name from geo_data where geocode = asf_victim.permanent_union limit 1) permanent_union, permanent_ward from asf_case,asf_victim where asf_case.id = case_id::int and asf_victim.id =" + str(
        victim_tbl_id)
    df = pandas.read_sql(qry, connection)
    returnee_case_id = df.loc[0].returnee_case_id
    victim_id = df.victim_id.tolist()[0] if len(df.victim_id.tolist()) and df.victim_id.tolist()[0] is not None  else ''
    iom_reference = df.iom_reference.tolist()[0] if len(df.iom_reference.tolist()) and df.iom_reference.tolist()[
                                                                                           0] is not None  else ''
    case_id = df.incident_id.tolist()[0] if len(df.case_id.tolist()) and df.case_id.tolist()[0] is not None  else ''
    return_from = df.return_from.values[0][1] if len(df.return_from.values) and df.return_from.values[0][
                                                                                    1] is not None  else ''
    birth_date = df.birth_date.values[0][1] if len(df.birth_date.values) and df.birth_date.values[0][
                                                                                 1] is not None  else ''
    victim_age = df.victim_age.tolist()[0] if len(df.victim_age.tolist()) and df.victim_age.tolist()[0] is not None and \
                                              df.victim_age.tolist()[0] != 'NaN' else ''
    date_return = df.date_return.values[0][1] if len(df.date_return.values) and df.date_return.values[0][
                                                                                    1] is not None  else ''
    victim_name = df.victim_name.tolist()[0] if len(df.victim_name.tolist()) and df.victim_name.tolist()[
                                                                                     0] is not None  else ''
    victim_sex = df.sex.values[0][1] if len(df.sex.values) and df.sex.values[0][1] is not None  else ''
    status = df.status.tolist()[0] if len(df.status.tolist()) and df.status.tolist()[0] is not None else ''
    education = df.education.tolist()[0] if len(df.education.tolist()) and df.education.tolist()[0] is not None  else ''
    beneficiary_reference_no = df.beneficiary_reference_no.tolist()[0] if len(df.beneficiary_reference_no.tolist()) and \
                                                                          df.beneficiary_reference_no.tolist()[
                                                                              0] is not None else ''
    maritial_status = df.maritial_status.tolist()[0] if len(df.maritial_status.tolist()) and \
                                                        df.maritial_status.tolist()[0] is not None  else ''
    father_name = df.father_name.tolist()[0] if len(df.father_name.tolist()) and df.father_name.tolist()[
                                                                                     0] is not None  else ''
    mother_name = df.mother_name.tolist()[0] if len(df.mother_name.tolist()) and df.mother_name.tolist()[
                                                                                     0] is not None  else ''
    birth_country = df.birth_country.tolist()[0] if len(df.birth_country.tolist()) and df.birth_country.tolist()[
                                                                                           0] is not None  else ''
    nationality = df.nationality.tolist()[0] if len(df.nationality.tolist()) and df.nationality.tolist()[
                                                                                     0] is not None  else ''

    current_division = df.division.values[0][1] if len(df.division.values) and df.division.values[0][
                                                                                   1] is not None  else ''
    current_district = df.district.values[0][1] if len(df.district.values) and df.district.values[0][
                                                                                   1] is not None  else ''
    current_upazila = df.upazila.values[0][1] if len(df.upazila.values) and df.upazila.values[0][1] is not None  else ''
    current_union = df.union_id.values[0][1] if len(df.union_id.values) and df.union_id.values[0][
                                                                                1] is not None  else ''
    current_ward = df.ward.values[0][1] if len(df.ward.values) and df.ward.values[0][1] is not None  else ''
    current_village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None  else ''
    current_postoffice = df.post_office.tolist()[0] if len(df.post_office.tolist()) and df.post_office.tolist()[
                                                                                            0] is not None  else ''

    permanent_division = df.permanent_division.values[0][1] if len(df.permanent_division.values) and \
                                                               df.permanent_division.values[0][1] is not None  else ''
    permanent_district = df.permanent_district.values[0][1] if len(df.permanent_district.values) and \
                                                               df.permanent_district.values[0][1] is not None  else ''
    permanent_upazila = df.permanent_upazila.values[0][1] if len(df.permanent_upazila.values) and \
                                                             df.permanent_upazila.values[0][1] is not None  else ''
    permanent_union = df.permanent_union.values[0][1] if len(df.permanent_union.values) and \
                                                         df.permanent_union.values[0][1] is not None  else ''
    permanent_ward = df.permanent_ward.values[0][1] if len(df.permanent_ward.values) and df.permanent_ward.values[0][
                                                                                             1] is not None  else ''
    permanent_village = df.permanent_village.tolist()[0] if len(df.permanent_village.tolist()) and \
                                                            df.permanent_village.tolist()[0] is not None  else ''
    permanent_post_office = df.permanent_post_office.tolist()[0] if len(df.permanent_post_office.tolist()) and \
                                                                    df.permanent_post_office.tolist()[
                                                                        0] is not None  else ''
    print(permanent_district, df.permanent_district.values[0][1])
    contact_self = df.contact_self.tolist()[0] if len(df.contact_self.tolist()) and df.contact_self.tolist()[
                                                                                        0] is not None  else ''
    contact_emergency = df.contact_emergency.tolist()[0] if len(df.contact_emergency.tolist()) and \
                                                            df.contact_self.tolist()[0] is not None  else ''
    occupation_in_host_country = df.occupation_in_host_country.tolist()[0] if len(
        df.occupation_in_host_country.tolist()) and df.occupation_in_host_country.tolist()[0] is not None  else ''
    beneficiary_picture = '/media/iom_admin/attachments/' + df.beneficiary_picture.tolist()[0] if len(
        df.beneficiary_picture.tolist()) and df.beneficiary_picture.tolist()[
                                                 0] is not None  else '/static/images/profile.jpg'

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"><div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><input type="checkbox" id="'||category_id||'"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and case when( select Count(*) FROM logger_instance WHERE ( json ->> 'victim_tbl_id') :: INT = """ + str(
        victim_tbl_id) + """ AND deleted_at IS NULL AND xform_id = ANY (select id from logger_xform where id_string = any('{beneficiary_profiling,socio_economic_support,support_history}')))>= 3 then fc.category_id = ANY ( '{1,2,10,20,30,40,50,60,70,80}' ) else fc.category_id = ANY ( '{1}' ) end AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    print(form_builder_server)

    # For loading default quarter,year
    qr = '%'
    yr = '%'
    q = "select BTRIM(to_char((date(quarter||'-'||yr)),'Month'),' ') mon,yr from public.vw_reintegration_sustainability where beneficiary_id='" + victim_id + "' order by id desc limit 1"

    dta = __db_fetch_values_dict(q)
    for tmp in dta:
        qr = tmp['mon']
        yr = tmp['yr']
    qery = "select id from logger_instance where json->>'victim_tbl_id' = '" + str(victim_tbl_id) + "'"
    df = pandas.DataFrame()
    df = pandas.read_sql(qery, connection)
    instance_id_list = df.id.tolist()
    data = {
        'returnee_case_id': returnee_case_id,
        'instance_id_list': instance_id_list,
        'main_str': main_str,
        'username': username,
        'beneficiary_picture': beneficiary_picture,
        'iom_reference': iom_reference,
        'victim_tbl_id': victim_tbl_id,
        'victim_id': victim_id,
        'victim_name': victim_name,
        'victim_sex': victim_sex,
        'birth_date': birth_date,
        'victim_age': victim_age,
        'birth_country': birth_country,
        'case_id': case_id,
        'return_from': return_from,
        'date_return': date_return,
        'education': education,
        'beneficiary_reference_no': beneficiary_reference_no,
        'maritial_status': maritial_status,
        'father_name': father_name,
        'mother_name': mother_name,
        'nationality': nationality,
        'current_division': current_division,
        'current_district': current_district,
        'current_upazila': current_upazila,
        'current_union': current_union,
        'current_ward': current_ward,
        'current_village': current_village,
        'current_postoffice': current_postoffice,
        'permanent_division': permanent_division,
        'permanent_district': permanent_district,
        'permanent_upazila': permanent_upazila,
        'permanent_union': permanent_union,
        'permanent_ward': permanent_ward,
        'permanent_village': permanent_village,
        'permanent_post_office': permanent_post_office,
        'contact_self': contact_self,
        'contact_emergency': contact_emergency,
        'occupation_in_host_country': occupation_in_host_country,
        'permanent_address': '',
        'permanent_postoffice': '',
        'injury_details': '',
        'notified_within_24h': '',
        'verification_within_24h': '',
        'server_address': server_address, 'form_builder_server': form_builder_server, 'qr': qr, 'yr': yr
    }
    return render(request, "asfmodule/victim_profile.html", data)


@csrf_exempt
def generate_pdf(request):
    checked_id_list = request.POST.getlist('checked_id')
    checked_id_list = str([int(i) for i in checked_id_list]).replace('[', '{').replace(']', '}')
    report_check = request.POST.get('checked_report_id', 'no')
    victim_tbl_id = request.POST.get('victim_tbl_id')
    qry = "select *,(select label_text return_from from vw_country where value_text = return_from limit 1),case when sex = '1' then 'Male' when sex = '2' then 'Female' else 'Other' end sex,birth_date::date,date_return::date,(select field_name from geo_data where geocode = division limit 1) division,(select field_name from geo_data where geocode = district limit 1) district,(select field_name from geo_data where geocode = upazila limit 1) upazila,(select field_name from geo_data where geocode = union_id limit 1) union_id, ward ,(select field_name from geo_data where geocode = asf_victim.permanent_division limit 1) permanent_division,(select field_name from geo_data where geocode = asf_victim.permanent_district limit 1) permanent_district,(select field_name from geo_data where geocode = asf_victim.permanent_upazila limit 1) permanent_upazila,(select field_name from geo_data where geocode = asf_victim.permanent_union limit 1) permanent_union, permanent_ward from asf_case,asf_victim where asf_case.id = case_id::int and asf_victim.id =" + str(
        victim_tbl_id)
    df = pandas.read_sql(qry, connection)
    victim_id = df.victim_id.tolist()[0] if len(df.victim_id.tolist()) and df.victim_id.tolist()[0] is not None  else ''
    iom_reference = df.iom_reference.tolist()[0] if len(df.iom_reference.tolist()) and df.iom_reference.tolist()[
                                                                                           0] is not None  else ''
    case_id = df.incident_id.tolist()[0] if len(df.case_id.tolist()) and df.case_id.tolist()[0] is not None  else ''
    return_from = df.return_from.values[0][1] if len(df.return_from.values) and df.return_from.values[0][
                                                                                    1] is not None  else ''
    birth_date = df.birth_date.values[0][1] if len(df.birth_date.values) and df.birth_date.values[0][
                                                                                 1] is not None  else ''
    victim_age = df.victim_age.tolist()[0] if len(df.victim_age.tolist()) and df.victim_age.tolist()[0] is not None and \
                                              df.victim_age.tolist()[0] != 'NaN' else ''
    date_return = df.date_return.values[0][1] if len(df.date_return.values) and df.date_return.values[0][
                                                                                    1] is not None  else ''
    victim_name = df.victim_name.tolist()[0] if len(df.victim_name.tolist()) and df.victim_name.tolist()[
                                                                                     0] is not None  else ''
    victim_sex = df.sex.values[0][1] if len(df.sex.values) and df.sex.values[0][1] is not None  else ''
    status = df.status.tolist()[0] if len(df.status.tolist()) and df.status.tolist()[0] is not None else ''
    education = df.education.tolist()[0] if len(df.education.tolist()) and df.education.tolist()[0] is not None  else ''
    beneficiary_reference_no = df.beneficiary_reference_no.tolist()[0] if len(df.beneficiary_reference_no.tolist()) and \
                                                                          df.beneficiary_reference_no.tolist()[
                                                                              0] is not None else ''
    maritial_status = df.maritial_status.tolist()[0] if len(df.maritial_status.tolist()) and \
                                                        df.maritial_status.tolist()[0] is not None  else ''
    father_name = df.father_name.tolist()[0] if len(df.father_name.tolist()) and df.father_name.tolist()[
                                                                                     0] is not None  else ''
    mother_name = df.mother_name.tolist()[0] if len(df.mother_name.tolist()) and df.mother_name.tolist()[
                                                                                     0] is not None  else ''
    birth_country = df.birth_country.tolist()[0] if len(df.birth_country.tolist()) and df.birth_country.tolist()[
                                                                                           0] is not None  else ''
    nationality = df.nationality.tolist()[0] if len(df.nationality.tolist()) and df.nationality.tolist()[
                                                                                     0] is not None  else ''

    current_division = df.division.values[0][1] if len(df.division.values) and df.division.values[0][
                                                                                   1] is not None  else ''
    current_district = df.district.values[0][1] if len(df.district.values) and df.district.values[0][
                                                                                   1] is not None  else ''
    current_upazila = df.upazila.values[0][1] if len(df.upazila.values) and df.upazila.values[0][1] is not None  else ''
    current_union = df.union_id.values[0][1] if len(df.union_id.values) and df.union_id.values[0][
                                                                                1] is not None  else ''
    current_ward = df.ward.values[0][1] if len(df.ward.values) and df.ward.values[0][1] is not None  else ''
    current_village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None  else ''
    current_postoffice = df.post_office.tolist()[0] if len(df.post_office.tolist()) and df.post_office.tolist()[
                                                                                            0] is not None  else ''

    permanent_division = df.permanent_division.values[0][1] if len(df.permanent_division.values) and \
                                                               df.permanent_division.values[0][1] is not None  else ''
    permanent_district = df.permanent_district.values[0][1] if len(df.permanent_district.values) and \
                                                               df.permanent_district.values[0][1] is not None  else ''
    permanent_upazila = df.permanent_upazila.values[0][1] if len(df.permanent_upazila.values) and \
                                                             df.permanent_upazila.values[0][1] is not None  else ''
    permanent_union = df.permanent_union.values[0][1] if len(df.permanent_union.values) and \
                                                         df.permanent_union.values[0][1] is not None  else ''
    permanent_ward = df.permanent_ward.values[0][1] if len(df.permanent_ward.values) and df.permanent_ward.values[0][
                                                                                             1] is not None  else ''
    permanent_village = df.permanent_village.tolist()[0] if len(df.permanent_village.tolist()) and \
                                                            df.permanent_village.tolist()[0] is not None  else ''
    permanent_post_office = df.permanent_post_office.tolist()[0] if len(df.permanent_post_office.tolist()) and \
                                                                    df.permanent_post_office.tolist()[
                                                                        0] is not None  else ''
    # print(permanent_district, df.permanent_district.values[0][1])
    contact_self = df.contact_self.tolist()[0] if len(df.contact_self.tolist()) and df.contact_self.tolist()[
                                                                                        0] is not None  else ''
    contact_emergency = df.contact_emergency.tolist()[0] if len(df.contact_emergency.tolist()) and \
                                                            df.contact_self.tolist()[0] is not None  else ''
    occupation_in_host_country = ''
    beneficiary_picture = '/media/iom_admin/attachments/' + df.beneficiary_picture.tolist()[0] if len(
        df.beneficiary_picture.tolist()) and df.beneficiary_picture.tolist()[
                                                 0] is not None  else '/static/images/profile.jpg'

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('""" + str(
        checked_id_list) + """') AND user_id = """ + str(user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    print(form_builder_server)

    # For loading default quarter,year
    qr = '%'
    yr = '%'
    q = "select BTRIM(to_char((date(quarter||'-'||yr)),'Month'),' ') mon,yr from public.vw_reintegration_sustainability where beneficiary_id='" + victim_id + "' order by id desc limit 1"

    dta = __db_fetch_values_dict(q)
    for tmp in dta:
        qr = tmp['mon']
        yr = tmp['yr']

    qery = "select id from logger_instance where json->>'victim_tbl_id' = '" + str(victim_tbl_id) + "'"
    df = pandas.DataFrame()
    df = pandas.read_sql(qery, connection)
    instance_id_list = df.id.tolist()
    data = {
        'report_check': report_check,
        'main_str': main_str,
        'instance_id_list': instance_id_list,
        'username': username,
        'beneficiary_picture': beneficiary_picture,
        'iom_reference': iom_reference,
        'victim_tbl_id': victim_tbl_id,
        'victim_id': victim_id,
        'victim_name': victim_name,
        'victim_sex': victim_sex,
        'birth_date': birth_date,
        'victim_age': victim_age,
        'birth_country': birth_country,
        'case_id': case_id,
        'return_from': return_from,
        'date_return': date_return,
        'education': education,
        'beneficiary_reference_no': beneficiary_reference_no,
        'maritial_status': maritial_status,
        'father_name': father_name,
        'mother_name': mother_name,
        'nationality': nationality,
        'current_division': current_division,
        'current_district': current_district,
        'current_upazila': current_upazila,
        'current_union': current_union,
        'current_ward': current_ward,
        'current_village': current_village,
        'current_postoffice': current_postoffice,
        'permanent_division': permanent_division,
        'permanent_district': permanent_district,
        'permanent_upazila': permanent_upazila,
        'permanent_union': permanent_union,
        'permanent_ward': permanent_ward,
        'permanent_village': permanent_village,
        'permanent_post_office': permanent_post_office,
        'contact_self': contact_self,
        'contact_emergency': contact_emergency,
        'occupation_in_host_country': occupation_in_host_country,
        'permanent_address': '',
        'permanent_postoffice': '',
        'injury_details': '',
        'notified_within_24h': '',
        'verification_within_24h': '',
        'server_address': server_address, 'form_builder_server': form_builder_server, 'qr': qr, 'yr': yr,
        'current_date': datetime.datetime.now()
    }
    return render(request, "asfmodule/profile_export.html", data)
    # pdf = render_to_pdf('asfmodule/export.html', data)
    # response = HttpResponse(pdf, mimetype='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename=export.pdf'
    # return response


@login_required
def victim_list(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/victim_list.html', {'divisions': divisions})


@csrf_exempt
def get_victims_list(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    status = request.POST.get('status')
    query = "select id,victim_id,(select incident_id from asf_case where id = case_id::int limit 1),victim_name ,(select incident_date from asf_case where id = case_id::int limit 1) ,mobile,sex,status,(select field_name from geo_data where id = current_division::int limit 1)division,(select field_name from geo_data where id = current_district::int limit 1) district ,(select field_name from geo_data where id = current_upazila::int limit 1) upazila ,(select field_name from geo_data where id = current_union::int limit 1) union_name ,current_address address from asf_victim where case_id::int = any(select id from asf_case where status = 'Valid') and  current_division like '" + str(
        division) + "' and current_district like '" + str(district) + "' and current_upazila like '" + str(
        upazila) + "' and status like '" + str(status) + "'"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def services_to_other_institutes_list(request):
    return render(request, 'asfmodule/services_to_other_institutes_list.html')


@csrf_exempt
def get_services_to_other_institutes_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "WITH t AS(SELECT json ->> 'date' s_date, json ->> 'organization' organization, json ->> 'hospital' hospital, json ->> 'service' service, json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_female' child_female, json ->> 'child_male' child_male, json ->> 'trangender' trangender, json ->> 'session_adult_female' seasson_adult_female, json ->> 'session_adult_male' seasson_adult_male, json ->> 'session_child_female' seasson_child_female, json ->> 'session_child_male' seasson_child_male, json ->> 'session_trangender' seasson_trangender, json ->> 'procedure' s_procedure FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute')) SELECT to_char(s_date::date,'DD/MM/YYYY') s_date, case when organization='1' then 'Govt Hospital' when organization='2' then 'E-Clinic' when organization='3' then 'Outreach' when organization='4' then 'Community Clinic' end organization, case when hospital='1' then 'SHNIBPS' when hospital='2' then 'DMCH' when hospital='3' then 'ShSMCH' when hospital='4' then 'SSMC' when hospital='5' then 'MMCH' when hospital='6' then 'KMCH' when hospital='7' then 'CMCH' when hospital='8' then 'CuMCH' when hospital='9' then 'VSC' else '' end hospital, case when service='1' then 'Physiotherapy' when service='2' then 'Psychotherapy' end service, adult_female, adult_male, child_female, child_male, trangender, seasson_adult_female, seasson_adult_male, seasson_child_female, seasson_child_male, seasson_trangender, coalesce(s_procedure,'') s_procedure FROM t  where s_date:: DATE between to_date('" + str(
        from_date) + "','DD/MM/YYYY') and to_date('" + str(to_date) + "','DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


def services_to_other_institutes_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='services_other_institute'")
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    print(form_builder_server)
    return render(request, 'asfmodule/services_to_other_institutes_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server})


# Capacity Building
@login_required
def capacity_building_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='capacity_building'")
    return render(request, 'asfmodule/capacity_building_list.html', {'form_id': form_id})


@csrf_exempt
def get_capacity_building_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='capacity_building') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='capacity_building') limit 1),0) can_delete,instance_id,case when training_name::int = 1 then 'Counsellor Training' when training_name::int = 2 then 'Forum Training' when training_name::int = 99 then training_name_other end training_name, to_char(training_start_time::date,'DD/MM/YYYY') date_created,(select field_name from geo_data where geocode = division) division , (select field_name from geo_data where geocode = district) district , (select field_name from geo_data where geocode = upazila) upazila from vw_capacity_building WHERE training_start_time:: date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(
            to_date) + "','DD/MM/YYYY') AND upazila IN( ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid limit 1) FROM usermodule_catchment_area WHERE user_id = " + str(
            user_id) + ") UNION ( SELECT geocode FROM geo_data WHERE field_parent_id = ANY ( SELECT geoid FROM usermodule_catchment_area WHERE user_id = " + str(
            user_id) + ") AND field_type_id = 88)) order by instance_id desc"
    except Exception:
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='capacity_building') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='capacity_building') limit 1),0) can_delete,instance_id,case when training_name::int = 1 then 'Counsellor Training' when training_name::int = 2 then 'Forum Training' when training_name::int = 99 then training_name_other end training_name, to_char(training_start_time::date,'DD/MM/YYYY') date_created,(select field_name from geo_data where geocode = division) division , (select field_name from geo_data where geocode = district) district , (select field_name from geo_data where geocode = upazila) upazila from vw_capacity_building WHERE training_start_time:: date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(to_date) + "','DD/MM/YYYY') order by instance_id desc"
    print(query)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


def capacity_building_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='capacity_building'")
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    print(form_builder_server)
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1

    return render(request, 'asfmodule/capacity_building_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'instance_id': instance_id})


# Case Study
@login_required
def case_study_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='case_study'")
    username = request.user
    return render(request, 'asfmodule/case_study_list.html', {'form_id': form_id, 'username': username})


@csrf_exempt
def get_case_study_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    user_id = request.user.id
    role = __db_fetch_single_value(
        "select (SELECT role FROM public.usermodule_organizationrole WHERE id = role_id limit 1)role_name  from usermodule_userrolemap where user_id = (select id from usermodule_usermoduleprofile where user_id= " + str(
            user_id) + ")")
    if role == 'Field Officer':
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='case_study') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='case_study') limit 1),0) can_delete,organization_name,individual_name,data_source,introduction,to_char(date_submission::date,'DD/MM/YYYY') date_submission, accomplishment,challenge,challenge_overcome,conclusion,promising_practice,instance_id,lesson_learned  from vw_case_study WHERE date_submission::date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(to_date) + "','DD/MM/YYYY') and user_id=" + str(
            user_id) + " order by instance_id desc"
    elif role == 'Admin':
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='case_study') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='case_study') limit 1),0) can_delete,organization_name,individual_name,data_source,introduction,to_char(date_submission::date,'DD/MM/YYYY') date_submission, accomplishment,challenge,challenge_overcome,conclusion,promising_practice,instance_id,lesson_learned  from vw_case_study WHERE date_submission::date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(to_date) + "','DD/MM/YYYY') order by instance_id desc"
    else:
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='case_study') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='case_study') limit 1),0) can_delete,organization_name,individual_name,data_source,introduction,to_char(date_submission::date,'DD/MM/YYYY') date_submission, accomplishment,challenge,challenge_overcome,conclusion,promising_practice,instance_id,lesson_learned  from vw_case_study WHERE date_submission::date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(
            to_date) + "','DD/MM/YYYY') and user_id=any(select user_id from usermodule_usermoduleprofile where rsc_name_id = any(select rsc_name_id from usermodule_usermoduleprofile where user_id =" + str(
            user_id) + ")) order by instance_id desc"
    print(query)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def case_study_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='case_study'")
    redirected_url = '/asf/case_study_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


# MSC story
@login_required
def msc_story_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='msc_story'")
    username = request.user
    return render(request, 'asfmodule/msc_story_list.html', {'form_id': form_id, 'username': username})


@csrf_exempt
def get_msc_story_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    user_id = request.user.id
    role = __db_fetch_single_value(
        "select (SELECT role FROM public.usermodule_organizationrole WHERE id = role_id limit 1)role_name  from usermodule_userrolemap where user_id = (select id from usermodule_usermoduleprofile where user_id= " + str(
            user_id) + ")")
    if role == 'Field Officer':
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='msc_story') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='msc_story') limit 1),0) can_delete,organization_name,individual_name,data_source,introduction,to_char(date_submission::date,'DD/MM/YYYY') date_submission, changes,story_detail,significant_change,conclusion,future_change_envisaged,instance_id  from vw_msc_story WHERE date_submission::date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(to_date) + "','DD/MM/YYYY') and user_id=" + str(
            user_id) + " order by instance_id desc"
    elif role == 'Admin':
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='msc_story') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='msc_story') limit 1),0) can_delete,organization_name,individual_name,data_source,introduction,to_char(date_submission::date,'DD/MM/YYYY') date_submission, changes,story_detail,significant_change,conclusion,future_change_envisaged,instance_id  from vw_msc_story WHERE date_submission::date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(to_date) + "','DD/MM/YYYY') order by instance_id desc"
    else:
        query = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='msc_story') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='msc_story') limit 1),0) can_delete,organization_name,individual_name,data_source,introduction,to_char(date_submission::date,'DD/MM/YYYY') date_submission, changes,story_detail,significant_change,conclusion,future_change_envisaged,instance_id  from vw_msc_story WHERE date_submission::date  BETWEEN to_date('" + str(
            from_date) + "','DD/MM/YYYY') AND to_date('" + str(
            to_date) + "','DD/MM/YYYY') and user_id=any(select user_id from usermodule_usermoduleprofile where rsc_name_id = any(select rsc_name_id from usermodule_usermoduleprofile where user_id =" + str(
            user_id) + "))  order by instance_id desc"
    print(query)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def msc_story_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='msc_story'")
    redirected_url = '/asf/msc_story_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


# Event
@login_required
def event_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_workshop'")
    return render(request, 'asfmodule/event_list.html', {'form_id': form_id})


@csrf_exempt
def get_event_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        q = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='event_workshop') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='event_workshop') limit 1),0) can_delete,ROW_NUMBER() OVER(ORDER BY id) AS serial_no,id,json->>'participant/total_participant' total_participant, to_char((json->>'event/event_start_time')::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,to_char((json->>'event/event_end_time')::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_end_date, (select field_name from geo_data where geocode = (json->>'geo/district')) district, (select field_name from geo_data where geocode = (json->>'geo/upazila')) upazila from vw_groupevent where (json ->> 'geo/upazila') IN ( ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid limit 1) FROM usermodule_catchment_area WHERE user_id = " + str(
            user_id) + ") UNION ( SELECT geocode FROM geo_data WHERE field_parent_id = ANY ( SELECT geoid FROM usermodule_catchment_area WHERE user_id = " + str(
            user_id) + ") AND field_type_id = 88))"
    except Exception:
        q = "select COALESCE((select can_edit from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='event_workshop') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = " + str(
            user_id) + " and xform_id = (select id from logger_xform where id_string='event_workshop') limit 1),0) can_delete,ROW_NUMBER() OVER(ORDER BY id) AS serial_no,id,json->>'participant/total_participant' total_participant, to_char((json->>'event/event_start_time')::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,to_char((json->>'event/event_end_time')::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_end_date, (select field_name from geo_data where geocode = (json->>'geo/district')) district, (select field_name from geo_data where geocode = (json->>'geo/upazila')) upazila from vw_groupevent"

    main_df = pd.read_sql(q, connection)

    eventname_q = "select id ,(select event_name from iom_event where code =json->>'event/event_name' limit 1) event_name from vw_groupevent"
    eventname_df = pd.read_sql(eventname_q, connection)

    main_df = main_df.merge(eventname_df, on=['id'], how='left', )
    data = main_df.to_dict('records')

    data = json.dumps(data, default=decimal_date_default)
    return HttpResponse(data)


def event_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    # server_address = '192.168.22.133:8001'
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_workshop'")
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/event_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'instance_id': instance_id})


# Event Workshop List
@login_required
def event_workshop_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_workshop'")
    return render(request, 'asfmodule/event_workshop_list.html', {'form_id': form_id})


@csrf_exempt
def get_event_workshop_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = """ SELECT   COALESCE(
                    (
                    SELECT can_edit
                    FROM   vwrolewiseformpermission
                    WHERE  user_id = """ + str(user_id) + """
                    AND    xform_id =
                           (
                                  SELECT id
                                  FROM   logger_xform
                                  WHERE  id_string='event_workshop') limit 1),0) can_edit,
         COALESCE(
                    (
                    SELECT can_delete
                    FROM   vwrolewiseformpermission
                    WHERE  user_id = """ + str(user_id) + """
                    AND    xform_id =
                           (
                                  SELECT id
                                  FROM   logger_xform
                                  WHERE  id_string='event_workshop') limit 1),0)    can_delete,
         row_number() OVER (ORDER BY id desc)                                         AS serial_no,
         event_name,
         id,
         to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
         to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
         username,
         district_label district ,
         upazila_label  upazila ,
         union_label    union_name ,
         para_bazar_school ,
         CASE
                  WHEN id::text =
                           (
                                  SELECT event_id::text
                                  FROM   vw_event_workshop_observation_checklist
                                  WHERE  event_id::int = vw_merged_event_workshop.id limit 1) THEN 1
                  ELSE 0
         END observation ,
         0   review
            FROM     vw_merged_event_workshop
            WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))"""
    except Exception:
        query = """ select  COALESCE(
                             (
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_workshop') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_workshop') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                                          event_name,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_workshop_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_workshop.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  0 review  from vw_merged_event_workshop """
    print query
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def event_workshop_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_workshop'")
    redirected_url = '/asf/event_workshop_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def event_workshop_profile(request, event_id):
    qry = """
        select id event_id,
        to_char(event_start_time::date,'DD/MM/YYYY') date_created,
        username,
        district_label district,
        upazila_label upazila,
        union_label union_name,
        para_bazar_school,
        village,
        male_greater_equal_18,
        male_less_18,
        female_greater_equal_18,
        female_less_18,
        total_participant,(select participant_category from vw_event_participants where event_id = '""" + str(
        event_id) + """') as participant_category,
                  remarks
      from vw_merged_event_workshop where id = """ + str(event_id) + """
    """
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_greater_equal_18 = df.male_greater_equal_18.tolist()[0] if len(df.male_greater_equal_18.tolist()) and \
                                                                    df.male_greater_equal_18.tolist()[
                                                                        0] is not None else ''
    male_less_18 = df.male_less_18.tolist()[0] if len(df.male_less_18.tolist()) and df.male_less_18.tolist()[
                                                                                        0] is not None  else ''
    female_greater_equal_18 = df.female_greater_equal_18.tolist()[0] if len(df.female_greater_equal_18.tolist()) and \
                                                                        df.female_greater_equal_18.tolist()[
                                                                            0] is not None  else ''
    female_less_18 = df.female_less_18.tolist()[0] if len(df.female_less_18.tolist()) and df.female_less_18.tolist()[
                                                                                              0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{700,702}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)

    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'event_workshop_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_greater_equal_18': male_greater_equal_18,
        'female_greater_equal_18': female_greater_equal_18,
        'male_less_18': male_less_18,
        'female_less_18': female_less_18,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })


# IPT show List
@login_required
def ipt_show_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_ipt_show'")
    return render(request, 'asfmodule/ipt_show_list.html', {'form_id': form_id})


@csrf_exempt
def get_ipt_show_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        # query = "with t as( select COALESCE((select can_edit from vwrolewiseformpermission where user_id = "+str(user_id)+" and xform_id = (select id from logger_xform where id_string='event_ipt_show') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = "+str(user_id)+" and xform_id = (select id from logger_xform where id_string='event_ipt_show') limit 1),0) can_delete,ROW_NUMBER() OVER (ORDER BY id) AS serial_no,id,to_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created,(select username from auth_user where id = user_id limit 1) username , (select field_name from geo_data where geocode = (json->>'geo/district')) district ,(select field_name from geo_data where geocode = (json->>'geo/upazila')) upazila , coalesce((select field_name from geo_data where geocode = (json->>'geo/union')),'') union_name ,json->>'geo/para_bazar_school' para_bazar_school ,case when id::text = (select (json->>'event_id')::text from logger_instance where xform_id = (select id from logger_xform where id_string = 'ipt_show_checklist') and deleted_at is null and (json->>'event_id') is not null and (json->>'event_id')::int = st.id limit 1 ) then 1 else 0 end observation ,case when id::text = (select (json->>'event_id')::text from logger_instance where xform_id = (select id from logger_xform where id_string = 'event_ipt_show_review') and deleted_at is null and (json->>'event_id') is not null and (json->>'event_id')::int = st.id limit 1) then 1 else 0 end review from logger_instance st where xform_id = (select id from logger_xform where id_string = 'event_ipt_show') and deleted_at is null and (json ->> 'geo/upazila') IN ( ( SELECT ( SELECT geocode FROM geo_data WHERE id = geoid limit 1) FROM usermodule_catchment_area WHERE user_id = "+str(user_id)+") UNION ( SELECT geocode FROM geo_data WHERE field_parent_id = ANY ( SELECT geoid FROM usermodule_catchment_area WHERE user_id = "+str(user_id)+") AND field_type_id = 88)) )select * from t"
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_ipt_show') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_ipt_show') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_ipt_show_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_ipt_show.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_ipt_show_review
                                           WHERE  event_id::int = vw_merged_event_ipt_show.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_ipt_show
                  WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))"""
    except Exception:
        # query = "with t as( select COALESCE((select can_edit from vwrolewiseformpermission where user_id = "+str(user_id)+" and xform_id = (select id from logger_xform where id_string='event_ipt_show') limit 1),0) can_edit,COALESCE((select can_delete from vwrolewiseformpermission where user_id = "+str(user_id)+" and xform_id = (select id from logger_xform where id_string='event_ipt_show') limit 1),0) can_delete,ROW_NUMBER() OVER (ORDER BY id) AS serial_no,id,to_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created,(select username from auth_user where id = user_id limit 1) username , (select field_name from geo_data where geocode = (json->>'geo/district')) district ,(select field_name from geo_data where geocode = (json->>'geo/upazila')) upazila , coalesce((select field_name from geo_data where geocode = (json->>'geo/union')),'') union_name ,json->>'geo/para_bazar_school' para_bazar_school ,case when id::text = (select (json->>'event_id')::text from logger_instance where xform_id = (select id from logger_xform where id_string = 'ipt_show_checklist') and deleted_at is null and (json->>'event_id') is not null and (json->>'event_id')::int = st.id limit 1 ) then 1 else 0 end observation ,case when id::text = (select (json->>'event_id')::text from logger_instance where xform_id = (select id from logger_xform where id_string = 'event_ipt_show_review') and deleted_at is null and (json->>'event_id') is not null and (json->>'event_id')::int = st.id limit 1) then 1 else 0 end review from logger_instance st where xform_id = (select id from logger_xform where id_string = 'event_ipt_show') and deleted_at is null)select * from t"
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_ipt_show') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_ipt_show') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_ipt_show_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_ipt_show.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_ipt_show_review
                                           WHERE  event_id::int = vw_merged_event_ipt_show.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_ipt_show
        """
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def ipt_show_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_ipt_show'")
    redirected_url = '/asf/ipt_show_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def ipt_profile(request, event_id):
    qry = "WITH t AS( SELECT id event_id, To_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created, ( SELECT username FROM auth_user WHERE id = user_id limit 1) username , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/district')) district , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/upazila')) upazila , COALESCE( ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/union')),'') union_name , json->>'geo/para_bazar_school' para_bazar_school , json->>'geo/village' village FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_ipt_show') AND deleted_at IS NULL AND id = " + str(
        event_id) + "), t1 AS ( SELECT json->>'event_id' event_id, json->>'participant/male_greater_equal_18' male_greater_equal_18 , json->>'participant/male_less_18' male_less_18 , json->>'participant/female_greater_equal_18' female_greater_equal_18 , json->>'participant/female_less_18' female_less_18 , json->>'participant/total_participant' total_participant , (select participant_category from vw_event_participants where event_id = '" + str(
        event_id) + "') as participant_category, json->>'remarks' remarks FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_attendance_ipt_show') AND deleted_at IS NULL AND ( json->>'event_id')::int = " + str(
        event_id) + ") SELECT t.event_id, t.date_created , t.username, t.district , t.upazila, t.union_name , t.para_bazar_school, t.village , t1.male_greater_equal_18, t1.male_less_18, t1.female_greater_equal_18, t1.female_less_18, t1.total_participant, t1.participant_category, t1.remarks FROM t LEFT JOIN t1 ON t.event_id = t1.event_id::int"
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_greater_equal_18 = df.male_greater_equal_18.tolist()[0] if len(df.male_greater_equal_18.tolist()) and \
                                                                    df.male_greater_equal_18.tolist()[
                                                                        0] is not None else ''
    male_less_18 = df.male_less_18.tolist()[0] if len(df.male_less_18.tolist()) and df.male_less_18.tolist()[
                                                                                        0] is not None  else ''
    female_greater_equal_18 = df.female_greater_equal_18.tolist()[0] if len(df.female_greater_equal_18.tolist()) and \
                                                                        df.female_greater_equal_18.tolist()[
                                                                            0] is not None  else ''
    female_less_18 = df.female_less_18.tolist()[0] if len(df.female_less_18.tolist()) and df.female_less_18.tolist()[
                                                                                              0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{100,101,102}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)

    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'ipt_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_greater_equal_18': male_greater_equal_18,
        'female_greater_equal_18': female_greater_equal_18,
        'male_less_18': male_less_18,
        'female_less_18': female_less_18,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })


@csrf_exempt
def get_events_forms_data(request):
    category_id = request.POST.get('category_id')
    event_id = request.POST.get('event_id')
    user_id = request.user.id
    query = """ WITH t AS( SELECT ( SELECT title FROM logger_xform WHERE id = form_id), form_id,rf.can_edit,rf.can_delete FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND category_id = """ + str(
        category_id) + """ AND fc.form_id = rf.xform_id AND user_id = """ + str(
        user_id) + """) , t1 AS ( SELECT logger_instance.id log_ins_id, json->>'event_id'::text event_id, * FROM t, logger_instance WHERE t.form_id = logger_instance.xform_id and deleted_at is null order by date_created desc) SELECT '<div class="panel panel-default" ><div class="panel-heading forms_data_panel_heading" role="tab" id="heading' ||log_ins_id ||'"><h4 class="panel-title forms_data_panel_title"><a id="data_id_' ||log_ins_id ||'" class="collapsed" onclick="load_forms_data(' ||log_ins_id ||',''data_view' || log_ins_id ||''',1)" role="button" data-toggle="collapse" href="#collapse' || log_ins_id ||'" aria-expanded="false" aria-controls="collapse' ||log_ins_id ||'">' || To_char(date_created :: DATE, 'DD/MM/YYYY') ||'</a><span style="margin-left:30%">' || Replace(Greatest(title, Rpad(title, 32, ' ')) :: text, ' ', '&nbsp;') ||'</span>' || case when can_edit = 1 then '<a onclick="load_forms_edit_mode(' || xform_id ||',' || log_ins_id || ')" class="pull-right" style="cursor:pointer;margin-right: -5px;margin-left: 11px;" data-toggle="modal" data-target="#myModal"><i class="fa fa-pencil"></i></a>' else '' end || case when can_delete = 1 then '<a onclick="delete_forms_data(' || xform_id ||',' || log_ins_id || ')" class="pull-right" style="cursor:pointer" data-toggle="modal" data-target="#myModal"><i class="fa fa-trash"></i></a>' else '' end || '</h4></div><div id="collapse' || log_ins_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading' || log_ins_id ||'"><div class="panel-body"><div class="ribbon" id="data_view' || log_ins_id ||'"></div></div></div></div>' AS form_str FROM t1 WHERE event_id LIKE '%""" + str(
        event_id) + """%' """
    print(query)
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    return HttpResponse(main_str)


# Video Show List
@login_required
def video_show_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_video_show'")
    return render(request, 'asfmodule/video_show_list.html', {'form_id': form_id})


@csrf_exempt
def get_video_show_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_video_show') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_video_show') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_video_show_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_video_show.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_video_show_review
                                           WHERE  event_id::int = vw_merged_event_video_show.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_video_show
                 WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))
        """
    except Exception:
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_video_show') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_video_show') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_video_show_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_video_show.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_video_show_review
                                           WHERE  event_id::int = vw_merged_event_video_show.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_video_show
        """
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def video_show_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_video_show'")
    redirected_url = '/asf/video_show_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def video_show_profile(request, event_id):
    qry = "with t as( SELECT id event_id, To_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created, ( SELECT username FROM auth_user WHERE id = user_id limit 1) username , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/district')) district , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/upazila')) upazila , COALESCE( ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/union')),'') union_name , json->>'geo/para_bazar_school' para_bazar_school , json->>'geo/village' village FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_video_show') AND deleted_at IS NULL AND id = " + str(
        event_id) + "), t1 as ( select json->>'event_id' event_id, json->>'participant/male_greater_equal_18' male_greater_equal_18 , json->>'participant/male_less_18' male_less_18 , json->>'participant/female_greater_equal_18' female_greater_equal_18 , json->>'participant/female_less_18' female_less_18 , json->>'participant/total_participant' total_participant , (select participant_category from vw_event_participants where event_id = '" + str(
        event_id) + "') as participant_category, json->>'remarks' remarks FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_attendance_video_show') AND deleted_at IS NULL and (json->>'event_id')::int = " + str(
        event_id) + " )select t.event_id,t.date_created ,t.username,t.district ,t.upazila,t.union_name ,t.para_bazar_school,t.village ,t1.male_greater_equal_18, t1.male_less_18, t1.female_greater_equal_18, t1.female_less_18, t1.total_participant, t1.participant_category, t1.remarks from t left join t1 on t.event_id = t1.event_id::int"
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_greater_equal_18 = df.male_greater_equal_18.tolist()[0] if len(df.male_greater_equal_18.tolist()) and \
                                                                    df.male_greater_equal_18.tolist()[
                                                                        0] is not None else ''
    male_less_18 = df.male_less_18.tolist()[0] if len(df.male_less_18.tolist()) and df.male_less_18.tolist()[
                                                                                        0] is not None  else ''
    female_greater_equal_18 = df.female_greater_equal_18.tolist()[0] if len(df.female_greater_equal_18.tolist()) and \
                                                                        df.female_greater_equal_18.tolist()[
                                                                            0] is not None  else ''
    female_less_18 = df.female_less_18.tolist()[0] if len(df.female_less_18.tolist()) and df.female_less_18.tolist()[
                                                                                              0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{300,301,302}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)

    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'video_show_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_greater_equal_18': male_greater_equal_18,
        'female_greater_equal_18': female_greater_equal_18,
        'male_less_18': male_less_18,
        'female_less_18': female_less_18,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })


# School Quiz List
@login_required
def school_quiz_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_school_quiz'")
    return render(request, 'asfmodule/school_quiz_list.html', {'form_id': form_id})


@csrf_exempt
def get_school_quiz_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_school_quiz') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_school_quiz') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_quiz_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_school_quiz.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_quiz_review
                                           WHERE  event_id::int = vw_merged_event_school_quiz.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_school_quiz
                  WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))
        """
    except Exception:
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_school_quiz') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_school_quiz') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_quiz_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_school_quiz.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_quiz_review
                                           WHERE  event_id::int = vw_merged_event_school_quiz.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_school_quiz
        """
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def school_quiz_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_school_quiz'")
    redirected_url = '/asf/school_quiz_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def school_quiz_profile(request, event_id):
    qry = "with t as( SELECT id event_id, To_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created, ( SELECT username FROM auth_user WHERE id = user_id limit 1) username , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/district')) district , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/upazila')) upazila , COALESCE( ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/union')),'') union_name , json->>'geo/para_bazar_school' para_bazar_school , json->>'geo/village' village FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_school_quiz') AND deleted_at IS NULL AND id = " + str(
        event_id) + "), t1 as ( select json->>'event_id' event_id, json->>'participant/male_11_14' male_11_14 , json->>'participant/male_15_16' male_15_16 , json->>'participant/female_11_14' female_11_14 , json->>'participant/female_15_16' female_15_16 , json->>'participant/total_participant' total_participant ,(select participant_category from vw_event_participants where event_id = '" + str(
        event_id) + "') as participant_category , json->>'remarks' remarks FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_attendance_school_quiz') AND deleted_at IS NULL and (json->>'event_id')::int = " + str(
        event_id) + " )select t.event_id,t.date_created ,t.username,t.district ,t.upazila,t.union_name ,t.para_bazar_school,t.village ,t1.male_11_14, t1.male_15_16, t1.female_11_14, t1.female_15_16, t1.total_participant, t1.participant_category, t1.remarks from t left join t1 on t.event_id = t1.event_id::int"
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_11_14 = df.male_11_14.tolist()[0] if len(df.male_11_14.tolist()) and df.male_11_14.tolist()[
                                                                                  0] is not None else ''
    male_15_16 = df.male_15_16.tolist()[0] if len(df.male_15_16.tolist()) and df.male_15_16.tolist()[
                                                                                  0] is not None  else ''
    female_11_14 = df.female_11_14.tolist()[0] if len(df.female_11_14.tolist()) and df.female_11_14.tolist()[
                                                                                        0] is not None  else ''
    female_15_16 = df.female_15_16.tolist()[0] if len(df.female_15_16.tolist()) and df.female_15_16.tolist()[
                                                                                        0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{400,401,402}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'school_quiz_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_11_14': male_11_14,
        'male_15_16': male_15_16,
        'female_11_14': female_11_14,
        'female_15_16': female_15_16,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })


# Tea Stall Meeting List
@login_required
def tea_stall_meeting_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_tea_stall_meeting'")
    return render(request, 'asfmodule/tea_stall_meeting_list.html', {'form_id': form_id})


@csrf_exempt
def get_tea_stall_meeting_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_tea_stall_meeting') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_tea_stall_meeting') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_tea_stall_meeting_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_tea_stall_meeting.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_tea_stall_meeting_review
                                           WHERE  event_id::int = vw_merged_event_tea_stall_meeting.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_tea_stall_meeting
                  WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))
        """
    except Exception:
        query = """
        select  COALESCE((
                             SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_tea_stall_meeting') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_tea_stall_meeting') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_tea_stall_meeting_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_tea_stall_meeting.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_tea_stall_meeting_review
                                           WHERE  event_id::int = vw_merged_event_tea_stall_meeting.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_tea_stall_meeting
        """
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def tea_stall_meeting_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_tea_stall_meeting'")
    redirected_url = '/asf/tea_stall_meeting_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def tea_stall_meeting_profile(request, event_id):
    qry = "with t as( SELECT id event_id, To_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created, ( SELECT username FROM auth_user WHERE id = user_id limit 1) username , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/district')) district , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/upazila')) upazila , COALESCE( ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/union')),'') union_name , json->>'geo/para_bazar_school' para_bazar_school , json->>'geo/village' village FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_tea_stall_meeting') AND deleted_at IS NULL AND id = " + str(
        event_id) + "), t1 as ( select json->>'event_id' event_id, json->>'participant/male_greater_equal_18' male_greater_equal_18 , json->>'participant/male_less_18' male_less_18 , json->>'participant/female_greater_equal_18' female_greater_equal_18 , json->>'participant/female_less_18' female_less_18 , json->>'participant/total_participant' total_participant ,(select participant_category from vw_event_participants where event_id = '" + str(
        event_id) + "') as participant_category, json->>'remarks' remarks FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_attendance_tea_stall_meeting') AND deleted_at IS NULL and (json->>'event_id')::int = " + str(
        event_id) + " )select t.event_id,t.date_created ,t.username,t.district ,t.upazila,t.union_name ,t.para_bazar_school,t.village ,t1.male_greater_equal_18, t1.male_less_18, t1.female_greater_equal_18, t1.female_less_18, t1.total_participant, t1.participant_category, t1.remarks from t left join t1 on t.event_id = t1.event_id::int"
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_greater_equal_18 = df.male_greater_equal_18.tolist()[0] if len(df.male_greater_equal_18.tolist()) and \
                                                                    df.male_greater_equal_18.tolist()[
                                                                        0] is not None else ''
    male_less_18 = df.male_less_18.tolist()[0] if len(df.male_less_18.tolist()) and df.male_less_18.tolist()[
                                                                                        0] is not None  else ''
    female_greater_equal_18 = df.female_greater_equal_18.tolist()[0] if len(df.female_greater_equal_18.tolist()) and \
                                                                        df.female_greater_equal_18.tolist()[
                                                                            0] is not None  else ''
    female_less_18 = df.female_less_18.tolist()[0] if len(df.female_less_18.tolist()) and df.female_less_18.tolist()[
                                                                                              0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{200,201,202}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)

    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'tea_stall_meeting_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_greater_equal_18': male_greater_equal_18,
        'female_greater_equal_18': female_greater_equal_18,
        'male_less_18': male_less_18,
        'female_less_18': female_less_18,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })


# Paper clipping
@login_required
def paper_clipping_list(request):
    return render(request, 'asfmodule/paper_clipping_list.html')


@csrf_exempt
def get_paper_clipping_list(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "WITH t AS(SELECT Coalesce(json ->> 'newspaper_name', '') newspaper_name, Coalesce(json ->> 'news_publish_date', '') news_publish_date, Coalesce(json ->> 'newspaper_page_no', '') newspaper_page_no, Coalesce(json ->> 'category', '') category, Coalesce(json ->> 'remarks', '') remarks, Coalesce(json ->> 'news_scanned_file', '') news_scanned_file, Coalesce(json ->> 'news_publish_date', '') s_date FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'paper_clipping')) SELECT newspaper_name,to_char(news_publish_date::date,'DD/MM/YYYY') news_publish_date, newspaper_page_no, case when category = '1' then 'Advertisement' when category = '2' then 'Funding' when category = '3' then 'Medical' when category = '4' then 'Notification' when category = '5' then 'Other burn' when category = '99' then 'Others' when category = '6' then 'Partners' when category = '7' then 'RAPU' when category = '8' then 'SRU' end category, remarks, news_scanned_file FROM t WHERE s_date :: DATE BETWEEN To_date('" + str(
        from_date) + "', 'DD/MM/YYYY') AND to_date('" + str(to_date) + "', 'DD/MM/YYYY')"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


def paper_clipping_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='paper_clipping'")
    return render(request, 'asfmodule/event_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id})


@login_required
def dashboard(request):
    return render(request, 'asfmodule/dashboard.html')


@csrf_exempt
def get_dashboard_data(request):
    from datetime import datetime
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = "with t as( select count(*) incident_cnt from asf_case where status = 'Valid' and incident_date::date between '" + str(
        from_date) + "' AND '" + str(
        to_date) + "'), t1 as ( select count(*) victim_cnt from asf_victim where case_id::int = any(select id from asf_case where status = 'Valid') and  created_at::date between '" + str(
        from_date) + "' AND '" + str(
        to_date) + "' ),t2 as( select count(*) notified_cnt from asf_victim where case_id::int = any(select id from asf_case where status = 'Valid') and notified_within_24h = 'Yes'  and created_at::date between '" + str(
        from_date) + "' AND '" + str(to_date) + "' )select * from t,t1,t2"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    incident_tiles_cnt = df.incident_cnt.tolist()[0]
    victim_tiles_cnt = df.victim_cnt.tolist()[0]
    notified_tiles_cnt = df.notified_cnt.tolist()[0]
    ################### INCIDENT AND VICTIM TREND & COLUMN CHART #############
    ##########################################################################
    date_format = "%Y-%m-%d"
    a = datetime.strptime(from_date, date_format)
    b = datetime.strptime(to_date, date_format)
    delta = b - a
    print(delta)
    if int(delta.days) < 30:
        # date wise
        qry = """ WITH victim_tbl AS( SELECT *, ( SELECT incident_date FROM asf_case WHERE case_id::int = id) FROM asf_victim WHERE case_id::int = ANY ( SELECT id FROM asf_case WHERE incident_date::date BETWEEN '""" + str(
            from_date) + """' AND '""" + str(
            to_date) + """' AND status ='Valid') ) ,inc_tbl AS ( SELECT incident_date::date AS categories, 'Incident'::text AS names , count(*) as cnt FROM asf_case WHERE incident_date::date BETWEEN '""" + str(
            from_date) + """' AND '""" + str(
            to_date) + """' AND    status ='Valid' GROUP BY incident_date::date ), vic_tbl AS ( SELECT incident_date::date AS categories, 'Victim'::text AS names, count(*) cnt FROM victim_tbl GROUP by incident_date::date ), unix_all_date AS ( SELECT categories FROM inc_tbl UNION SELECT categories FROM vic_tbl ), date_not_in_incident_tbl AS ( SELECT DISTINCT categories FROM unix_all_date EXCEPT SELECT categories FROM inc_tbl ), date_not_in_victim_tbl AS ( SELECT DISTINCT categories FROM unix_all_date EXCEPT SELECT categories FROM vic_tbl ), ftbl AS ( ( SELECT * FROM inc_tbl UNION SELECT categories, 'Incident'::text AS names, 0 AS cnt FROM date_not_in_incident_tbl ) UNION ALL ( SELECT * FROM vic_tbl UNION SELECT categories, 'Victim'::text AS names, 0 AS cnt FROM date_not_in_victim_tbl ) ) SELECT categories, names, cnt FROM ftbl ORDER BY categories asc """

    elif int(delta.days) < 365:
        # month wise
        qry = """ WITH victim_tbl as( select *,(select incident_date from asf_case where case_id::int = id) from asf_victim where case_id::int = any(select id from asf_case WHERE incident_date::date BETWEEN '""" + str(
            from_date) + """' AND '""" + str(
            to_date) + """' and status ='Valid') ) ,inc_tbl AS ( SELECT extract('month' from incident_date::date) ||','|| to_char(incident_date::date,'YY') AS categories, 'Incident'::text AS names ,count(*) cnt FROM asf_case WHERE incident_date::date BETWEEN '""" + str(
            from_date) + """' AND '""" + str(
            to_date) + """' AND    status ='Valid' GROUP BY extract('month' from incident_date::date) ||','|| to_char(incident_date::date,'YY') ), vic_tbl AS ( SELECT extract('month' from incident_date::date) ||','|| to_char(incident_date::date,'YY') AS categories, 'Victim'::text AS names, count(*) cnt FROM victim_tbl GROUP BY extract('month' from incident_date::date) ||','|| to_char(incident_date::date,'YY') ), unix_all_date AS ( SELECT categories FROM inc_tbl UNION SELECT categories FROM vic_tbl ), month_not_in_incident_tbl AS ( SELECT DISTINCT categories FROM unix_all_date EXCEPT SELECT categories FROM inc_tbl ), month_not_in_victim_tbl AS ( SELECT DISTINCT categories FROM unix_all_date EXCEPT SELECT categories FROM vic_tbl ), ftbl AS ( ( SELECT * FROM inc_tbl UNION SELECT categories, 'Incident'::text AS names, 0 AS cnt FROM month_not_in_incident_tbl ) UNION ALL ( SELECT * FROM vic_tbl UNION SELECT categories, 'Victim'::text AS names, 0 AS cnt FROM month_not_in_victim_tbl ) ) SELECT trim(to_char(to_timestamp ( left(categories, strpos(categories, ',') - 1)::text, 'MM'), 'Month')) ||','|| substring(categories from  strpos(categories, ',') + 1)  categories, names, cnt FROM ftbl ORDER BY substring(categories from  strpos(categories, ',') + 1)::int asc,left(categories, strpos(categories, ',') - 1)::int asc"""
    else:
        # year wise
        qry = """WITH victim_tbl AS( SELECT *, ( SELECT incident_date FROM asf_case WHERE case_id::int = id) FROM asf_victim WHERE case_id::int = ANY ( SELECT id FROM asf_case WHERE incident_date::date BETWEEN '""" + str(
            from_date) + """' AND '""" + str(
            to_date) + """' AND status ='Valid')) ,inc_tbl AS ( SELECT extract('year' FROM incident_date::date) AS categories, 'Incident'::text AS names , count(*) cnt FROM asf_case WHERE incident_date::date BETWEEN '""" + str(
            from_date) + """' AND '""" + str(
            to_date) + """' AND status ='Valid' GROUP BY extract('year' FROM incident_date::date) ), vic_tbl AS ( SELECT extract('year' FROM incident_date::date) AS categories, 'Victim'::text AS names, count(*) cnt FROM victim_tbl GROUP BY extract('year' FROM incident_date::date) ) , unix_all_date AS ( SELECT categories FROM inc_tbl UNION SELECT categories FROM vic_tbl ), month_not_in_incident_tbl AS ( SELECT DISTINCT categories FROM unix_all_date EXCEPT SELECT categories FROM inc_tbl ), month_not_in_victim_tbl AS ( SELECT DISTINCT categories FROM unix_all_date EXCEPT SELECT categories FROM vic_tbl ), ftbl AS ( ( SELECT * FROM inc_tbl UNION SELECT categories, 'Incident'::text AS names, 0 AS cnt FROM month_not_in_incident_tbl ) UNION ALL ( SELECT * FROM vic_tbl UNION SELECT categories, 'Victim'::text AS names, 0 AS cnt FROM month_not_in_victim_tbl ) ) SELECT categories, names, cnt FROM ftbl ORDER BY categories asc"""
    print(qry)
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    data = []
    name = []
    categories = []
    if not df.empty:
        for each in df['names'].unique().tolist():
            data.append(df['cnt'][df['names'] == each].tolist())

        categories = json.dumps(df['categories'].unique().tolist(), default=decimal_date_default)
        name = json.dumps(df['names'].unique().tolist(), default=decimal_date_default)
        data = json.dumps(data, default=decimal_date_default)

    ##############  INCIDENT CAUSE PIE  ##################
    ######################################################
    qry = """WITH t AS( SELECT Count(*)::float total FROM asf_case WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' AND status ='Valid'), t1 AS ( SELECT incident_cause, count(*) cnt, round(count(*)*100/total)::int percentage FROM asf_case, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' AND status ='Valid' GROUP BY incident_cause, total), tt AS ( SELECT 'Addiction' AS incident_cause UNION ALL SELECT 'Dowry' AS incident_cause UNION ALL SELECT 'Family related dispute' AS incident_cause UNION ALL SELECT 'Land/property/money dispute' AS incident_cause UNION ALL SELECT 'Marital dispute' AS incident_cause UNION ALL SELECT 'Unknown' AS incident_cause UNION ALL SELECT 'Refusal of love' AS incident_cause UNION ALL SELECT 'Refusal of sex' AS incident_cause UNION ALL SELECT 'Refusal of marriage' AS incident_cause UNION ALL SELECT 'Others' AS incident_cause ) SELECT tt.incident_cause as categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.incident_cause = t1.incident_cause"""
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    incident_cause_pie_data = {}
    incident_categories = df.categories.tolist()
    incident_percentage = df.percentage.tolist()
    incident_cnt = df.cnt.tolist()
    # color = ['#0B336C','#0AAECE','#3A89C3','#0069b7','#08C4BB','#9999ff']
    incident_cause_pie_data = []
    for n, y, count in zip(incident_categories, incident_percentage, incident_cnt):
        incident_cause_pie_data.append(
            {
                'name': str(n),
                'y': y,
                'count': count
            }
        )
    ##################### EDUCATION PIE ########################
    ############################################################
    qry = """ with vtc_tbl as( select *,(select incident_date from asf_case where id = case_id::int AND status ='Valid' limit 1) from asf_victim) ,t AS ( SELECT Count(*)::float total FROM vtc_tbl WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' ), t1 AS ( SELECT education, count(*) cnt, round(count(*)*100/total)::int percentage FROM vtc_tbl, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' GROUP BY education, total), tt AS ( SELECT 'Nil' AS education UNION ALL SELECT 'Primary' AS education UNION ALL SELECT 'Junior Secondary' AS education UNION ALL SELECT 'SSC/Equivalence' AS education UNION ALL SELECT 'HSC/Equivalence' AS education UNION ALL SELECT 'Graduation' AS education UNION ALL SELECT 'Post Graduation' AS education) SELECT tt.education categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.education = t1.education """
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    education_pie_data = {}
    education_categories = df.categories.tolist()
    education_percentage = df.percentage.tolist()
    education_cnt = df.cnt.tolist()
    # color = ['#0B336C','#0AAECE','#3A89C3','#0069b7','#08C4BB','#9999ff']
    education_pie_data = []
    for n, y, count in zip(education_categories, education_percentage, education_cnt):
        education_pie_data.append(
            {
                'name': str(n),
                'y': y,
                'count': count
            }
        )

    ##################### AGE RANGE PIE ########################
    ############################################################
    qry = """ with vtc_tbl as( select *,(select incident_date from asf_case where id = case_id::int AND status ='Valid' limit 1) from asf_victim) ,t AS ( SELECT Count(*)::float total FROM vtc_tbl WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' ), t1 AS ( SELECT '0-5' AS age_range, count(*) cnt, round(count(*)*100/total)::int percentage FROM vtc_tbl, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' and victim_age::int between 0 and 5 GROUP BY total union all SELECT '6-12' AS age_range, count(*) cnt, round(count(*)*100/total)::int percentage FROM vtc_tbl, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' and victim_age::int between 6 and 12 GROUP BY total union all SELECT '13-18' AS age_range, count(*) cnt, round(count(*)*100/total)::int percentage FROM vtc_tbl, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' and victim_age::int between 13 and 18 GROUP BY total union all SELECT '19-35' AS age_range, count(*) cnt, round(count(*)*100/total)::int percentage FROM vtc_tbl, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' and victim_age::int between 19 and 35 GROUP BY total union all SELECT '36+' AS age_range, count(*) cnt, round(count(*)*100/total)::int percentage FROM vtc_tbl, t WHERE incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' and victim_age::int >= 36 GROUP BY total ), tt AS ( SELECT '0-5' AS age_range UNION ALL SELECT '6-12' AS age_range UNION ALL SELECT '13-18' AS age_range UNION ALL SELECT '19-35' AS age_range UNION ALL SELECT '36+' AS age_range ) SELECT tt.age_range categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.age_range = t1.age_range """
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    age_range_pie_data = {}
    age_range_categories = df.categories.tolist()
    age_range_percentage = df.percentage.tolist()
    age_range_cnt = df.cnt.tolist()
    # color = ['#0B336C','#0AAECE','#3A89C3','#0069b7','#08C4BB','#9999ff']
    age_range_pie_data = []
    for n, y, count in zip(age_range_categories, age_range_percentage, age_range_cnt):
        age_range_pie_data.append(
            {
                'name': str(n),
                'y': y,
                'count': count
            }
        )
    ##################### Tables ###############################
    ############################################################
    qry = """ with case_tbl as(select district,count(*) incident_cnt from asf_case where incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' AND status ='Valid' group by district) , vtc_tbl as ( select *,(select incident_date from asf_case where id = case_id::int AND status ='Valid' limit 1) from asf_victim),vic_tbl1 as ( select current_district,count(*) victim_cnt from vtc_tbl where current_district is not null and incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' group by current_district )select (select field_name from geo_data where id = district::int limit 1) district,incident_cnt, coalesce(victim_cnt,0) victim_cnt FROM case_tbl left join vic_tbl1 on current_district = district"""
    district_wise_data = __db_fetch_values_dict(qry)

    qry = """ with case_tbl as(select upazila,count(*) incident_cnt from asf_case where incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' AND status ='Valid' group by upazila) , vtc_tbl as ( select *,(select incident_date from asf_case where id = case_id::int AND status ='Valid' limit 1) from asf_victim),vic_tbl1 as ( select current_upazila,count(*) victim_cnt from vtc_tbl where current_upazila is not null and incident_date::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' group by current_upazila )select (select field_name from geo_data where id = upazila::int limit 1) upazila,incident_cnt, coalesce(victim_cnt,0) victim_cnt FROM case_tbl left join vic_tbl1 on current_upazila = upazila """
    upazila_wise_data = __db_fetch_values_dict(qry)
    print(qry)
    data = json.dumps({'incident_cnt': incident_tiles_cnt,
                       'victim_cnt': victim_tiles_cnt,
                       'notified_cnt': notified_tiles_cnt,
                       'categories': categories,
                       'name': name,
                       'data': data,
                       'incident_cause_pie_data': incident_cause_pie_data,
                       'education_pie_data': education_pie_data,
                       'age_range_pie_data': age_range_pie_data,
                       'district_wise_data': district_wise_data,
                       'upazila_wise_data': upazila_wise_data
                       })
    return HttpResponse(data)


@login_required
def medical_patient_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/medical_patient_report.html', {'divisions': divisions})


@csrf_exempt
def get_medical_patient_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ with asf_tbl as( select * from asf_case where status='Valid' and division like '""" + str(
        division) + """' and district like '""" + str(district) + """' and upazila like '""" + str(
        upazila) + """' and incident_date::date BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """'), acid_burn_adult_female as ( select 'Acid Burn'::text as "type",count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int > 18 and sex = 'Female' ), acid_burn_adult_male as ( select 'Acid Burn'::text as "type",count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int > 18 and sex = 'Male' ), acid_burn_children_female as ( select 'Acid Burn'::text as "type",count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int <= 18 and sex = 'Female' ), acid_burn_children_male as ( select 'Acid Burn'::text as "type",count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int <= 18 and sex = 'Male' ), acid_burn_transgender as ( select 'Acid Burn'::text as "type",count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and sex = 'Transgender' ), other_burn_adult_female as ( select 'Others'::text as "type",count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int > 18 and sex = 'Female' ), other_burn_adult_male as ( select 'Others'::text as "type",count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int > 18 and sex = 'Male' ), other_burn_children_female as ( select 'Others'::text as "type",count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int <= 18 and sex = 'Female' ), other_burn_children_male as ( select 'Others'::text as "type",count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int <= 18 and sex = 'Male' ), other_burn_transgender as ( select 'Others'::text as "type",count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and sex = 'Transgender' ),acid_table as ( select acid_burn_adult_female."type",female_adult,male_adult,female_children,male_children,transgender, female_adult+male_adult+female_children+male_children+transgender as total from acid_burn_adult_female,acid_burn_adult_male,acid_burn_children_female,acid_burn_children_male,acid_burn_transgender ), others_table as ( select other_burn_adult_female."type",female_adult,male_adult,female_children,male_children,transgender ,female_adult+male_adult+female_children+male_children+transgender as total from other_burn_adult_female,other_burn_adult_male,other_burn_children_female,other_burn_children_male,other_burn_transgender ) select * from acid_table union all select * from others_table union all select 'Total'::text as "type" ,acid_table.female_adult + others_table.female_adult, acid_table.male_adult + others_table.male_adult, acid_table.female_children + others_table.female_children, acid_table.male_children + others_table.male_children, acid_table.transgender + others_table.transgender, acid_table.total + others_table.total from acid_table,others_table """
    new_patient_data = __db_fetch_values_dict(query)
    query = """ with asf_tbl as( select * from asf_case where status='Valid' and division like '""" + str(
        division) + """' and district like '""" + str(district) + """' and upazila like '""" + str(
        upazila) + """' and incident_date::date BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """'), get_victim_id as ( select distinct json->>'victim_id' victim_id from logger_instance where xform_id = (select id from logger_xform where id_string = 'medical_readmission') ), acid_burn_adult_female as ( select 'Acid Burn'::text as "type",count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int > 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_adult_male as ( select 'Acid Burn'::text as "type",count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int > 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_children_female as ( select 'Acid Burn'::text as "type",count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int <= 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_children_male as ( select 'Acid Burn'::text as "type",count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int <= 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_transgender as ( select 'Acid Burn'::text as "type",count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and sex = 'Transgender' and victim_id = any(select victim_id from get_victim_id) ), other_burn_adult_female as ( select 'Others'::text as "type",count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int > 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), other_burn_adult_male as ( select 'Others'::text as "type",count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int > 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), other_burn_children_female as ( select 'Others'::text as "type",count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int <= 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), other_burn_children_male as ( select 'Others'::text as "type",count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int <= 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), other_burn_transgender as ( select 'Others'::text as "type",count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and sex = 'Transgender' and victim_id = any(select victim_id from get_victim_id) ),acid_table as ( select acid_burn_adult_female."type",female_adult,male_adult,female_children,male_children,transgender, female_adult+male_adult+female_children+male_children+transgender as total from acid_burn_adult_female,acid_burn_adult_male,acid_burn_children_female,acid_burn_children_male,acid_burn_transgender ), others_table as ( select other_burn_adult_female."type",female_adult,male_adult,female_children,male_children,transgender ,female_adult+male_adult+female_children+male_children+transgender as total from other_burn_adult_female,other_burn_adult_male,other_burn_children_female,other_burn_children_male,other_burn_transgender ) select * from acid_table union all select * from others_table union all select 'Total'::text as "type" ,acid_table.female_adult + others_table.female_adult, acid_table.male_adult + others_table.male_adult, acid_table.female_children + others_table.female_children, acid_table.male_children + others_table.male_children, acid_table.transgender + others_table.transgender, acid_table.total + others_table.total from acid_table,others_table """
    old_patient_data = __db_fetch_values_dict(query)

    query = """ with asf_tbl as( select * from asf_case where status='Valid' and division like '""" + str(
        division) + """' and district like '""" + str(district) + """' and upazila like '""" + str(
        upazila) + """' and incident_date::date BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """'), get_victim_id as ( select distinct json->>'victim_id' victim_id from logger_instance where xform_id = (select id from logger_xform where id_string = 'prescription_treatment_plan') ), acid_burn_adult_female as ( select 'Acid Burn'::text as "type",count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int > 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_adult_male as ( select 'Acid Burn'::text as "type",count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int > 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_children_female as ( select 'Acid Burn'::text as "type",count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int <= 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_children_male as ( select 'Acid Burn'::text as "type",count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and victim_age::int <= 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_transgender as ( select 'Acid Burn'::text as "type",count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl where burn_type='Chemical(Acid/Alkali)') and sex = 'Transgender' and victim_id = any(select victim_id from get_victim_id) ), other_burn_adult_female as ( select 'Others'::text as "type",count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int > 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), other_burn_adult_male as ( select 'Others'::text as "type",count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int > 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), other_burn_children_female as ( select 'Others'::text as "type",count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int <= 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), other_burn_children_male as ( select 'Others'::text as "type",count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and victim_age::int <= 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), other_burn_transgender as ( select 'Others'::text as "type",count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl where burn_type=any(array['Others','Flame'])) and sex = 'Transgender' and victim_id = any(select victim_id from get_victim_id) ),acid_table as ( select acid_burn_adult_female."type",female_adult,male_adult,female_children,male_children,transgender, female_adult+male_adult+female_children+male_children+transgender as total from acid_burn_adult_female,acid_burn_adult_male,acid_burn_children_female,acid_burn_children_male,acid_burn_transgender ), others_table as ( select other_burn_adult_female."type",female_adult,male_adult,female_children,male_children,transgender ,female_adult+male_adult+female_children+male_children+transgender as total from other_burn_adult_female,other_burn_adult_male,other_burn_children_female,other_burn_children_male,other_burn_transgender ) select * from acid_table union all select * from others_table union all select 'Total'::text as "type" ,acid_table.female_adult + others_table.female_adult, acid_table.male_adult + others_table.male_adult, acid_table.female_children + others_table.female_children, acid_table.male_children + others_table.male_children, acid_table.transgender + others_table.transgender, acid_table.total + others_table.total from acid_table,others_table """
    out_patient_data = __db_fetch_values_dict(query)

    data = json.dumps({
        'new_patient_data': new_patient_data,
        'old_patient_data': old_patient_data,
        'out_patient_data': out_patient_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def medical_certificate_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/medical_certificate_report.html', {'divisions': divisions})


@csrf_exempt
def get_medical_certificate_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ with asf_tbl as( select * from asf_case where status='Valid' and division like '""" + str(
        division) + """' and district like '""" + str(district) + """' and upazila like '""" + str(
        upazila) + """' and incident_date::date BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """'), get_victim_id as ( select distinct json->>'victim_id' victim_id from logger_instance where xform_id = (select id from logger_xform where id_string = 'medical_certificate') ), acid_burn_adult_female as ( select count(*) female_adult from asf_victim where case_id::int = any(select id from asf_tbl ) and victim_age::int > 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_adult_male as ( select count(*) male_adult from asf_victim where case_id::int = any(select id from asf_tbl ) and victim_age::int > 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_children_female as ( select count(*) female_children from asf_victim where case_id::int = any(select id from asf_tbl ) and victim_age::int <= 18 and sex = 'Female' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_children_male as ( select count(*) male_children from asf_victim where case_id::int = any(select id from asf_tbl ) and victim_age::int <= 18 and sex = 'Male' and victim_id = any(select victim_id from get_victim_id) ), acid_burn_transgender as ( select count(*) transgender from asf_victim where case_id::int = any(select id from asf_tbl ) and sex = 'Transgender' and victim_id = any(select victim_id from get_victim_id) ),acid_table as ( select female_adult,male_adult,female_children,male_children,transgender, female_adult+male_adult+female_children+male_children+transgender as total from acid_burn_adult_female,acid_burn_adult_male,acid_burn_children_female,acid_burn_children_male,acid_burn_transgender ) select * from acid_table """
    certificate_data = __db_fetch_values_dict(query)

    data = json.dumps({
        'certificate_data': certificate_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def medical_injuries_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/medical_injuries_report.html', {'divisions': divisions})


@csrf_exempt
def get_medical_injuries_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS( SELECT (json->>'burn_percent')::float burn_percent, (json->>'victim_id')::text victim_id, ( SELECT sex FROM asf_victim WHERE victim_id = (json->>'victim_id') limit 1), ( SELECT victim_age FROM asf_victim WHERE victim_id = (json->>'victim_id') limit 1) FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'description_injuries') AND ( json->>'victim_id') = ANY ( SELECT victim_id FROM asf_victim WHERE current_division LIKE '""" + str(
        division) + """' AND current_district LIKE '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) AND date_created::date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS ( SELECT 'Female'::text AS categories, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent < 5 AND sex = 'Female' AND victim_age::int >= 18) AS minor, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent BETWEEN 5 AND 10 AND sex = 'Female' AND victim_age::int >= 18) AS medium, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent > 10 AND sex = 'Female' AND victim_age::int >= 18) AS major UNION ALL SELECT 'Male'::text AS categories, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent < 5 AND sex = 'Male' AND victim_age::int >= 18) AS minor, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent BETWEEN 5 AND 10 AND sex = 'Male' AND victim_age::int >= 18) AS medium, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent > 10 AND sex = 'Male' AND victim_age::int >= 18 ) AS major UNION ALL SELECT 'Female Children'::text AS categories, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent < 5 AND sex = 'Female' AND victim_age::int < 18) AS minor, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent BETWEEN 5 AND 10 AND sex = 'Female' AND victim_age::int < 18) AS medium, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent > 10 AND sex = 'Female' AND victim_age::int < 18 ) AS major UNION ALL SELECT 'Male Children'::text AS categories, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent < 5 AND sex = 'Male' AND victim_age::int < 18) AS minor, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent BETWEEN 5 AND 10 AND sex = 'Male' AND victim_age::int < 18) AS medium, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent > 10 AND sex = 'Male' AND victim_age::int < 18 ) AS major UNION ALL SELECT 'Transgender'::text AS categories, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent < 5 AND sex = 'Transgender') AS minor, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent BETWEEN 5 AND 10 AND sex = 'Transgender' ) AS medium, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE burn_percent > 10 AND sex = 'Transgender' ) AS major ) SELECT * FROM t UNION ALL SELECT 'Total'::text AS categories, sum(minor) minor, sum(medium) medium, sum( major) major FROM t """
    certificate_data = __db_fetch_values_dict(query)

    data = json.dumps({
        'certificate_data': certificate_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def medical_operations_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/medical_operations_report.html', {'divisions': divisions})


@csrf_exempt
def get_medical_operations_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ with legal_form as( select (json->>'victim_id')::text victim_id,(select sex from asf_victim where victim_id = (json->>'victim_id') limit 1),(select victim_age from asf_victim where victim_id = (json->>'victim_id') limit 1) from logger_instance where xform_id =(select id from logger_xform where id_string = 'surgery') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """'), t as ( SELECT 'Female'::text AS categories, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int >= 18) as minor, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int >= 18) as medium, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int >= 18 ) as major union all SELECT 'Male'::text AS categories, (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int >= 18) as minor, (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int >= 18) as medium, (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int >= 18 ) as major union all SELECT 'Female Children'::text AS categories, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int < 18) as minor, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int < 18) as medium, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int < 18 ) as major union all SELECT 'Male Children'::text AS categories, (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int < 18) as minor, (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int < 18) as medium, (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int < 18 ) as major union all SELECT 'Transgender'::text AS categories, (select count(distinct victim_id) from legal_form where sex = 'Transgender') as minor, (select count(distinct victim_id) from legal_form where sex = 'Transgender' ) as medium, (select count(distinct victim_id) from legal_form where sex = 'Transgender' ) as major )select *,minor+medium+major as total from t union all SELECT 'Total'::text AS categories, sum(minor) minor, sum(medium) medium, sum( major) major,sum(minor)+sum(medium)+sum( major) from t """
    operations_data = __db_fetch_values_dict(query)

    qry = """ WITH asf_tbl AS(SELECT * FROM asf_case WHERE status = 'Valid' AND division LIKE '""" + str(
        division) + """' AND district LIKE '""" + str(district) + """' AND upazila LIKE '""" + str(
        upazila) + """'), get_victim_id1 AS (SELECT DISTINCT json ->> 'victim_id' victim_id FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'surgery') AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), get_victim_id as( select victim_id from get_victim_id1 group by victim_id having count(victim_id) = 1), acid_burn_adult_female AS (SELECT 'Acid Burn' :: text AS "type", Count(*) female_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT >= 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_adult_male AS (SELECT 'Acid Burn' :: text AS "type", Count(*) male_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT >= 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_children_female AS (SELECT 'Acid Burn' :: text AS "type", Count(*) female_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT < 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_children_male AS (SELECT 'Acid Burn' :: text AS "type", Count(*) male_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT < 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_transgender AS (SELECT 'Acid Burn' :: text AS "type", Count(*) transgender FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND sex = 'Transgender' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_adult_female AS (SELECT 'Others' :: text AS "type", Count(*) female_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT >= 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_adult_male AS (SELECT 'Others' :: text AS "type", Count(*) male_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT >= 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_children_female AS (SELECT 'Others' :: text AS "type", Count(*) female_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT < 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_children_male AS (SELECT 'Others' :: text AS "type", Count(*) male_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT < 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_transgender AS (SELECT 'Others' :: text AS "type", Count(*) transgender FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND sex = 'Transgender' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_table AS (SELECT acid_burn_adult_female."type", female_adult, male_adult, female_children, male_children, transgender, female_adult + male_adult + female_children + male_children + transgender AS total FROM acid_burn_adult_female, acid_burn_adult_male, acid_burn_children_female, acid_burn_children_male, acid_burn_transgender), others_table AS (SELECT other_burn_adult_female."type", female_adult, male_adult, female_children, male_children, transgender, female_adult + male_adult + female_children + male_children + transgender AS total FROM other_burn_adult_female, other_burn_adult_male, other_burn_children_female, other_burn_children_male, other_burn_transgender) SELECT * FROM acid_table UNION ALL SELECT * FROM others_table UNION ALL SELECT 'Total' :: text AS "type", acid_table.female_adult + others_table.female_adult, acid_table.male_adult + others_table.male_adult, acid_table.female_children + others_table.female_children, acid_table.male_children + others_table.male_children, acid_table.transgender + others_table.transgender, acid_table.total + others_table.total FROM acid_table, others_table """
    new_patient_data = __db_fetch_values_dict(qry)

    qry = """ WITH asf_tbl AS(SELECT * FROM asf_case WHERE status = 'Valid' AND division LIKE '""" + str(
        division) + """' AND district LIKE '""" + str(district) + """' AND upazila LIKE '""" + str(
        upazila) + """'), get_victim_id1 AS (SELECT DISTINCT json ->> 'victim_id' victim_id FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'surgery') AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), get_victim_id as( select victim_id from get_victim_id1 group by victim_id having count(victim_id) > 1), acid_burn_adult_female AS (SELECT 'Acid Burn' :: text AS "type", Count(*) female_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT >= 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_adult_male AS (SELECT 'Acid Burn' :: text AS "type", Count(*) male_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT >= 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_children_female AS (SELECT 'Acid Burn' :: text AS "type", Count(*) female_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT < 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_children_male AS (SELECT 'Acid Burn' :: text AS "type", Count(*) male_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND victim_age :: INT < 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_burn_transgender AS (SELECT 'Acid Burn' :: text AS "type", Count(*) transgender FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = 'Chemical(Acid/Alkali)' ) AND sex = 'Transgender' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_adult_female AS (SELECT 'Others' :: text AS "type", Count(*) female_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT >= 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_adult_male AS (SELECT 'Others' :: text AS "type", Count(*) male_adult FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT >= 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_children_female AS (SELECT 'Others' :: text AS "type", Count(*) female_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT < 18 AND sex = 'Female' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_children_male AS (SELECT 'Others' :: text AS "type", Count(*) male_children FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND victim_age :: INT < 18 AND sex = 'Male' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), other_burn_transgender AS (SELECT 'Others' :: text AS "type", Count(*) transgender FROM asf_victim WHERE case_id :: INT = ANY (SELECT id FROM asf_tbl WHERE burn_type = ANY ( array['Others', 'Flame'] )) AND sex = 'Transgender' AND victim_id = ANY (SELECT victim_id FROM get_victim_id)), acid_table AS (SELECT acid_burn_adult_female."type", female_adult, male_adult, female_children, male_children, transgender, female_adult + male_adult + female_children + male_children + transgender AS total FROM acid_burn_adult_female, acid_burn_adult_male, acid_burn_children_female, acid_burn_children_male, acid_burn_transgender), others_table AS (SELECT other_burn_adult_female."type", female_adult, male_adult, female_children, male_children, transgender, female_adult + male_adult + female_children + male_children + transgender AS total FROM other_burn_adult_female, other_burn_adult_male, other_burn_children_female, other_burn_children_male, other_burn_transgender) SELECT * FROM acid_table UNION ALL SELECT * FROM others_table UNION ALL SELECT 'Total' :: text AS "type", acid_table.female_adult + others_table.female_adult, acid_table.male_adult + others_table.male_adult, acid_table.female_children + others_table.female_children, acid_table.male_children + others_table.male_children, acid_table.transgender + others_table.transgender, acid_table.total + others_table.total FROM acid_table, others_table """
    old_patient_data = __db_fetch_values_dict(qry)

    qry = """ WITH asf_tbl AS(SELECT * FROM asf_case WHERE status = 'Valid' AND division LIKE '""" + str(
        division) + """' AND district LIKE '""" + str(district) + """' AND upazila LIKE '""" + str(
        upazila) + """'), get_victim_id AS (SELECT json ->> 'victim_id' victim_id ,json->>'number_of_procedure' number_of_procedure FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'surgery') AND date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """' )select count(*) total_operation, count(distinct victim_id) total_patients,sum(number_of_procedure::int) total_procedure from get_victim_id """
    total_data = __db_fetch_values_dict(qry)

    data = json.dumps({
        'operations_data': operations_data,
        'new_patient_data': new_patient_data,
        'old_patient_data': old_patient_data,
        'total_data': total_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def legal_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/legal_report.html', {'divisions': divisions})


@csrf_exempt
def get_legal_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')

    query = """ with tiles1 as( select count(*) lag_cnt from logger_instance where xform_id = (select id from logger_xform where id_string = 'legal_support_case_status') and (json->>'case_handed_over')::int = 1 and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """'),tiles2 as ( select count(*) other_lag_cnt from logger_instance where xform_id = (select id from logger_xform where id_string = 'legal_support_case_status') and (json->>'case_handed_over')::int = 2 and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """') and date_created::date between '""" + str(from_date) + """' and '""" + str(
        to_date) + """' )select * from tiles1,tiles2 """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    lag_tiles_cnt = df.lag_cnt.tolist()[0]
    other_lag_tiles_cnt = df.other_lag_cnt.tolist()[0]
    print(query)

    qry = """ with legal_form as( select json->>'has_case_filed' has_case_filed from logger_instance where xform_id = (select id from logger_xform where id_string = 'legal_support_case_status') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """'), total_tbl as ( select count(*) total from legal_form ),t1 as ( SELECT 'Yes' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where has_case_filed::int = 1 GROUP BY total union all SELECT 'No' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where has_case_filed::int = 0 GROUP BY total ),tt AS ( SELECT 'Yes' AS categories UNION ALL SELECT 'No' AS categories )SELECT tt.categories categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.categories = t1.categories """
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    case_filed_pie_data = {}
    case_filed_categories = df.categories.tolist()
    case_filed_percentage = df.percentage.tolist()
    case_filed_cnt = df.cnt.tolist()
    # color = ['#0B336C','#0AAECE','#3A89C3','#0069b7','#08C4BB','#9999ff']
    case_filed_pie_data = []
    for n, y, count in zip(case_filed_categories, case_filed_percentage, case_filed_cnt):
        case_filed_pie_data.append(
            {
                'name': str(n),
                'y': y,
                'count': count
            }
        )

    qry = """ with legal_form as( select json->>'case_filed_in' case_filed_in from logger_instance where xform_id = (select id from logger_xform where id_string = 'legal_support_case_status') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """' and (json->>'case_filed_in')::text is not null), total_tbl as ( select count(*) total from legal_form ),t1 as ( SELECT 'Thana' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_filed_in::int = 1 GROUP BY total union all SELECT 'Court' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_filed_in::int = 2 GROUP BY total ),tt AS ( SELECT 'Thana' AS categories UNION ALL SELECT 'Court' AS categories )SELECT tt.categories categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.categories = t1.categories """
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    case_filed_in_pie_data = {}
    case_filed_in_categories = df.categories.tolist()
    case_filed_in_percentage = df.percentage.tolist()
    case_filed_in_cnt = df.cnt.tolist()
    # color = ['#0B336C','#0AAECE','#3A89C3','#0069b7','#08C4BB','#9999ff']
    case_filed_in_pie_data = []
    for n, y, count in zip(case_filed_in_categories, case_filed_in_percentage, case_filed_in_cnt):
        case_filed_in_pie_data.append(
            {
                'name': str(n),
                'y': y,
                'count': count
            }
        )
    print(case_filed_in_pie_data)

    qry = """with legal_form as( select json->>'case_stage_status' case_stage_status from logger_instance where xform_id = (select id from logger_xform where id_string = 'legal_support_case_status') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """' and (json->>'case_stage_status')::text is not null), total_tbl as ( select count(*) total from legal_form ),t1 as ( SELECT 'Investigation' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_stage_status::int = 1 GROUP BY total union all SELECT 'Trial Stage' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_stage_status::int = 2 GROUP BY total union all SELECT 'Discharge' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_stage_status::int = 3 GROUP BY total union all SELECT 'Acquittal' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_stage_status::int = 4 GROUP BY total union all SELECT 'Conviction' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_stage_status::int = 5 GROUP BY total union all SELECT 'Compromised' AS categories, Count(*) cnt, Round(Count(*)*100/total)::int percentage FROM total_tbl, legal_form where case_stage_status::int = 6 GROUP BY total ),tt AS ( SELECT 'Investigation' AS categories UNION ALL SELECT 'Trial Stage' AS categories UNION ALL SELECT 'Discharge' AS categories UNION ALL SELECT 'Acquittal' AS categories UNION ALL SELECT 'Conviction' AS categories UNION ALL SELECT 'Compromised' AS categories )SELECT tt.categories categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.categories = t1.categories"""
    stage_wise_data = __db_fetch_values_dict(qry)

    data = json.dumps({
        'lag_tiles_cnt': lag_tiles_cnt,
        'other_lag_tiles_cnt': other_lag_tiles_cnt,
        'case_filed_pie_data': case_filed_pie_data,
        'case_filed_in_pie_data': case_filed_in_pie_data,
        'stage_wise_data': stage_wise_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def rehab_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/rehab_report.html', {'divisions': divisions})


@csrf_exempt
def get_rehab_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')

    query = """ WITH tiles1 AS(SELECT Count(*) rehab_cnt FROM logger_instance WHERE xform_id = any(SELECT id FROM logger_xform WHERE id_string =any(array['case_followup_status','economical_support','case_conference'])) AND ( json ->> 'victim_id' ) = ANY (SELECT victim_id FROM asf_victim WHERE current_division LIKE '""" + str(
        division) + """' AND current_district LIKE '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid'))  AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), tiles2 AS (SELECT Count(*) followup_cnt FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'case_followup_status') AND ( json ->> 'followup_issue' ) :: INT = 1 AND ( json ->> 'victim_id' ) = ANY (SELECT victim_id FROM asf_victim WHERE current_division LIKE '""" + str(
        division) + """' AND current_district LIKE '""" + str(
        district) + """') AND date_created :: DATE BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """'), tiles3 as ( SELECT Count(*) economic_cnt FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'economical_support') AND ( json ->> 'victim_id' ) = ANY (SELECT victim_id FROM asf_victim WHERE current_division LIKE '""" + str(
        division) + """' AND current_district LIKE '""" + str(
        district) + """') AND date_created :: DATE BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """' ) SELECT * FROM tiles1, tiles2,tiles3 """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    rehab_tiles_cnt = df.rehab_cnt.tolist()[0]
    followup_tiles_cnt = df.followup_cnt.tolist()[0]
    economic_tiles_cnt = df.economic_cnt.tolist()[0]
    print(query)

    qry = """ with legal_form as( select sum((json->>'particiapnt_total')::int) total,sum((json->>'participant_girl')::int) total_girl, sum((json->>'participant_male')::int) total_male, sum((json->>'participant_female')::int) totaL_female, sum((json->>'participant_boy')::int) total_boy, sum((json->>'participant_trangender')::int) total_transgender from logger_instance where xform_id =(select id from logger_xform where id_string = 'capacity_building') and (json->>'division') like '""" + str(
        division) + """' and (json->>'district') like '""" + str(
        district) + """' and date_created::date between '""" + str(from_date) + """' and '""" + str(
        to_date) + """'),t1 as ( SELECT 'Male' AS categories, total_male cnt, Round(total_male*100/total)::int percentage FROM legal_form union all SELECT 'Female' AS categories, total_female cnt, Round(total_female*100/total)::int percentage FROM legal_form union all SELECT 'Girls' AS categories, total_girl cnt, Round(total_girl*100/total)::int percentage FROM legal_form union all SELECT 'Boys' AS categories, total_boy cnt, Round(total_boy*100/total)::int percentage FROM legal_form union all SELECT 'Transgender' AS categories, total_transgender cnt, Round(total_transgender*100/total)::int percentage FROM legal_form ) ,tt AS ( SELECT 'Male' AS categories UNION ALL SELECT 'Female' AS categories UNION ALL SELECT 'Girls' AS categories UNION ALL SELECT 'Boys' AS categories UNION ALL SELECT 'Transgender' AS categories )SELECT tt.categories categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.categories = t1.categories """
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    capacity_building_participant_pie_data = {}
    capacity_building_participant_categories = df.categories.tolist()
    capacity_building_participant_percentage = df.percentage.tolist()
    capacity_building_participant_cnt = df.cnt.tolist()
    # color = ['#0B336C','#0AAECE','#3A89C3','#0069b7','#08C4BB','#9999ff']
    capacity_building_participant_pie_data = []
    for n, y, count in zip(capacity_building_participant_categories, capacity_building_participant_percentage,
                           capacity_building_participant_cnt):
        capacity_building_participant_pie_data.append(
            {
                'name': str(n),
                'y': y,
                'count': count
            }
        )

    qry = """ with legal_form as( select (json->>'capacity_building_subject') capacity_building_subject from logger_instance where xform_id =(select id from logger_xform where id_string = 'capacity_building') and (json->>'division') like '""" + str(
        division) + """' and (json->>'district') like '""" + str(
        district) + """' and date_created::date between '""" + str(from_date) + """' and '""" + str(
        to_date) + """' and (json->>'capacity_building_subject') is not null),total_cnt as ( select count(*) total from legal_form ),t1 as ( SELECT 'Life skills / Social Skills' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form,total_cnt where capacity_building_subject::int = 1 group by total union all SELECT 'Gender Issues' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 2 group by total union all SELECT 'Legal Issues' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 3 group by total union all SELECT 'Skill based training' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 4 group by total union all SELECT 'Survivor''r rights' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 5 group by total union all SELECT 'Burn Care Training' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 6 group by total union all SELECT 'Mental health' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 7 group by total union all SELECT 'Organization Development' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 8 group by total union all SELECT 'HR management' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 9 group by total union all SELECT 'Others' AS categories, count(*) cnt, Round(count(*)*100/total)::int percentage FROM legal_form, total_cnt where capacity_building_subject::int = 99 group by total ) ,tt AS ( SELECT 'Life skills / Social Skills' AS categories UNION ALL SELECT 'Gender Issues' AS categories UNION ALL SELECT 'Legal Issues' AS categories UNION ALL SELECT 'Skill based training' AS categories UNION ALL SELECT 'Survivor''r rights' AS categories UNION ALL SELECT 'Burn Care Training' AS categories UNION ALL SELECT 'Mental health' AS categories UNION ALL SELECT 'Organization Development' AS categories UNION ALL SELECT 'HR management' AS categories UNION ALL SELECT 'Others' AS categories )SELECT tt.categories categories, COALESCE(cnt,0) cnt, COALESCE(percentage,0) percentage FROM tt LEFT JOIN t1 ON tt.categories = t1.categories order by percentage desc """
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    name = df.categories.tolist()
    data = df.percentage.tolist()
    cnt = df.cnt.tolist()
    # capacity_building_participant_cnt

    data = json.dumps({
        'rehab_tiles_cnt': rehab_tiles_cnt,
        'followup_tiles_cnt': followup_tiles_cnt,
        'economic_tiles_cnt': economic_tiles_cnt,
        'capacity_building_participant_pie_data': capacity_building_participant_pie_data,
        'name': name,
        'data': data,
        'cnt': cnt
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def physiotherapy_patient_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/physiotherapy_patient_report.html', {'divisions': divisions})


@csrf_exempt
def get_physiotherapy_patient_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ with legal_form as( select (json->>'victim_id')::text victim_id ,json->>'procedure' mprocedure,json->>'seassion' seassion,(select sex from asf_victim where victim_id = (json->>'victim_id') limit 1),(select victim_age from asf_victim where victim_id = (json->>'victim_id') limit 1) from logger_instance where xform_id =(select id from logger_xform where id_string = 'physiotherapy_ongoing_support') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """' and (json->>'service_point')::int = 1), t as ( select (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int >= 18 ) male, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int >= 18 ) female, (select count(distinct victim_id) from legal_form where victim_age::int < 18 ) child, sum(mprocedure::int) total_procedure ,sum(seassion::int) total_session from legal_form ) select male+female+child total_patient,* from t """
    ipd_data = __db_fetch_values_dict(query)
    query = """ with legal_form as( select (json->>'victim_id')::text victim_id ,json->>'procedure' mprocedure,json->>'seassion' seassion,(select sex from asf_victim where victim_id = (json->>'victim_id') limit 1),(select victim_age from asf_victim where victim_id = (json->>'victim_id') limit 1) from logger_instance where xform_id =(select id from logger_xform where id_string = 'physiotherapy_ongoing_support') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """' and (json->>'service_point')::int = 2), t as ( select (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int >= 18 ) male, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int >= 18 ) female, (select count(distinct victim_id) from legal_form where victim_age::int < 18 ) child, sum(mprocedure::int) total_procedure ,sum(seassion::int) total_session from legal_form ) select male+female+child total_patient,* from t """
    opd_data = __db_fetch_values_dict(query)

    query = """ with legal_form as( select (json->>'victim_id')::text victim_id ,json->>'procedure' mprocedure,json->>'seassion' seassion,(select sex from asf_victim where victim_id = (json->>'victim_id') limit 1),(select victim_age from asf_victim where victim_id = (json->>'victim_id') limit 1) from logger_instance where xform_id =(select id from logger_xform where id_string = 'physiotherapy_ongoing_support') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """' ), t as ( select (select count(distinct victim_id) from legal_form where sex = 'Male' and victim_age::int >= 18 ) male, (select count(distinct victim_id) from legal_form where sex = 'Female' and victim_age::int >= 18 ) female, (select count(distinct victim_id) from legal_form where victim_age::int < 18 ) child, sum(mprocedure::int) total_procedure ,sum(seassion::int) total_session from legal_form ) select male+female+child total_patient,* from t """
    total_data = __db_fetch_values_dict(query)

    data = json.dumps({
        'ipd_data': ipd_data,
        'opd_data': opd_data,
        'total_data': total_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def physiotherapy_govt_hospital_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/physiotherapy_govt_hospital_report.html', {'divisions': divisions})


@csrf_exempt
def get_physiotherapy_govt_hospital_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ with legal_form as( select json->>'hospital' hospital,json->>'adult_female' adult_female, json->>'adult_male' adult_male, json->>'child_male' child_male, json->>'child_female' child_female,json->>'trangender' trangender ,json->>'session_adult_female' session_adult_female ,json->>'session_adult_male' session_adult_male ,json->>'session_child_female' session_child_female ,json->>'session_child_male' session_child_male ,json->>'session_trangender' session_trangender ,json->>'procedure' mprocedures from logger_instance where xform_id =(select id from logger_xform where id_string = 'services_other_institute') and (json->>'service' = '1') and (json->>'organization') = '1' and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """'), t as ( select case when hospital = '1' then 'SHNIBPS' when hospital = '2' then 'DMCH' when hospital = '3' then 'ShSMCH' when hospital = '4' then 'SSMC' when hospital = '5' then 'MMCH' when hospital = '6' then 'KMCH' when hospital = '7' then 'CMCH' when hospital = '8' then 'CuMCH' when hospital = '9' then 'VSC' end hospital,coalesce(sum(adult_male::int),0) male, coalesce(sum(adult_female::int),0) female, coalesce(sum(child_male::int)+sum(child_female::int),0) child, coalesce(sum(session_adult_female::int)+sum(session_adult_male::int) +sum(session_child_female::int)+sum(session_child_male::int)+sum(session_trangender::int),0) total_session ,coalesce(sum(mprocedures::int),0) total_procedure from legal_form group by hospital ) select male+female+child total_patient,* from t """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def physiotherapy_eclinic_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/physiotherapy_eclinic_report.html', {'divisions': divisions})


@csrf_exempt
def get_physiotherapy_eclinic_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS(SELECT json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_male' child_male, json ->> 'child_female' child_female, json ->> 'trangender' trangender, json ->> 'session_adult_female' session_adult_female, json ->> 'session_adult_male' session_adult_male, json ->> 'session_child_female' session_child_female, json ->> 'session_child_male' session_child_male, json ->> 'session_trangender' session_trangender, json ->> 'procedure' mprocedures FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute') and (json->>'service' = '1') AND ( json ->> 'organization') = '2' AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS (SELECT Coalesce(SUM(adult_male :: INT), 0) male, Coalesce(SUM(adult_female :: INT), 0) female, Coalesce(SUM(child_male::INT) + SUM(child_female::INT), 0) child, Coalesce(SUM(session_adult_female::INT) + SUM(session_adult_male::INT) + SUM(session_child_female::INT) + SUM(session_child_male::INT) + SUM(session_trangender::INT), 0) total_session, Coalesce(SUM(mprocedures :: INT), 0) total_procedure FROM legal_form ) SELECT male + female + child total_patient, * FROM t  """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def physiotherapy_outreach_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/physiotherapy_outreach_report.html', {'divisions': divisions})


@csrf_exempt
def get_physiotherapy_outreach_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS(SELECT json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_male' child_male, json ->> 'child_female' child_female, json ->> 'trangender' trangender, json ->> 'session_adult_female' session_adult_female, json ->> 'session_adult_male' session_adult_male, json ->> 'session_child_female' session_child_female, json ->> 'session_child_male' session_child_male, json ->> 'session_trangender' session_trangender, json ->> 'procedure' mprocedures FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute') and (json->>'service' = '1') AND ( json ->> 'organization') = '3' AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS (SELECT Coalesce(SUM(adult_male :: INT), 0) male, Coalesce(SUM(adult_female :: INT), 0) female, Coalesce(SUM(child_male::INT) + SUM(child_female::INT), 0) child, Coalesce(SUM(session_adult_female::INT) + SUM(session_adult_male::INT) + SUM(session_child_female::INT) + SUM(session_child_male::INT) + SUM(session_trangender::INT), 0) total_session, Coalesce(SUM(mprocedures :: INT), 0) total_procedure FROM legal_form ) SELECT male + female + child total_patient, * FROM t  """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def physiotherapy_community_clinic_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/physiotherapy_community_clinic_report.html', {'divisions': divisions})


@csrf_exempt
def get_physiotherapy_community_clinic_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS(SELECT json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_male' child_male, json ->> 'child_female' child_female, json ->> 'trangender' trangender, json ->> 'session_adult_female' session_adult_female, json ->> 'session_adult_male' session_adult_male, json ->> 'session_child_female' session_child_female, json ->> 'session_child_male' session_child_male, json ->> 'session_trangender' session_trangender, json ->> 'procedure' mprocedures FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute') and (json->>'service' = '1') AND ( json ->> 'organization') = '4' AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS (SELECT Coalesce(SUM(adult_male :: INT), 0) male, Coalesce(SUM(adult_female :: INT), 0) female, Coalesce(SUM(child_male::INT) + SUM(child_female::INT), 0) child, Coalesce(SUM(session_adult_female::INT) + SUM(session_adult_male::INT) + SUM(session_child_female::INT) + SUM(session_child_male::INT) + SUM(session_trangender::INT), 0) total_session, Coalesce(SUM(mprocedures :: INT), 0) total_procedure FROM legal_form ) SELECT male + female + child total_patient, * FROM t  """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def physiotherapy_pressure_garment_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/physiotherapy_pressure_garment_report.html', {'divisions': divisions})


@csrf_exempt
def get_medical_pressure_garment_report(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS( SELECT json->>'victim_id' victim_id, ( SELECT sex FROM asf_victim WHERE victim_id = (json->>'victim_id') limit 1), json ->> 'quantity' quantity FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'pressure_garments_splint') AND ( json ->> 'support_type') = '1' AND ( json->>'victim_id') = ANY ( SELECT victim_id FROM asf_victim WHERE current_division LIKE '""" + str(
        division) + """' AND current_district LIKE '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) AND date_created :: date BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' ), tbl AS ( SELECT ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE sex = 'Male') male, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE sex = 'Female') female, ( SELECT count(DISTINCT victim_id) FROM legal_form WHERE sex = 'Child') child, ( SELECT count(quantity) FROM legal_form) quantity ) SELECT male+female+child total_patient, * FROM tbl """
    new_patient_data = __db_fetch_values_dict(query)
    query = """ WITH legal_form AS( SELECT json->>'victim_id' victim_id,json ->> 'quantity' quantity,json->>'amount' amount FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'pressure_garments_splint') AND ( json ->> 'support_type') = '2' and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(
        district) + """' and case_id::int = any(select id from asf_case where status = 'Valid')) AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """' ) select (select count(distinct victim_id) from legal_form) total_patient ,(select coalesce(sum(quantity::int),0) from legal_form) quantity, (select coalesce(sum(amount::float),0) from legal_form) amount """
    old_patient_data = __db_fetch_values_dict(query)

    data = json.dumps({
        'new_patient_data': new_patient_data,
        'old_patient_data': old_patient_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def psychotherapy_govt_hospital_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/psychotherapy_govt_hospital_report.html', {'divisions': divisions})


@csrf_exempt
def get_psychotherapy_govt_hospital_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ with legal_form as( select json->>'hospital' hospital,json->>'adult_female' adult_female, json->>'adult_male' adult_male, json->>'child_male' child_male, json->>'child_female' child_female,json->>'trangender' trangender ,json->>'session_adult_female' session_adult_female ,json->>'session_adult_male' session_adult_male ,json->>'session_child_female' session_child_female ,json->>'session_child_male' session_child_male ,json->>'session_trangender' session_trangender ,json->>'procedure' mprocedures from logger_instance where xform_id =(select id from logger_xform where id_string = 'services_other_institute') and (json->>'service' = '2') and (json->>'organization') = '1' and date_created::date between '""" + str(
        from_date) + """' and '""" + str(
        to_date) + """'), t as ( select case when hospital = '1' then 'SHNIBPS' when hospital = '2' then 'DMCH' when hospital = '3' then 'ShSMCH' when hospital = '4' then 'SSMC' when hospital = '5' then 'MMCH' when hospital = '6' then 'KMCH' when hospital = '7' then 'CMCH' when hospital = '8' then 'CuMCH' when hospital = '9' then 'VSC' end hospital,coalesce(sum(adult_male::int),0) male, coalesce(sum(adult_female::int),0) female, coalesce(sum(child_male::int)+sum(child_female::int),0) child, coalesce(sum(session_adult_female::int)+sum(session_adult_male::int) +sum(session_child_female::int)+sum(session_child_male::int)+sum(session_trangender::int),0) total_session ,coalesce(sum(mprocedures::int),0) total_procedure from legal_form group by hospital ) select male+female+child total_patient,* from t """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def psychotherapy_eclinic_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/psychotherapy_eclinic_report.html', {'divisions': divisions})


@csrf_exempt
def get_psychotherapy_eclinic_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS(SELECT json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_male' child_male, json ->> 'child_female' child_female, json ->> 'trangender' trangender, json ->> 'session_adult_female' session_adult_female, json ->> 'session_adult_male' session_adult_male, json ->> 'session_child_female' session_child_female, json ->> 'session_child_male' session_child_male, json ->> 'session_trangender' session_trangender, json ->> 'procedure' mprocedures FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute') and (json->>'service' = '2') AND ( json ->> 'organization') = '2' AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS (SELECT Coalesce(SUM(adult_male :: INT), 0) male, Coalesce(SUM(adult_female :: INT), 0) female, Coalesce(SUM(child_male::INT) + SUM(child_female::INT), 0) child, Coalesce(SUM(session_adult_female::INT) + SUM(session_adult_male::INT) + SUM(session_child_female::INT) + SUM(session_child_male::INT) + SUM(session_trangender::INT), 0) total_session, Coalesce(SUM(mprocedures :: INT), 0) total_procedure FROM legal_form ) SELECT male + female + child total_patient, * FROM t  """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def psychotherapy_outreach_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/psychotherapy_outreach_report.html', {'divisions': divisions})


@csrf_exempt
def get_psychotherapy_outreach_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS(SELECT json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_male' child_male, json ->> 'child_female' child_female, json ->> 'trangender' trangender, json ->> 'session_adult_female' session_adult_female, json ->> 'session_adult_male' session_adult_male, json ->> 'session_child_female' session_child_female, json ->> 'session_child_male' session_child_male, json ->> 'session_trangender' session_trangender, json ->> 'procedure' mprocedures FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute') and (json->>'service' = '2') AND ( json ->> 'organization') = '3' AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS (SELECT Coalesce(SUM(adult_male :: INT), 0) male, Coalesce(SUM(adult_female :: INT), 0) female, Coalesce(SUM(child_male::INT) + SUM(child_female::INT), 0) child, Coalesce(SUM(session_adult_female::INT) + SUM(session_adult_male::INT) + SUM(session_child_female::INT) + SUM(session_child_male::INT) + SUM(session_trangender::INT), 0) total_session, Coalesce(SUM(mprocedures :: INT), 0) total_procedure FROM legal_form ) SELECT male + female + child total_patient, * FROM t  """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def psychotherapy_community_clinic_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/psychotherapy_community_clinic_report.html', {'divisions': divisions})


@csrf_exempt
def get_psychotherapy_community_clinic_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    query = """ WITH legal_form AS(SELECT json ->> 'adult_female' adult_female, json ->> 'adult_male' adult_male, json ->> 'child_male' child_male, json ->> 'child_female' child_female, json ->> 'trangender' trangender, json ->> 'session_adult_female' session_adult_female, json ->> 'session_adult_male' session_adult_male, json ->> 'session_child_female' session_child_female, json ->> 'session_child_male' session_child_male, json ->> 'session_trangender' session_trangender, json ->> 'procedure' mprocedures FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'services_other_institute') and (json->>'service' = '2') AND ( json ->> 'organization') = '4' AND date_created :: DATE BETWEEN '""" + str(
        from_date) + """' AND '""" + str(
        to_date) + """'), t AS (SELECT Coalesce(SUM(adult_male :: INT), 0) male, Coalesce(SUM(adult_female :: INT), 0) female, Coalesce(SUM(child_male::INT) + SUM(child_female::INT), 0) child, Coalesce(SUM(session_adult_female::INT) + SUM(session_adult_male::INT) + SUM(session_child_female::INT) + SUM(session_child_male::INT) + SUM(session_trangender::INT), 0) total_session, Coalesce(SUM(mprocedures :: INT), 0) total_procedure FROM legal_form ) SELECT male + female + child total_patient, * FROM t  """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


@login_required
def psychotherapy_patient_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    return render(request, 'asfmodule/psychotherapy_patient_report.html', {'divisions': divisions})


@csrf_exempt
def get_psychotherapy_patient_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    query = """ with main_tbl as( SELECT json->>'victim_id' victim_id,unnest(string_to_array((json->>'services')::text, ' ')) services FROM logger_instance WHERE xform_id = (SELECT id FROM logger_xform WHERE id_string = 'psychological_services') and (json->>'victim_id') = any (select victim_id from asf_victim where current_division like '""" + str(
        division) + """' and current_district like '""" + str(district) + """' and current_upazila like '""" + str(
        upazila) + """') AND date_created :: DATE BETWEEN '""" + str(from_date) + """' AND '""" + str(
        to_date) + """'),main_tbl1 as ( select distinct *,(select victim_age from asf_victim where victim_id = main_tbl.victim_id limit 1) ,(select sex from asf_victim where victim_id = main_tbl.victim_id limit 1) from main_tbl where services != '' ), female_tbl as (select services,count(victim_id) female from main_tbl1 where sex = 'Female' and victim_age::int >= 18 group by services), male_tbl as (select services,count(victim_id) male from main_tbl1 where sex = 'Male' and victim_age::int >= 18 group by services), female_cld_tbl as (select services,count(victim_id) female_child from main_tbl1 where sex = 'Female' and victim_age::int < 18 group by services), male_cld_tbl as (select services,count(victim_id) male_child from main_tbl1 where sex = 'Male' and victim_age::int < 18 group by services) ,all_serv_tbl as (select unnest(string_to_array('1,2,5,6,7,9,10,11,14,13,15,16,18,19',',')) services) , ss1 as ( select all_serv_tbl.services,coalesce(female,0) female from all_serv_tbl left join female_tbl on all_serv_tbl.services = female_tbl.services ), ss2 as( select ss1.services,female,coalesce(male,0) male from ss1 left join male_tbl on ss1.services = male_tbl.services ), ss3 as( select ss2.*,coalesce(female_child,0)female_child from ss2 left join female_cld_tbl on ss2.services = female_cld_tbl.services ),ss4 as ( select ss3.*,coalesce(male_child,0) male_child from ss3 left join male_cld_tbl on ss3.services = male_cld_tbl.services )select case when services = '1' then 'Art therapy' when services = '2' then 'Breathing' when services = '5' then 'Emotional Support' when services = '6' then 'Family Counseling/Therapy' when services = '7' then 'Group Counseling/Therapy' when services = '9' then 'Imaginary Relaxation' when services = '10' then 'Individual Counseling/Therapy' when services = '11' then 'Music therapy' when services = '14' then 'Pre - Operation Counseling' when services = '13' then 'Post - Operation Counseling' when services = '15' then 'Primary Psychosocial Assessment' when services = '16' then 'Progressive Muscular Relaxation' when services = '18' then 'Recreational Activity/Therapy' when services = '19' then 'Social Skill Training' end services,female,male,female_child,male_child,female+male+female_child+male_child total_patient from ss4 """
    print(query)
    govt_data = __db_fetch_values_dict(query)
    data = json.dumps({
        'govt_data': govt_data
    }, default=decimal_date_default)
    return HttpResponse(data)


#   Referral

@login_required
def referral_list(request):
    query = "select geocode as id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())

    return render(request, 'asfmodule/referral_list.html', {'divisions': divisions})


@csrf_exempt
def get_referral_list(request):
    division = request.POST.get('division')
    district = request.POST.get('district')
    upazila = request.POST.get('upazila')
    status = request.POST.get('status')
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = "with t as( select id from asf_victim where referral_followup_status like '" + str(
            status) + "' and case_id::int = any( select id from asf_case where division LIKE '" + str(
            division) + "' AND district LIKE '" + str(district) + "' AND upazila LIKE '" + str(
            upazila) + "' and upazila in ((select (SELECT geocode FROM geo_data WHERE id = geoid limit 1) from usermodule_catchment_area where user_id = " + str(
            user_id) + ") union (select geocode from geo_data where field_parent_id = any (select geoid from usermodule_catchment_area where user_id = " + str(
            user_id) + ") and field_type_id = 88))) )select instance_id::int id, victim_tbl_id, referral_organization_name referral_organization, beneficiary_id, coalesce (( select case when sex = '1' then 'Male' when sex = '2' then 'Female' end from asf_victim where id::text = victim_tbl_id limit 1),'') sex, coalesce (( select victim_name from asf_victim where id::text =victim_tbl_id limit 1), '') victim_name, coalesce (( select victim_age from asf_victim where id::text =victim_tbl_id limit 1), '') victim_age, coalesce (( select incident_id from asf_case where id = ( select case_id::int from asf_victim where id::text =victim_tbl_id ) limit 1), '') iom_case_no, date(referral_date) referral_date, referral_services from vw_iom_referral where victim_tbl_id = any(select id::text from t)"
    except Exception:
        query = "with t as( select id from asf_victim where referral_followup_status like '" + str(
            status) + "' and case_id::int = any( select id from asf_case where division LIKE '" + str(
            division) + "' AND district LIKE '" + str(district) + "' AND upazila LIKE '" + str(
            upazila) + "') )select instance_id::int id, victim_tbl_id, referral_organization_name referral_organization, beneficiary_id, coalesce (( select case when sex = '1' then 'Male' when sex = '2' then 'Female' end from asf_victim where id::text = victim_tbl_id limit 1),'') sex, coalesce (( select victim_name from asf_victim where id::text =victim_tbl_id limit 1), '') victim_name, coalesce (( select victim_age from asf_victim where id::text =victim_tbl_id limit 1), '') victim_age, coalesce (( select incident_id from asf_case where id = ( select case_id::int from asf_victim where id::text =victim_tbl_id ) limit 1), '') iom_case_no, date(referral_date) referral_date, referral_services from vw_iom_referral where victim_tbl_id = any(select id::text from t)"
    print query
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


#   Call Center

@login_required
def call_center_report(request):
    query = "select id,field_name from geo_data where field_type_id = 85"
    df = pandas.read_sql(query, connection)
    divisions = zip(df.id.tolist(), df.field_name.tolist())
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='call_center_support'")
    return render(request, 'asfmodule/call_center_report.html', {'divisions': divisions, 'form_id': form_id})


@csrf_exempt
def get_call_center_report(request):
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')

    q = "select ROW_NUMBER() OVER(ORDER BY id) AS serial_no,id,json->>'call_center/caller_id' caller_id, json->>'call_center/caller_name' caller_name,date((json->>'call_center/date_call_received')::TIMESTAMP ) date_call_received,json->>'call_center/caller_mobile' caller_mobile, json->>'call_center/caller_age' caller_age,json->>'call_center/calling_reason' calling_reason from vw_call_center_support where date(json->>'call_center/date_call_received') between '" + from_date + "' and '" + to_date + "'"
    main_df = pd.read_sql(q, connection)

    other_q = "select id, get_form_option_label(676,'call_center/call_from',json->>'call_center/call_from') call_from, get_form_option_label(676,'call_center/district',json->>'call_center/district') district, get_form_option_label(676,'call_center/reffered',json->>'call_center/reffered') reffered, get_form_option_label(676,'call_center/caller_gender',json->>'call_center/caller_gender') gender from vw_call_center_support where date(json->>'call_center/date_call_received') between '" + from_date + "' and '" + to_date + "'  order by id desc"
    other_df = pd.read_sql(other_q, connection)

    main_df = main_df.merge(other_df, on=['id'], how='left', )

    main_df = main_df.fillna('')
    data = main_df.to_dict('records')

    data = json.dumps(data, default=decimal_date_default)

    return HttpResponse(data)


def call_center_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    # server_address = '192.168.22.133:8001'
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='call_center_support'")
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/call_center_support_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'instance_id': instance_id})


# Consultancy Matrix

def consultancy_matrix(request):
    status_list = __db_fetch_values_dict("select status from cm_status")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='consultation_matrix'")

    # Status Update form

    if request.method == 'POST':

        data_id = request.POST.get('data_id')

        status = request.POST.get('status')

        status_dataset = __db_fetch_values_dict("select *  from cm_data_status where cm_id = " + str(data_id))

        if status_dataset:

            update_q = "update cm_data_status set status='" + status + "' where cm_id =  " + str(data_id)

            __db_commit_query(update_q)

        else:

            cursor = connection.cursor()

            cursor.execute(
                """INSERT INTO public.cm_data_status(cm_id, status)VALUES (%s, %s);""",
                (data_id, status))

        messages.success(request, '<i class="fa fa-check-circle"></i> Status updated successfully!',
                         extra_tags='alert-success crop-both-side')

    return render(request, 'asfmodule/consultancy_matrix.html', {'status_list': status_list, 'form_id': form_id})


@csrf_exempt
def get_consultancy_matrix(request):
    user_id = request.user.id
    q = "select COALESCE(( SELECT can_edit FROM vwrolewiseformpermission WHERE user_id = " + str(
        user_id) + " AND xform_id = ( SELECT id FROM logger_xform WHERE id_string='consultation_matrix') limit 1),0) can_edit, COALESCE( ( SELECT can_delete FROM vwrolewiseformpermission WHERE user_id = " + str(
        user_id) + " AND xform_id = ( SELECT id FROM logger_xform WHERE id_string='consultation_matrix') limit 1),0) can_delete, id ,contract_number,assigment_title,consultant_name,amount_grant,date(date_commissioned) date_commissioned,COALESCE (status,'Ongoing')status from vw_consultancy_matrix"
    main_df = pd.read_sql(q, connection)

    currency_q = "select  id,get_form_option_label(677,'currency',currency) currency from vw_consultancy_matrix"
    currency_df = pd.read_sql(currency_q, connection)

    main_df = main_df.merge(currency_df, on=['id'], how='left')
    main_df = main_df.fillna('')

    data = main_df.to_dict('records')

    data = json.dumps(data, default=decimal_date_default)
    return HttpResponse(data)


def consultancy_matrix_form(request):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    # server_address = '192.168.22.133:8001'
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='consultation_matrix'")
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/consultancy_matrix_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'instance_id': instance_id})


def get_consultation_matrix_profile(request, id):
    assignment_title = __db_fetch_single_value("select assigment_title from vw_consultancy_matrix where id =" + str(id))
    q = "select id ,contract_number,assigment_title,consultant_name,amount_grant,date(date_commissioned) date_commissioned,lead_consultant_name,posting_reference_number,commissioner from vw_consultancy_matrix where id =" + str(
        id)
    main_df = pd.read_sql(q, connection)

    currency_q = "select  id,get_form_option_label(677,'currency',currency) currency from vw_consultancy_matrix where id =" + str(
        id)
    currency_df = pd.read_sql(currency_q, connection)

    main_df = main_df.merge(currency_df, on=['id'], how='left')
    main_df = main_df.fillna('')
    data = main_df.to_dict('records')

    deliverable_q = "select * from vw_child_consultancy_matrix where id  = " + str(id)
    deliverable_data = __db_fetch_values_dict(deliverable_q)

    deliverable_data = json.dumps(deliverable_data)

    return render(request, 'asfmodule/consultation_matrix_profile.html',
                  {'assignment_title': assignment_title, 'profile': data, 'deliverable_data': deliverable_data})


@login_required
def xls_export_consultancy_matrix(request):
    query = """
            with t as (
        select id,date_created,lead_consultant_name,
        posting_reference_number,
        commissioner,
        date_commissioned,
        amount_grant,
        consultant_name,
        case when currency = '1' then 'BDT' when currency = '2' then 'USD' end currency,
        contract_number,
        assigment_title,
        coalesce(status,'Ongoing') status,
        json_array_elements(deliverable::json) deliverable from vw_consultancy_matrix vcm
        ), t1 as (select id,lead_consultant_name,date_created,
        posting_reference_number,
        commissioner,
        date_commissioned,
        amount_grant,
        consultant_name,
        currency,
        contract_number,
        assigment_title,status,
        deliverable->>'deliverable/r_position' r_position,
        to_char((deliverable->>'deliverable/date_submitted_by_consultant')::date,'DD-MON-YYYY') date_submitted_by_consultant,
        deliverable->>'deliverable/deliverable' deliverable,
        to_char((deliverable->>'deliverable/due_date')::date,'DD-MON-YY') due_date from t)
        select
        t1.contract_number "Contract Number",
        t1.posting_reference_number "Posting Ref #",
        t1.assigment_title "Assignment Title",
        t1.amount_grant "Amount of grant/procurement contract",
        t1.currency "Currency",
        t1.consultant_name "Consultant (s) Name(s)",
        t1.lead_consultant_name "Name of the Lead consultant",
        t1.commissioner "Commissioner",
        coalesce(to_char((t1.date_commissioned)::date,'DD-MON-YY'),'') "Date Commissioned",
        t1.deliverable "Deliverables (as in Contract)",
        t1.due_date "Due Date",
        coalesce(to_char((t1.date_submitted_by_consultant)::date,'DD-MON-YY'),'') "Date Submitted by Consultant",
        coalesce(cmd.policy_team_approval,'') "Policy Team",
        coalesce(cmd.reintegration_team_approval,'') "Reintegration Team",
        coalesce(cmd.m_e_team_approval,'') "M&E",
        coalesce(cmd.pm_approval,'') "PM",
        coalesce(to_char((cmd.returned_to_consultant)::date,'DD-MON-YY'),'') "Returned  to Consultant",
        coalesce(cmd.revised_report_received,'') "Revised Report received",
        case when cmd.checked_by_commissioner is null then 'No' else 'Yes' end  "Checked by Commisioner",
        coalesce(to_char((cmd.checked_by_commissioner)::date,'DD-MON-YY'),'') "Checked Date",
        coalesce(cmd.signed_off_by_pm,'') "Signed off by PM",
        coalesce(cmd.stakeholder_approval,'') "Stakeholder Approval (if required)",
        coalesce(cmd.final_document_submitted::text,'') "Final Document Submitted",
        coalesce(to_char((t1.date_created)::date,'DD-MON-YY'),'') "Date",
        coalesce(cmd.release_final_payment,'') "Release Final Payment",
        coalesce(cmd.performance_rating,'') "Performance Rating"
        from t1 left join  con_matrix_deliverable cmd on t1.id = cmd.data_id and t1.r_position::int = cmd.serial_no
    """
    df = pandas.read_sql(query, connection, index_col=['Contract Number', 'Posting Ref #', 'Assignment Title',
                                                       'Amount of grant/procurement contract', 'Currency',
                                                       'Consultant (s) Name(s)', 'Name of the Lead consultant',
                                                       'Commissioner', 'Date Commissioned',
                                                       'Deliverables (as in Contract)'])
    writer = pandas.ExcelWriter("onadata/media/uploaded_files/output.xlsx")
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    f = open('onadata/media/uploaded_files/output.xlsx', 'r')
    response = HttpResponse(f, mimetype='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Consultancy Matrix_' + str(date.today()) + '.xls'
    return response


@csrf_exempt
def get_deliverable(request):
    data_id = request.POST.get('data_id')
    serial_no = request.POST.get('serial_no')
    user_id = request.user.id
    # query from con_matrix_deliverable
    query = "select * from con_matrix_deliverable where serial_no=" + str(serial_no) + " and data_id =" + str(data_id)
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(json.dumps(data))


'''
checked_by_commissioner
final_document_submitted
returned_to_consultant
'''


def update_deliverable(request):
    data_id = ''
    if request.method == 'POST':
        data_id = request.POST.get('data_id')
        serial_no = request.POST.get('serial_no')
        existed_data = __db_fetch_values_dict(
            "select * from con_matrix_deliverable where data_id = " + str(data_id) + " and serial_no = " + str(
                serial_no) + " limit 1")
        policy_team_approval = request.POST.get('policy_team_approval')
        reintegration_team_approval = request.POST.get('reintegration_team_approval')
        m_e_team_approval = request.POST.get('m_e_team_approval')
        pm_approval = request.POST.get('pm_approval')
        returned_to_consultant_u = ""
        if len(request.POST.get('returned_to_consultant')) == 0:
            returned_to_consultant = None
            returned_to_consultant_u = "NULL"
        else:
            returned_to_consultant = request.POST.get('returned_to_consultant')
            returned_to_consultant_u = "'" + request.POST.get('returned_to_consultant') + "'"

        if request.POST.get('checked_by_commissioner') == '':
            checked_by_commissioner = None
            checked_by_commissioner_u = "NULL"
        else:
            checked_by_commissioner = request.POST.get('checked_by_commissioner')
            checked_by_commissioner_u = "'" + request.POST.get('checked_by_commissioner') + "'"
        stakeholder_approval = request.POST.get('stakeholder_approval')
        signed_off_by_pm = request.POST.get('signed_off_by_pm')

        if request.POST.get('final_document_submitted') == '':
            final_document_submitted = None
            final_document_submitted_u = "NULL"
        else:
            final_document_submitted = request.POST.get('final_document_submitted')
            final_document_submitted_u = "'" + request.POST.get('final_document_submitted') + "'"
        release_final_payment = request.POST.get('release_final_payment')
        performance_rating = request.POST.get('performance_rating')
        revised_report_received = request.POST.get('revised_report_received')

        cursor = connection.cursor()
        if existed_data:
            for temp in existed_data:
                id = temp['id']
                update_q = "UPDATE public.con_matrix_deliverable SET policy_team_approval='" + policy_team_approval + "', reintegration_team_approval='" + str(
                    reintegration_team_approval) + "', m_e_team_approval='" + str(
                    m_e_team_approval) + "', pm_approval='" + str(
                    pm_approval) + "', checked_by_commissioner=" + checked_by_commissioner_u + ", signed_off_by_pm='" + str(
                    signed_off_by_pm) + "', stakeholder_approval='" + str(
                    stakeholder_approval) + "', final_document_submitted=" + final_document_submitted_u + ", release_final_payment='" + str(
                    release_final_payment) + "', performance_rating='" + str(
                    performance_rating) + "', returned_to_consultant=" + str(
                    returned_to_consultant_u) + ", revised_report_received='" + str(
                    revised_report_received) + "' WHERE id = " + str(id)
                print(update_q)
                __db_commit_query(update_q)

        else:
            cursor.execute(
                """INSERT INTO public.con_matrix_deliverable(data_id, serial_no, policy_team_approval, reintegration_team_approval, m_e_team_approval, pm_approval, checked_by_commissioner, signed_off_by_pm, stakeholder_approval, final_document_submitted, release_final_payment, performance_rating, returned_to_consultant, revised_report_received)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
                (data_id, serial_no, policy_team_approval, reintegration_team_approval, m_e_team_approval, pm_approval,
                 checked_by_commissioner, signed_off_by_pm, stakeholder_approval, final_document_submitted,
                 release_final_payment, performance_rating, returned_to_consultant, revised_report_received))

    return HttpResponseRedirect('/asf/get_consultation_matrix_profile/' + data_id)


# All ODK form commonly loaded from here

@login_required
def get_form(request, id_string):
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    # server_address = '192.168.22.133:8001'
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='" + id_string + "'")
    return render(request, 'asfmodule/form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server})


@csrf_exempt
def get_form_access(request, id_string):
    q = "select * from coalesce(get_form_access_option('" + id_string + "'),0)"
    cursor = connection.cursor()
    cursor.execute(q)
    fetchVal = cursor.fetchone()
    cursor.close()
    val = fetchVal[0]

    return HttpResponse(val)


@login_required
def rsc_list(request):
    return render(request, 'asfmodule/rsc_list.html')


@csrf_exempt
def get_rsc_list(request):
    query = "select ROW_NUMBER() OVER (ORDER BY id) AS serial_no,id,rsc_name from usermodule_rsc"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def events_from_csv_list(request):
    return render(request, 'asfmodule/events_from_csv_list.html')


@csrf_exempt
def get_events_from_csv_list(request):
    query = "select ROW_NUMBER() OVER (ORDER BY id) AS serial_no,id,event_name from iom_event"
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def add_events_from_csv_form(request):
    if request.POST:
        event_name = request.POST.get('event_name')
        code = __db_fetch_single_value("select code::int+1 from iom_event order by code::int desc limit 1")
        query = "INSERT INTO public.iom_event (event_name,code) values('" + str(event_name) + "','" + str(code) + "')"
        __db_commit_query(query)
        return HttpResponseRedirect('/asf/events_from_csv_list/')
    return render(request, 'asfmodule/add_events_from_csv_form.html')


@login_required
def edit_events_from_csv(request, events_tbl_id):
    if request.POST:
        event_name = request.POST.get('event_name')
        query = "update public.iom_event  set event_name='" + str(event_name) + "' where id =" + str(events_tbl_id)
        __db_commit_query(query)
        return HttpResponseRedirect('/asf/events_from_csv_list/')

    qry = "select event_name from iom_event where id=" + str(events_tbl_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(qry, connection)
    event_name = df.event_name.tolist()[0]
    return render(request, 'asfmodule/edit_events_from_csv_form.html',
                  {'event_name': event_name, 'events_tbl_id': events_tbl_id})


@login_required
def delete_events_from_csv(request, events_tbl_id):
    query = "delete from public.iom_event  where id =" + str(events_tbl_id)
    __db_commit_query(query)
    return HttpResponseRedirect('/asf/events_from_csv_list/')


@login_required
def catchment_tree_test(request, rsc_id):
    query = "select * from geo_data where field_parent_id is null"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    id = df.id.tolist()
    name = df.field_name.tolist()
    all = zip(id, name)
    list_of_dictionary = []
    start = time.time()
    for id, name in all:
        query = "select id from geo_data where field_parent_id =" + str(id) + "limit 1"
        df = pandas.read_sql(query, connection)
        if len(df.id.tolist()):
            true = True
        else:
            true = False
        temp = {"id": id, "text": name, "hasChildren": true, "children": []}
        list_of_dictionary.append(temp)
    datasource = json.dumps({'list_of_dictionary': list_of_dictionary})
    check_nodes = get_check_nodes(rsc_id)
    json_content_dictionary = []
    for each in check_nodes:
        if each:
            query_for_json = "select uploaded_file_path from geo_data where id = " + str(each) + ""
            df = pandas.DataFrame()
            df = pandas.read_sql(query_for_json, connection)
            uploaded_file_path = df.uploaded_file_path.tolist()[0]
            if uploaded_file_path != "cd":
                file = open(uploaded_file_path, 'r')
                json_content = file.read()
                file.close()
            else:
                json_content = "{}"
            json_content_dictionary.append(json_content)
    print("END    " + str(time.time() - start))
    query = "select rsc_name from usermodule_rsc where id = " + rsc_id
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    rsc_name = df.rsc_name.tolist()[0]
    query = "WITH recursive t AS( SELECT id, field_name, field_parent_id FROM geo_data WHERE id IN ( SELECT (select id from geo_data where geocode = rsc_catchment_area.geo_id::text limit 1)geoid FROM PUBLIC.rsc_catchment_area WHERE rsc_id = " + str(
        rsc_id) + ") UNION ALL SELECT geo_data.id, geo_data.field_name, geo_data.field_parent_id FROM geo_data, t WHERE t.field_parent_id = geo_data.id) SELECT DISTINCT id, field_name, field_parent_id FROM t ORDER BY id"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    parent_list = df.id.tolist()
    query = "select node_name from geo_definition"
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    geo_def_list = df.node_name.tolist()
    return render(request, "asfmodule/catchment_tree_test.html", {'datasource': datasource
        , 'rsc_id': rsc_id
        , 'rsc_name': rsc_name
        , 'check_nodes': check_nodes, 'json_content': json_content_dictionary, 'parent_list': parent_list,
                                                                  'geo_def_list': json.dumps(geo_def_list)})


def get_check_nodes(rsc_id):
    query = "select (select id from geo_data where geocode = rsc_catchment_area.geo_id::text limit 1) geoid  from rsc_catchment_area where rsc_id = " + str(
        rsc_id) + ""
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    check_nodes = df.geoid.tolist()
    return check_nodes


@login_required
def catchment_data_insert(request):
    result_set = request.POST.get('result_set').split(',')
    rsc_id = int(request.POST.get('rsc_id'))
    delete_prev_catchment_record(rsc_id)
    result_set = list(set(result_set))
    for each in result_set:
        if each:
            query = "INSERT INTO public.rsc_catchment_area (rsc_id, geo_id) VALUES(" + str(
                rsc_id) + ", (select geocode::int from geo_data where id=" + str(each) + "))"
            __db_commit_query(query)
    return HttpResponseRedirect('/asf/rsc_list/')


def delete_prev_catchment_record(rsc_id):
    query = "delete from rsc_catchment_area where rsc_id = " + str(rsc_id) + ""
    __db_commit_query(query)


@login_required
def add_rsc_form(request):
    if request.POST:
        rsc_name = request.POST.get('rsc_name')
        query = "INSERT INTO public.usermodule_rsc (rsc_name) values('" + str(rsc_name) + "')"
        __db_commit_query(query)
        return HttpResponseRedirect('/asf/rsc_list/')
    return render(request, 'asfmodule/add_rsc_form.html')


@login_required
def edit_rsc_form(request, rsc_id):
    if rsc_id:
        edit_rsc_data = __db_fetch_values_dict("select * from usermodule_rsc where id  = " + str(rsc_id))
    if request.POST:
        rsc_name = request.POST.get('rsc_name')
        query = "UPDATE public.usermodule_rsc set rsc_name =  '" + str(rsc_name) + "' where id = " + str(rsc_id)
        __db_commit_query(query)
        return HttpResponseRedirect('/asf/rsc_list/')
    return render(request, 'asfmodule/edit_rsc_form.html', {
        'edit_rsc_data': edit_rsc_data[0]
    })


def beneficiary_progress_report(request, id):
    return render(request, 'asfmodule/beneficiary_status_report.html', {'id': id, 'year': '2019', 'quarter': 'June'})


@csrf_exempt
def get_progress_report_data(request):
    ben_tbl_id = request.POST.get('ben_tbl_id')
    income_q = "select * from vw_income_tracking_matrix where beneficiary_id=(select victim_id from asf_victim where id=" + str(
        ben_tbl_id) + ")"
    df_income = pandas.DataFrame()
    df_income = pandas.read_sql(income_q, connection)
    income_cat_list = []
    income_data_list = []
    for index, row in df_income.iterrows():
        print(str(row['_submission_time']), row['income_last_month'])
        income_cat_list.append(str(row['_submission_time']))
        income_data_list.append(row['income_last_month'])
    data = json.dumps({
        'income_cat_list': income_cat_list,
        'income_data_list': [{'name': '', 'data': income_data_list}]
    }, default=decimal_date_default)
    return HttpResponse(data)


@csrf_exempt
def get_reintegration_sustainibility_data(request):
    ben_tbl_id = request.POST.get('ben_tbl_id')
    # quarter = request.POST.get('qr')
    # year = request.POST.get('yr')

    q = "with t1 as(SELECT beneficiary_id, coalesce(round(economic_reintegration_score::numeric,2),0)economic_reintegration_score , coalesce(round(social_reintegration_score::numeric,2),0) social_reintegration_score, coalesce(round(psychosocial_score::numeric,2),0) psychosocial_score, coalesce(round(composite_score::numeric,2),0) composite_score, _submission_time, quarter, BTRIM(to_char((date(quarter||'-'||yr)),'Month'),' ') mon, yr FROM public.vw_reintegration_sustainability where victim_tbl_id = " + str(
        ben_tbl_id) + ") select *,(case when mon='March' then yr||'-'||'Q1' when mon='June' then yr||'-'||'Q2' when mon='September' then yr||'-'||'Q3' when mon='December' then yr||'-'||'Q4' else '' end) q_name from t1;"
    '''
    reintegration_q = "with t1 as(SELECT beneficiary_id, coalesce(round(economic_reintegration_score::numeric,2),0)economic_reintegration_score , coalesce(round(social_reintegration_score::numeric,2),0) social_reintegration_score, coalesce(round(psychosocial_score::numeric,2),0) psychosocial_score, coalesce(round(composite_score::numeric,2),0) composite_score, _submission_time, quarter, BTRIM (to_char((date(quarter||'-'||yr)),'Month'),' ') mon, yr FROM public.vw_reintegration_sustainability where beneficiary_id=(select victim_id from asf_victim where id=" + str(
        ben_tbl_id) + ")) select *,(case when mon='March' then yr||'-'||'Q1' when mon='June' then yr||'-'||'Q2' when mon='September' then yr||'-'||'Q3' when mon='December' then yr||'-'||'Q4' else '' end) q_name from t1 where mon like '" + str(
        quarter) + "' and yr like '" + str(year) + "' ";

    print reintegration_q
    df = pandas.DataFrame()
    df = pandas.read_sql(reintegration_q, connection)
    cat_list = []
    data_list = []
    d={}
    for index, row in df.iterrows():
        data_list.append(row['economic_reintegration_score'])
        cat_list.append('Economic')

        data_list.append(row['social_reintegration_score'])
        cat_list.append('Social')

        data_list.append(row['psychosocial_score'])
        cat_list.append('Psychosocial')

        data_list.append(row['composite_score'])
        cat_list.append('Composite')

        d = {
            'cat_list': cat_list,
            'data_list': [{'name': row['q_name'], 'data': data_list}]
        }

    data = json.dumps(d, default=decimal_date_default)
    '''
    df_u = pandas.read_sql(q, connection)
    cat_list_u = []
    eco_list = []
    social_list = []
    psy_list = []
    com_list = []
    for index, row in df_u.iterrows():
        cat_list_u.append(row['q_name'])

        eco_list.append(row['economic_reintegration_score'])
        social_list.append(row['social_reintegration_score'])
        psy_list.append(row['psychosocial_score'])
        com_list.append(row['composite_score'])
    d = {
        'cat_list': cat_list_u,
        'data_list': [{'name': 'Economic', 'data': eco_list}, {'name': 'Social', 'data': social_list},
                      {'name': 'Psychosocial', 'data': psy_list}
            , {'name': 'Composite', 'data': com_list}
                      ]}

    data = json.dumps(d, default=decimal_date_default)

    return HttpResponse(data)


'''
    EXPORT MODULE

'''


@login_required
def export(request):
    form_list = __db_fetch_values_dict("select id,title,id_string from logger_xform")
    rsc_list = __db_fetch_values_dict("select id,rsc_name from usermodule_rsc")
    user_list = get_own_and_partner_orgs_usermodule_users(request)
    username_list = [str(custom_user.user.username) for custom_user in user_list]
    # username_list.append(str(request.user.username))

    return render(request, 'asfmodule/export.html',
                  {'rsc_list': rsc_list, 'user_list': username_list, 'form_list': form_list})


@csrf_exempt
def get_export(request):
    id_string = request.POST.get('id_string')
    xform = get_object_or_404(XForm, id_string__exact=id_string)
    username = xform.user.username
    owner = get_object_or_404(User, username__iexact=username)
    '''
    if not has_permission(xform, owner, request):
        return HttpResponseForbidden(u'Not shared.')
    '''
    from_date = request.POST.get('from_date')
    to_date = request.POST.get('to_date')
    daterange = request.POST.get('date_range')
    userlist = request.POST.getlist('userlist[]')
    rsclist = request.POST.getlist('rsclist[]')

    query = get_query(from_date, to_date, rsclist, userlist, id_string)
    # query = '{"$and" : [ {"_submission_time":{"$gte":"2019-01-04T00:00:00","$lte":"2019-09-03T23:59:59"}},{"_submitted_by": { "$in" : ["iom_admin"] } }] }'
    print query

    export = Export.objects.create(xform=xform, export_type='xls')

    force_xlsx = True
    ext = 'xls' if not force_xlsx else 'xlsx'
    arguments = get_export_arguments('xls')

    flag = 0
    filepath = ''
    try:
        result = generate_export('xls', ext, username, id_string, export.id, query, arguments.get('group_delimiter'),
                                 arguments.get('split_select_multiples'), arguments.get('binary_select_multiples'),
                                 arguments.get('show_label'))
    except (Exception, NoRecordsFoundError) as e:
        export.internal_status = Export.FAILED
        export.save()
        flag = 2
        raise

    if not result.filename:
        flag = 0
    else:
        flag = 1
        filepath = '/media/' + str(result.filepath)

    data = {
        'flag': flag,
        'path': filepath
    }
    return HttpResponse(json.dumps(data), content_type='application/json')


def get_query(from_date, to_date, rsclist, userlist, id_string):
    eli_list = ['beneficiary_event', 'beneficiary_profiling', 'community_enterprise', 'counselor_psychosocial_support',
                'direct_inkind_support', 'general_followup', 'income_tracking_matrix', 'intervention_tracking_matrix',
                'medical_support', 'migration_forum', 'para_counselor_psychosocial_support',
                'preferred_services_reintegration_plan', 'psychosocial_assessment_plan', 'psychosocial_followup',
                'referral', 'referral_followup', 'reintegration_monitoring', 'reintegration_satisfaction',
                'reintegration_sustainability', 'social_reintegration',
                'socio_economic_support', 'support_history', 'training', 'training_followup']
    if id_string in eli_list:
        query = "with t1 as (with t as(select id,date_created,xform_id,user_id,json->>'victim_tbl_id' as victim_tbl_id, jsonb_set(jsonb_set(json::jsonb,'{_id}',to_jsonb(id)), '{_uuid}',to_jsonb(uuid)) as datajson from logger_instance where deleted_at is null) select coalesce(jsonb_set(jsonb_set(jsonb_set(datajson,'{_benificiary_id}',to_jsonb(beneficiary_id)),'{_case_number}',to_jsonb(case_number)),'{_rsc_name}',to_jsonb(rsc_name)),datajson) as datajson,xform_id,date_created,user_id,t.id from t left join vw_victim_export_cols on vw_victim_export_cols.id = t.victim_tbl_id::int4) select datajson from t1 where 1 = 1 ";
    elif id_string == 'returnee_case_initiation':
        query = "with t1 as (with t as(select id,date_created,xform_id,user_id,(select id from asf_victim where case_id::int4 = logger_instance.id) as victim_tbl_id, jsonb_set(jsonb_set(json::jsonb,'{_id}',to_jsonb(id)), '{_uuid}',to_jsonb(uuid)) as datajson from logger_instance where deleted_at is null) select coalesce(jsonb_set(jsonb_set(jsonb_set(datajson,'{_benificiary_id}',to_jsonb(beneficiary_id)),'{_case_number}',to_jsonb(case_number)),'{_rsc_name}',to_jsonb(rsc_name)),datajson) as datajson,xform_id,date_created,user_id,t.id from t left join vw_victim_export_cols on vw_victim_export_cols.id = t.victim_tbl_id::int4) select datajson from t1 where 1 = 1 "
    else:
        query = "select jsonb_set(jsonb_set(json::jsonb,'{_id}',to_jsonb(id)), '{_uuid}',to_jsonb(uuid)) as datajson from logger_instance where deleted_at is null "

    if id_string:
        query = query + " and xform_id = (select id from logger_xform where id_string = '" + str(id_string) + "')"

    if from_date and to_date:
        query += " and date_created between symmetric '" + str(from_date) + "' and '" + str(to_date) + "'"

    total_u_list = get_total_user_list(rsclist, userlist)

    if total_u_list:
        formatted_u_list_str = '\'' + '\', \''.join(total_u_list) + '\''
        query = query + " and user_id in (select id from auth_user where username in (%s))" % formatted_u_list_str

    return query


def get_total_user_list(rsclist, userlist):
    rsc_user = []
    total_user_list = []
    if rsclist:
        rsclist = [str(x) for x in rsclist]

        rsc_user_list = __db_fetch_values_dict(
            "select (select username from auth_user where id = user_id limit 1) username from usermodule_usermoduleprofile where rsc_name_id::text=any(ARRAY" + str(
                rsclist) + ")")
        for temp in rsc_user_list:
            rsc_user.append(str(temp['username']))
            # print rsc_user
    if userlist is not None:
        userlist = [str(x) for x in userlist]

    # Merge twolist and remove duplicate
    # creating set
    rsc_user_set = set(rsc_user)
    userlist_set = set(userlist)
    # Difference in two sets
    diff_element = userlist_set - rsc_user_set
    # union of difference + first list
    total_user_list = rsc_user + list(diff_element)
    return total_user_list


def remove_at(idx, s):
    return s[:idx] + s[idx + 1:]


def get_export_arguments(export_type):
    options = {
        'group_delimiter': '/',
        'split_select_multiples': True,
        'binary_select_multiples': False,
        'meta': None,
        'exp_data_typ': 'lbl'
    }
    arguments = {
    }

    if export_type in [Export.XLS_EXPORT, Export.GDOC_EXPORT,
                       Export.CSV_EXPORT, Export.CSV_ZIP_EXPORT,
                       Export.SAV_ZIP_EXPORT]:
        if options and "group_delimiter" in options:
            arguments["group_delimiter"] = options["group_delimiter"]
        if options and "split_select_multiples" in options:
            arguments["split_select_multiples"] = \
                options["split_select_multiples"]
        if options and "binary_select_multiples" in options:
            arguments["binary_select_multiples"] = \
                options["binary_select_multiples"]
        if options and "exp_data_typ" in options:
            dt_type = options["exp_data_typ"]
            if dt_type == 'lbl':
                arguments["show_label"] = True
            else:
                arguments["show_label"] = False

    return arguments


# Pot Song List
@login_required
def pot_song_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_pot_song'")
    return render(request, 'asfmodule/pot_song_list.html', {'form_id': form_id})


@csrf_exempt
def get_pot_song_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = """
        select  COALESCE((SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_pot_song') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_pot_song') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_pot_song_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_pot_song.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_pot_song_review
                                           WHERE  event_id::int = vw_merged_event_pot_song.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_pot_song
                  WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))
        """
    except Exception:
        query = """
        select  COALESCE((SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_pot_song') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_pot_song') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_pot_song_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_pot_song.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_pot_song_review
                                           WHERE  event_id::int = vw_merged_event_pot_song.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_pot_song
        """
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def pot_song_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_pot_song'")
    redirected_url = '/asf/pot_song_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def pot_song_profile(request, event_id):
    qry = "WITH t AS( SELECT id event_id, To_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created, ( SELECT username FROM auth_user WHERE id = user_id limit 1) username , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/district')) district , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/upazila')) upazila , COALESCE( ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/union')),'') union_name , json->>'geo/para_bazar_school' para_bazar_school , json->>'geo/village' village FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_pot_song') AND deleted_at IS NULL AND id = " + str(
        event_id) + "), t1 AS ( SELECT json->>'event_id' event_id, json->>'participant/male_greater_equal_18' male_greater_equal_18 , json->>'participant/male_less_18' male_less_18 , json->>'participant/female_greater_equal_18' female_greater_equal_18 , json->>'participant/female_less_18' female_less_18 , json->>'participant/total_participant' total_participant , (select participant_category from vw_event_participants where event_id = '" + str(
        event_id) + "') as participant_category, json->>'remarks' remarks FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_attendance_pot_song') AND deleted_at IS NULL AND ( json->>'event_id')::int = " + str(
        event_id) + ") SELECT t.event_id, t.date_created , t.username, t.district , t.upazila, t.union_name , t.para_bazar_school, t.village , t1.male_greater_equal_18, t1.male_less_18, t1.female_greater_equal_18, t1.female_less_18, t1.total_participant, t1.participant_category, t1.remarks FROM t LEFT JOIN t1 ON t.event_id = t1.event_id::int"
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_greater_equal_18 = df.male_greater_equal_18.tolist()[0] if len(df.male_greater_equal_18.tolist()) and \
                                                                    df.male_greater_equal_18.tolist()[
                                                                        0] is not None else ''
    male_less_18 = df.male_less_18.tolist()[0] if len(df.male_less_18.tolist()) and df.male_less_18.tolist()[
                                                                                        0] is not None  else ''
    female_greater_equal_18 = df.female_greater_equal_18.tolist()[0] if len(df.female_greater_equal_18.tolist()) and \
                                                                        df.female_greater_equal_18.tolist()[
                                                                            0] is not None  else ''
    female_less_18 = df.female_less_18.tolist()[0] if len(df.female_less_18.tolist()) and df.female_less_18.tolist()[
                                                                                              0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{500,501,502}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)

    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'pot_song_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_greater_equal_18': male_greater_equal_18,
        'female_greater_equal_18': female_greater_equal_18,
        'male_less_18': male_less_18,
        'female_less_18': female_less_18,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })


# School Program List
@login_required
def school_program_list(request):
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_school_program'")
    return render(request, 'asfmodule/school_program_list.html', {'form_id': form_id})


@csrf_exempt
def get_school_program_list(request):
    user_id = request.user.id
    try:
        __db_fetch_single_value("select geoid from usermodule_catchment_area where user_id = " + str(user_id))
        query = """
        select  COALESCE((SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_school_program') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_school_program') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_program_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_school_program.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_program_review
                                           WHERE  event_id::int = vw_merged_event_school_program.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_school_program
                  WHERE    coalesce(unions,upazila, district, division) = any(select geocode from get_catchment_area_by_user(""" + str(user_id) + """))
        """
    except Exception:
        query = """
        select COALESCE((SELECT can_edit
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (SELECT id  FROM   logger_xform
                                           WHERE  id_string='event_school_program') limit 1),0) can_edit,
                  COALESCE(
                             (
                             SELECT can_delete
                             FROM   vwrolewiseformpermission
                             WHERE  user_id = """ + str(user_id) + """
                             AND    xform_id =
                                    (
                                           SELECT id
                                           FROM   logger_xform
                                           WHERE  id_string='event_school_program') limit 1),0)    can_delete,
                                          row_number() OVER (ORDER BY id desc) AS serial_no,
                  id,
                  to_char(event_start_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS') event_start_date,
                  to_char(event_end_time::timestamptz, 'DD/MM/YYYY HH24:MI:SS')   event_end_date,
                  username,
                  district_label district ,
                  upazila_label upazila ,
                  union_label union_name ,
                  para_bazar_school ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_program_observation_checklist
                                           WHERE  event_id::int = vw_merged_event_school_program.id limit 1) THEN 1
                           ELSE 0
                  END observation ,
                  CASE
                           WHEN id::text =
                                    (
                                           SELECT event_id::text
                                           FROM   vw_event_school_program_review
                                           WHERE  event_id::int = vw_merged_event_school_program.id limit 1) THEN 1
                           ELSE 0
                  END review   from vw_merged_event_school_program
        """
    data = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    return HttpResponse(data)


@login_required
def school_program_form(request):
    username = request.user
    server_address = request.META.get('HTTP_HOST')
    print(server_address)
    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    form_id = __db_fetch_single_value("select id from logger_xform where id_string='event_school_program'")
    redirected_url = '/asf/school_program_list/'
    if request.GET:
        instance_id = request.GET.get('instance_id')
    else:
        instance_id = -1
    return render(request, 'asfmodule/formbuilder_form.html',
                  {'username': username, 'server_address': server_address, 'form_id': form_id,
                   'form_builder_server': form_builder_server, 'redirected_url': redirected_url,
                   'instance_id': instance_id})


@login_required
def school_program_profile(request, event_id):
    qry = "WITH t AS( SELECT id event_id, to_char((json->>'event/event_start_time')::date,'DD/MM/YYYY') date_created, ( SELECT username FROM auth_user WHERE id = user_id limit 1) username , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/district')) district , ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/upazila')) upazila , COALESCE( ( SELECT field_name FROM geo_data WHERE geocode = (json->>'geo/union')),'') union_name , json->>'geo/para_bazar_school' para_bazar_school , json->>'geo/village' village FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_school_program') AND deleted_at IS NULL AND id = " + str(
        event_id) + "), t1 AS ( SELECT json->>'event_id' event_id, json->>'participant/male_greater_15' male_greater_15 , json->>'participant/female_greater_15' female_greater_15 , json->>'participant/male_11_15' male_11_15 , json->>'participant/female_11_15' female_11_15 , json->>'participant/total_participant' total_participant , (select participant_category from vw_event_participants where event_id = '" + str(
        event_id) + "') as participant_category, json->>'remarks' remarks FROM logger_instance WHERE xform_id = ( SELECT id FROM logger_xform WHERE id_string = 'event_attendance_school_program') AND deleted_at IS NULL AND ( json->>'event_id')::int = " + str(
        event_id) + ") SELECT t.event_id, t.date_created , t.username, t.district , t.upazila, t.union_name , t.para_bazar_school, t.village , t1.male_greater_15, t1.female_greater_15, t1.male_11_15, t1.female_11_15, t1.total_participant, t1.participant_category, t1.remarks FROM t LEFT JOIN t1 ON t.event_id = t1.event_id::int"
    df = pandas.read_sql(qry, connection)
    event_id = df.event_id.tolist()[0] if len(df.event_id.tolist()) and df.event_id.tolist()[0] is not None  else ''
    date_created = df.date_created.tolist()[0] if len(df.date_created.tolist()) and df.date_created.tolist()[
                                                                                        0] is not None  else ''
    submitted_by = df.username.tolist()[0] if len(df.username.tolist()) and df.username.tolist()[0] is not None  else ''
    district = df.district.tolist()[0] if len(df.district.tolist()) and df.district.tolist()[0] is not None  else ''
    upazila = df.upazila.tolist()[0] if len(df.upazila.tolist()) and df.upazila.tolist()[0] is not None  else ''
    union = df.union_name.tolist()[0] if len(df.union_name.tolist()) and df.union_name.tolist()[0] is not None  else ''
    village = df.village.tolist()[0] if len(df.village.tolist()) and df.village.tolist()[0] is not None else ''
    para_bazar_school = df.para_bazar_school.tolist()[0] if len(df.para_bazar_school.tolist()) and \
                                                            df.para_bazar_school.tolist()[0] is not None  else ''
    male_greater_15 = df.male_greater_15.tolist()[0] if len(df.male_greater_15.tolist()) and \
                                                        df.male_greater_15.tolist()[0] is not None else ''
    female_greater_15 = df.female_greater_15.tolist()[0] if len(df.female_greater_15.tolist()) and \
                                                            df.female_greater_15.tolist()[0] is not None  else ''
    male_11_15 = df.male_11_15.tolist()[0] if len(df.male_11_15.tolist()) and df.male_11_15.tolist()[
                                                                                  0] is not None  else ''
    female_11_15 = df.female_11_15.tolist()[0] if len(df.female_11_15.tolist()) and df.female_11_15.tolist()[
                                                                                        0] is not None  else ''
    total_participant = df.total_participant.tolist()[0] if len(df.total_participant.tolist()) and \
                                                            df.total_participant.tolist()[0] is not None  else ''
    participant_category = df.participant_category.tolist()[0] if len(df.participant_category.tolist()) and \
                                                                  df.participant_category.tolist()[
                                                                      0] is not None  else ''

    user_id = request.user.id
    query = """ SELECT distinct category_id,'<div class="row"> <div class="col-lg-12"> <div class="panel-group"  role="tablist" aria-multiselectable="true"><div class="panel panel-default" style="margin-bottom: 10px;"><div style="height: 48px;" class="panel-heading" role="tab" id="heading'||category_id||'"><h4 class="panel-title"><a style="font-weight: bold;" class="collapsed"  onclick="load_forms('|| category_id ||',''internal_accordian'|| category_id ||''')" role="button" data-toggle="collapse"  href="#collapse'|| category_id ||'" aria-expanded="false" aria-controls="collapse'|| category_id ||'"> ' ||(SELECT category_name FROM forms_categories WHERE id = fc.category_id :: INT) || ' </a>'|| case when first_value(can_submit)over(PARTITION by category_id ORDER by can_submit desc) = 1 then '<a onclick="load_forms_list('|| category_id ||')"  class="btn btn-success btn-sm pull-right"   id="form'|| category_id ||'"  data-toggle="modal" data-target="#myModal"  ><i class="fa fa-4x fa fa-plus"></i></a>' else '' end  ||' </h4></div><div id="collapse'|| category_id ||'" class="panel-collapse collapse" role="tabpanel" aria-labelledby="heading'|| category_id ||'"><div class="panel-body"><div class="panel-group" id="internal_accordian'|| category_id ||'" role="tablist" aria-multiselectable="true"></div></div></div></div></div></div></div>' as form_str FROM vwrolewiseformpermission rf, forms_categories_relation fc WHERE ( rf.can_view = 1 OR rf.can_submit = 1) AND fc.form_id = rf.xform_id and fc.category_id = any('{600,601,602}') AND user_id = """ + str(
        user_id) + """ order by category_id asc """
    df = pandas.DataFrame()
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['form_str']:
        main_str += str(each)
    main_str = json.dumps(main_str)
    username = request.user
    # if in local environment, you should use your ip instead of localhost
    # server_address = request.META.get('ip')+':'+request.META.get('HTTP_HOST').split(':', 1)[1]
    # when in developement/live/client server
    server_address = request.META.get('HTTP_HOST')
    print(server_address)

    form_builder_server = __db_fetch_single_value("select form_builder_server from form_builder_configuration")
    module = 'school_program_profile'
    return render(request, "asfmodule/formbuilder_profile.html", {
        'main_str': main_str,
        'username': username,
        'submitted_by': submitted_by,
        'event_id': event_id,
        'date_created': date_created,
        'district': district,
        'upazila': upazila,
        'union': union,
        'village': village,
        'para_bazar_school': para_bazar_school,
        'male_greater_15': male_greater_15,
        'female_greater_15': female_greater_15,
        'male_11_15': male_11_15,
        'female_11_15': female_11_15,
        'total_participant': total_participant,
        'participant_category': participant_category,
        'server_address': server_address, 'form_builder_server': form_builder_server, 'module': module

    })
