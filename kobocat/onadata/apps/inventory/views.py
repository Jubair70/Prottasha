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


@login_required
def index(request):
    rsc_data_list = __db_fetch_values_dict("select * from usermodule_rsc")
    return render(request, "inventory/index.html", {
        'dataset': rsc_data_list
    })


@csrf_exempt
def get_product_table(request):

    from_date = request.POST.get('start_date')
    to_date = request.POST.get('end_date')
    rsc = request.POST.get('rsc_name')
    if ((from_date == '' or from_date is None) or (to_date == '' or to_date is None)):
        from_date = '2000-01-01'
        to_date = '2050-12-31'
    q = "select * from vw_product where date(created_at) between '"+from_date+"' and '"+to_date+"' and coalesce(rsc_name::text,'') like '"+rsc+"' order by id desc"

    data = __db_fetch_values_dict(q)

    return render(request, "inventory/product_table.html", {
        'dataset': data
    })


def add_product(request):

    if request.method == 'POST':

        product_name = request.POST.get("product_name")

        q = "INSERT INTO public.product (product_name,balance, created_at,created_by)VALUES('"+str(product_name)+"', 0,NOW(),"+str(request.user.id)+");"

        __db_commit_query(q)

    return HttpResponseRedirect("/inventory/")


@csrf_exempt
def stockin_product(request):
    rsc_data_list = __db_fetch_values_dict("select * from usermodule_rsc")
    if request.method == 'POST':
        p_id = request.POST.get("p_id")
        p_qty = request.POST.get("p_qty")
        p_date = request.POST.get("p_date")
        insert_q = "INSERT INTO public.product_stock_in(product_id, in_date, qty, stockin_by, created_at)VALUES ("+str(p_id)+", '"+str(p_date)+"', "+str(p_qty)+", "+str(request.user.id)+",NOW());"

        current_qty = __db_fetch_single_value("select balance from product where id = "+str(p_id))
        total_balance = current_qty+int(p_qty)
        update_q = "update product set balance = "+str(total_balance)+" where id =   "+str(p_id)
        __db_commit_query(insert_q)
        __db_commit_query(update_q)

        messages.success(request, '<i class="fa fa-check-circle"></i> Stocked successfully!',
                         extra_tags='alert-success crop-both-side')
        return HttpResponseRedirect('/inventory/')

    return render(request, "inventory/stockin_history.html", {'dataset': rsc_data_list})

@csrf_exempt
def check_stockout_qty(request):
    out_qty = request.POST.get("out_qty")
    pout_id = request.POST.get("pout_id")
    current_qty = __db_fetch_single_value("select balance from product where id = " + str(pout_id))
    flag=0
    if current_qty >= int(out_qty):
        flag=1
    else:
        flag=0
    return HttpResponse(flag)


@csrf_exempt
def stockout_product(request):
    rsc_data_list = __db_fetch_values_dict("select * from usermodule_rsc")
    if request.method == 'POST':
        pout_id = request.POST.get("pout_id")
        pout_qty = request.POST.get("pout_qty")
        pout_date = request.POST.get("pout_date")
        pout_req_by = request.POST.get("pout_req_by")
        pout_offi_name = request.POST.get("pout_offi_name")
        pout_purpose = request.POST.get("pout_purpose")
        pout_receipient = request.POST.get("pout_receipient")
        created_at = datetime.datetime.now()
        #insert_q = "INSERT INTO public.product_stock_out(product_id, out_date, qty, request_by, officer_name, purpose, recepient, created_at, created_by)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);"

        #q= """INSERT INTO public.product_stock_out(product_id, out_date, qty, request_by, officer_name, purpose, recepient, created_at, created_by)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",(pout_id, pout_date, pout_qty,pout_req_by, pout_offi_name,pout_purpose,pout_receipient,created_at,request.user.id)

        current_qty = __db_fetch_single_value("select balance from product where id = " + str(pout_id))

        if current_qty >= int(pout_qty):
            balance_rest = current_qty-int(pout_qty)
            update_q = "update product set balance = "+str(balance_rest)+" where id =   "+str(pout_id)
            cursor = connection.cursor()

            cursor.execute("""INSERT INTO public.product_stock_out(product_id, out_date, qty, request_by, officer_name, purpose, recepient, created_at, created_by)VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",(pout_id, pout_date, pout_qty,pout_req_by, pout_offi_name,pout_purpose,pout_receipient,created_at,request.user.id))
            #__db_commit_query(q)
            __db_commit_query(update_q)

            messages.success(request, '<i class="fa fa-check-circle"></i> Stock out successfully!',
                         extra_tags='alert-success crop-both-side')
            return HttpResponseRedirect('/inventory/')
        else:
            messages.success(request, '<i class="fa fa-check-circle"></i> Stock quantity is less than requested quantity!',
                             extra_tags='alert-danger crop-both-side')
            return HttpResponseRedirect('/inventory/')

    return render(request, "inventory/stockout_history.html", {'dataset': rsc_data_list})


@csrf_exempt
def get_stockout_history_data(request):
    from_date = request.POST.get('start_date')
    to_date = request.POST.get('end_date')
    rsc = request.POST.get('rsc_name')
    if ((from_date == '' or from_date is None) or (to_date == '' or to_date is None)):
        from_date = '2000-01-01'
        to_date = '2050-12-31'
    q = "select * from vw_product_stockout where out_date between '"+from_date+"' and '"+to_date+"' and coalesce(rsc_name::text,'') like '"+rsc+"' order by id desc "
    print q
    dataset = __db_fetch_values_dict(q)
    return render(request, "inventory/stockout_history_table.html", {'dataset': dataset})

@csrf_exempt
def get_stockin_history_data(request):

    from_date = request.POST.get('start_date')
    to_date = request.POST.get('end_date')
    rsc = request.POST.get('rsc_name')
    if ((from_date == '' or from_date is None) or (to_date == '' or to_date is None)):
        from_date = '2000-01-01'
        to_date = '2050-12-31'
    print rsc
    print from_date
    print to_date
    q = "select * from vw_product_stockin where in_date between '"+from_date+"' and '"+to_date+"' and coalesce(rsc_name::text,'') like '"+rsc+"' order by id desc"
    dataset = __db_fetch_values_dict(q)
    return render(request, "inventory/stockin_history_table.html", {'dataset': dataset})


