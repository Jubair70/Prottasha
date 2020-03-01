#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from celery.decorators import task
from datetime import timedelta
from celery.task import periodic_task
from django.db import connections
from django.http import HttpResponse
from django.core.cache import cache
import requests
import httplib
import json
from celery.schedules import crontab
from datetime import datetime, timedelta
from collections import OrderedDict
from task_helper import __send_followup_messages
from task_helper_didibot import __send_followup_messages_v2
import datetime


def __db_fetch_values(query):
    try:
        # print "data query"
        cursor = connections['iom'].cursor()
        print "success1"
        cursor.execute(query)
        print "success2"
        fetch_val = cursor.fetchall()
        print "success3"
        return fetch_val
    except Exception, e:
        print "db get error"
        print str(e)
        # Rollback in case there is any error

    finally:
        cursor.close()


def __db_change_query(query):
    try:
        # print "data query"
        cur = connections['iom'].cursor()
        cur.execute(query)
        # conn.commit()
        connections['iom'].commit()
        return 0
    except Exception, e:
        print "db error"
        print str(e)
        return -1
        # Rollback in case there is any error
    finally:
        cur.close()


def single_query(query):
    """function for  query where result is single"""

    fetchVal = __db_fetch_values(query)
    # print "single query"
    if fetchVal is None:
        return None
    if len(fetchVal) == 0:
        return None

    strType = map(str, fetchVal[0])
    ans = strType[0]
    return ans


def __db_fetch_values_dict(query):
    cursor = connections['iom'].cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def update_table(query):
    try:
        print query
        # create a new cursor
        cur = connections['iom'].cursor()
        # execute the UPDATE  statement
        cur.execute(query)
        # get the number of updated rows
        vendor_id = cur.fetchone()[0]
        print vendor_id
        # Commit the changes to the database_
        connections['iom'].commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception) as error:
        print(error)


def get_scheduled_user_id(scheduled_role, user_id, householdid, sectorid):
    # print each_sch[0]
    qry = "SELECT public.get_scheduled_user_id(" + str(scheduled_role) + "," + str(user_id) + "," + str(
        householdid) + "," + str(sectorid) + ")"
    print qry
    # cur.execute(qry)
    user_list = __db_fetch_values(qry)

    # return cur.fetchall()[0][0]
    return user_list[0][0]


def get_sector_id(sectorid):
    sec_sql = "select id from sector where sector_code='" + sectorid + "'"
    # cur.execute(sec_sql)
    # sec_list=cur.fetchall()
    sec_list = __db_fetch_values(sec_sql)

    if sec_list is not None and len(sec_list) > 0:
        return sec_list[0][0]
    return -1


def get_household_id(sectorid, hh_id):
    hh_sql = "select id from household where household_id='" + hh_id + "' and sector_id=" + str(sectorid)
    print hh_sql
    # cur.execute(hh_sql)
    # hh_list=cur.fetchall()
    hh_list = __db_fetch_values(hh_sql)

    if hh_list is not None and len(hh_list) > 0:
        return hh_list[0][0]
    return -1


def get_beneficiary_id(uid):
    ben_sql = "select id FROM beneficiary where uid='" + str(
        uid) + "' and status not in('WOMAN_DIED','INACTIVE','DELETED');"

    ben_list = __db_fetch_values(ben_sql)

    if ben_list is not None and len(ben_list) > 0:
        return ben_list[0][0]
    return -1


def get_start_point_name(start_point):
    # print each_sch[0]
    qry = "select start_point_name from start_point_def where id=" + str(start_point) + ";"
    print qry
    # cur.execute(qry)
    sp_list = __db_fetch_values(qry)

    # return cur.fetchall()[0][0]
    return sp_list[0][0]


def get_study_id(instance_id):
    # print each_sch[0]
    qry = "SELECT study_id FROM study_form where form_id=any(select xform_id from logger_instance where id=" + str(
        instance_id) + ");"
    print qry
    # cur.execute(qry)
    s_list = __db_fetch_values(qry)

    # return cur.fetchall()[0][0]
    return s_list[0][0]


def generate_schedule(instance_id, each_sch, sectorid, householdid, uid, scheduleid, user_id):
    # print each_sch[0]
    start_point_id = each_sch[3]
    schedule_type_id = each_sch[8]
    schedule_applicable_for = each_sch[10]
    source_form_id = each_sch[9]
    scheduled_form_id = each_sch[13]
    scheduled_role_id = each_sch[11]
    print "_______________________"

    start_point_name = get_start_point_name(start_point_id)
    study_id = get_study_id(instance_id)

    # sp_qry="select  get_start_point(3,'"+ str(start_point_id) +"',1)"
    sp_qry = "select  get_start_point(" + str(instance_id) + ",'" + str(start_point_name) + "'," + str(study_id) + ")"
    # cur.execute(sp_qry)

    sp = __db_fetch_values(sp_qry)

    start_point = sp[0][0]

    schedule_user_id = get_scheduled_user_id(scheduled_role_id, user_id, householdid, sectorid)

    if start_point_name == "Start of Round":
        batch_adjust = "select week_interval from batch where id=any(select batch_id from user_batch_map where user_id=" + str(
            user_id) + ")"
        print batch_adjust
        bta = __db_fetch_values(batch_adjust)
        if bta is not None and len(bta) > 0:
            week_interval = bta[0][0]
            print "###########################################1"
            print week_interval * 7
            t1 = datetime.strptime(start_point, "%Y-%m-%d")
            t = t1 + timedelta(days=week_interval * 7)
        else:
            t = datetime.strptime(start_point, "%Y-%m-%d")
    else:
        t = datetime.strptime(start_point, "%Y-%m-%d")
    print t

    interval_length = each_sch[4]

    interval_unit = each_sch[5]

    if str(interval_unit) == "3":
        round_length = 8
        interval_length = round_length * 7

    # t = datetime.strptime(start_point, "%Y-%m-%d")


    schedule_date = t + timedelta(days=interval_length)
    print schedule_date

    schedule_status = "ACTIVE"

    if str(schedule_type_id) == "1":
        if str(schedule_applicable_for) == "3":
            print "generate_schedule for household"
            gsch_qry = "INSERT INTO schedule(created_date, updated_date, status, schedule_date, instance_id, scheduled_form_id, household_id, parent_schedule_id, jweek_id, schedule_user_id, source_form_id,sector_id,role_id)    VALUES (now(), now(), '" + schedule_status + "', '" + str(
                schedule_date) + "', " + str(instance_id) + ", " + str(scheduled_form_id) + ", " + str(
                householdid) + ", " + str(scheduleid) + ", get_jivita_week_id('" + str(
                schedule_date) + "'::date), " + str(schedule_user_id) + ", " + str(source_form_id) + "," + str(
                sectorid) + "," + str(scheduled_role_id) + ");"

            __db_change_query(gsch_qry)
            print gsch_qry
        elif str(schedule_applicable_for) == "1":
            print "generate_schedule for mother"
            ben_id = get_beneficiary_id(uid)
            gsch_qry = "INSERT INTO schedule(created_date, updated_date, status, schedule_date, instance_id, scheduled_form_id, household_id, parent_schedule_id, jweek_id, schedule_user_id, source_form_id,sector_id,beneficiary_id,role_id)    VALUES (now(), now(), '" + schedule_status + "', '" + str(
                schedule_date) + "', " + str(instance_id) + ", " + str(scheduled_form_id) + ", " + str(
                householdid) + ", " + str(scheduleid) + ", get_jivita_week_id('" + str(
                schedule_date) + "'::date), " + str(schedule_user_id) + ", " + str(source_form_id) + "," + str(
                sectorid) + "," + str(ben_id) + "," + str(scheduled_role_id) + ");"

            __db_change_query(gsch_qry)
            print gsch_qry
        elif str(schedule_applicable_for) == "2":
            print "generate_schedule for child"
        else:
            print "no schedule"
            # household schedule

    else:
        print "cancel schedule"


def regenerate_parent_schedule(instance_id, each_sch, sectorid, householdid, uid, scheduleid, user_id):
    parent_sch_qry = "SELECT parent_schedule_id FROM public.schedule where id=" + str(scheduleid)
    psq = __db_fetch_values(parent_sch_qry)
    ps_id = psq[0][0]
    qry = "insert into schedule(created_date, updated_date, beneficiary_id, status, schedule_date, instance_id, scheduled_form_id, household_id, parent_schedule_id, jweek_id, prev_wrong_schedule_id, schedule_user_id, source_form_id, created_by, updated_by,  sector_id) SELECT now(), now(), beneficiary_id, 'HOLD', schedule_date, " + str(
        instance_id) + ", scheduled_form_id, household_id, parent_schedule_id, jweek_id, prev_wrong_schedule_id, schedule_user_id, source_form_id, created_by, updated_by, sector_id FROM schedule where id=" + str(
        ps_id)
    __db_change_query(qry)
    print qry


def get_compare_value(logic_id, instance_id):
    qry = "SELECT id, coalesce(variable_name,'') variable_name, variable_type, (select comparator_name from comparator_def where id=logic_comparator.comparator_id), val_1, val_2,variable_source, study_id, form_id, submission_type FROM logic_comparator where id=" + str(
        logic_id) + ";"
    print qry
    # cur.execute(qry)
    # logic_list_all=cur.fetchall()

    logic_list_all = __db_fetch_values(qry)
    logic_list = logic_list_all[0]

    variable_name = logic_list[1]
    variable_type = logic_list[2]
    comparator_name = logic_list[3]
    val_1 = logic_list[4]
    val_2 = logic_list[5]
    variable_source = logic_list[6]
    study_id = logic_list[7]
    form_id = logic_list[8]
    submission_type = logic_list[9]
    i_val = ""
    print variable_type
    if variable_source == "current":
        if variable_name == "":
            return True
        if variable_type == "constant":
            i_val = variable_name
        elif variable_type == "text" or variable_type == "select one" or variable_type == "calculate":
            instance_qry = "select json->>'" + variable_name + "' from logger_instance where id=" + str(
                instance_id) + ";"
            # print instance_qry
            # cur.execute(instance_qry)
            # instance_val= cur.fetchall()
            instance_val = __db_fetch_values(instance_qry)
            if instance_val is not None:
                i_val = instance_val[0][0]

    elif variable_source == "other":
        print submission_type
        if submission_type == "last":
            # get last submission id for this benificiary and/or household
            print submission_type
        elif submission_type == "any":
            # check whether any submission has this value
            print submission_type
            # print form_id

    elif variable_source == "profile":
        print submission_type
    else:
        return False

    print 'i_val', i_val, comparator_name, val_1
    if comparator_name == '=':
        # print "here",str(i_val)==str(val_1)
        return str(i_val) == str(val_1)
    # print comparator_name
    # print i_val
    return False


def check_condition(cid, instance_id):
    qry = "SELECT id, coalesce(block_id_1,-1) block_id_1, coalesce(block_id_2,-1) block_id_2, coalesce(is_block_1,0) is_block_1,coalesce(is_block_2,0) is_block_2,coalesce(function_operator,'') function_operator FROM logic_block where id=" + str(
        cid)
    # print qry
    # cur.execute(qry)
    # block_list_all=cur.fetchall()

    block_list_all = __db_fetch_values(qry)
    block_list = block_list_all[0]

    block_id_1 = block_list[1]
    block_id_2 = block_list[2]

    is_block_1 = block_list[3]
    is_block_2 = block_list[4]

    print "########################"

    print block_id_1
    print block_id_2
    print is_block_1
    print is_block_2

    function_operator = block_list[5]

    block_condition_1 = False
    block_condition_2 = False

    # print(str(block_id_1) !='-1' and str(is_block_1)=='0')

    if str(block_id_1) == '-1':
        block_condition_1 = True

    if str(block_id_1) != '-1' and str(is_block_1) == '0':
        block_condition_1 = get_compare_value(block_id_1, instance_id)

    if str(block_id_1) != '-1' and str(is_block_1) == '1':
        block_condition_1 = check_condition(block_id_1, instance_id)

    if str(block_id_2) == '-1':
        block_condition_2 = True

    if str(block_id_2) != '-1' and str(is_block_2) == '0':
        block_condition_2 = get_compare_value(block_id_2, instance_id)

    if str(block_id_2) != '-1' and str(is_block_2) == '1':
        block_condition_2 = check_condition(block_id_2, instance_id)
    # print block_condition_1
    # print block_condition_2
    # print function_operator

    if function_operator == '' or function_operator == 'None' or function_operator == 'and':
        return block_condition_1 and block_condition_2

    if function_operator == 'or':
        return block_condition_1 or block_condition_2
    return False


def cancel_schedule(instance_id, each_sch, sectorid, householdid, uid, scheduleid, user_id):
    # print each_sch[0]

    schedule_type_id = each_sch[8]
    schedule_applicable_for = each_sch[10]
    scheduled_form_id = each_sch[13]

    study_id = get_study_id(instance_id)

    schedule_status = "CANCELLED"

    if str(schedule_type_id) == "2":
        if str(schedule_applicable_for) == "3":
            print "cancel_schedule for household"
            gsch_qry = "update schedule set status='" + schedule_status + "' where status='ACTIVE' and household_id=" + str(
                householdid) + " and scheduled_form_id=" + str(scheduled_form_id) + ";"
            # gsch_qry="INSERT INTO schedule(created_date, updated_date, status, schedule_date, instance_id, scheduled_form_id, household_id, parent_schedule_id, jweek_id, schedule_user_id, source_form_id,sector_id)    VALUES (now(), now(), '" + schedule_status + "', '" + str(schedule_date) + "', " + str(instance_id) + ", " + str(scheduled_form_id) + ", "+ str(householdid) +", "+ str(scheduleid) +", get_jivita_week_id('" + str(schedule_date) + "'::date), "+ str(schedule_user_id) +", " + str(source_form_id)+","+ str(sectorid) + ");"
            __db_change_query(gsch_qry)
            print gsch_qry
        elif str(schedule_applicable_for) == "1":
            print "cancel_schedule for mother"
            ben_id = get_beneficiary_id(uid)
            gsch_qry = "update schedule set status='" + schedule_status + "' where status='ACTIVE' and beneficiary_id=" + str(
                ben_id) + " and scheduled_form_id=" + str(scheduled_form_id) + ";"
            # gsch_qry="INSERT INTO schedule(created_date, updated_date, status, schedule_date, instance_id, scheduled_form_id, household_id, parent_schedule_id, jweek_id, schedule_user_id, source_form_id,sector_id,beneficiary_id)    VALUES (now(), now(), '" + schedule_status + "', '" + str(schedule_date) + "', " + str(instance_id) + ", " + str(scheduled_form_id) + ", "+ str(householdid) +", "+ str(scheduleid) +", get_jivita_week_id('" + str(schedule_date) + "'::date), "+ str(schedule_user_id) +", " + str(source_form_id)+","+ str(sectorid)+","+ str(ben_id) + ");"
            __db_change_query(gsch_qry)
            print gsch_qry
        elif str(schedule_applicable_for) == "2":
            print "generate_schedule for child"
        else:
            print "no schedule"
            # household schedule

    else:
        print "cancel schedule"


def cancel_all_schedule(instance_id, each_sch, sectorid, householdid, uid, scheduleid, user_id, schedule_status):
    # print each_sch[0]
    schedule_type_id = each_sch[8]
    schedule_applicable_for = each_sch[10]
    scheduled_form_id = each_sch[13]

    study_id = get_study_id(instance_id)

    # schedule_status="CANCELLED"



    if str(schedule_type_id) == "2" or str(schedule_type_id) == "4":
        if str(schedule_applicable_for) == "3":
            print "cancel_schedule for household"
            gsch_qry = "update schedule set status='" + schedule_status + "' where status='ACTIVE' and household_id=" + str(
                gsch) + ";"
            __db_change_query(gsch_qry)
            print gsch_qry
        elif str(schedule_applicable_for) == "1":
            print "cancel_schedule for mother"
            ben_id = get_beneficiary_id(uid)
            gsch_qry = "update schedule set status='" + schedule_status + "' where status='ACTIVE' and beneficiary_id=" + str(
                ben_id) + ";"

            __db_change_query(gsch_qry)
            print gsch_qry
        elif str(schedule_applicable_for) == "2":
            print "generate_schedule for child"
        else:
            print "no schedule"
            # household schedule

    else:
        print "cancel schedule"


def generate_all_schedule(instance_id):
    condition_id = -1
    form_id = -1

    ins_sql = "select xform_id,json,user_id from logger_instance where id=" + str(instance_id)
    print ins_sql
    # cur.execute(ins_sql)
    # ins_list=cur.fetchall()
    ins_list = __db_fetch_values(ins_sql)

    if ins_list is not None:
        for each_inst in ins_list:
            form_id = each_inst[0]
            json = each_inst[1]
            user_id = each_inst[2]
            # print json.items()
    sectorid = ""
    scheduleid = "-1"
    householdid = ""
    uid = ""
    sector_primary_id = -1
    hh_primary_id = -1

    for k, v in json.items():
        # print k,v
        if k == "sectorid" or k == "TLIGIS_RENEWSECTORID":
            sectorid = v
            sector_primary_id = get_sector_id(sectorid)
        if k == "scheduleid":
            scheduleid = v
        if k == "householdid" or k == "GISV_HHID" or k == "TLIGIS_NEWREHHID":
            householdid = v
        if k == "uid" or k == "NWVM_WOMANUID":
            uid = v
    if householdid <> "":
        hh_primary_id = get_household_id(sector_primary_id, householdid)

    df = []
    sch_sql = "SELECT id, event_id, (select block_id from form_outcomes where id=logic.condition_id) condition_id, start_point_id, interval_length, interval_unit_id, after_interval_length, after_interval_unit_id, schedule_type_id, form_id, shedule_applicable_for_id, sheduled_role_id, validity_period,coalesce(scheduled_form,-1) scheduled_form FROM logic where form_id=" + str(
        form_id)
    print sch_sql
    # cur.execute(sch_sql)

    # sch_list=cur.fetchall()
    sch_list = __db_fetch_values(sch_sql)

    if sch_list is not None:
        for each_sch in sch_list:
            condition_id = each_sch[2]
            schedule_type_id = each_sch[8]
            scheduled_form = each_sch[13]

            chk_condition = check_condition(condition_id, instance_id)
            print chk_condition
            if chk_condition == True:
                if str(schedule_type_id) == "1":
                    print "generate_schedule"
                    generate_schedule(instance_id, each_sch, sector_primary_id, hh_primary_id, uid, scheduleid, user_id)
                elif str(schedule_type_id) == "3":
                    print "cancel_all_schedule"
                    cancel_all_schedule(instance_id, each_sch, sector_primary_id, hh_primary_id, uid, scheduleid,
                                        user_id, "CANCELLED")
                elif str(schedule_type_id) == "4":
                    print "hold_schedule"
                    cancel_all_schedule(instance_id, each_sch, sector_primary_id, hh_primary_id, uid, scheduleid,
                                        user_id, "HOLD")
                elif str(schedule_type_id) == "5":
                    print "regenerate_parent_schedule"
                    regenerate_parent_schedule(instance_id, each_sch, sector_primary_id, hh_primary_id, uid, scheduleid,
                                               user_id)
                else:
                    print scheduled_form
                    if str(scheduled_form) == "-1":
                        cancel_all_schedule(instance_id, each_sch, sector_primary_id, hh_primary_id, uid, scheduleid,
                                            user_id, "CANCELLED")
                        print "cancel_all_schedule"
                    else:
                        cancel_schedule(instance_id, each_sch, sector_primary_id, hh_primary_id, uid, scheduleid,
                                        user_id)
                        print "cancel_schedule"


@periodic_task(run_every=timedelta(seconds=10), name="populate_table_queue_iom")
def queue_info_insert(lock_expire=1200):
    print "Started"
    lock_key = 'instance_data'
    acquire_lock = lambda: cache.add(lock_key, '1', lock_expire)
    release_lock = lambda: cache.delete(lock_key)
    if acquire_lock():
        try:
            instance_query = "select id, instance_id, xform_id from instance_queue where status='new' order by created_at"

            instance_queue = __db_fetch_values(instance_query)

            print("instance_queue")
            print(instance_queue)

            for each in instance_queue:
                function_query = 'select function_name from form_function where form_id =%s' % (each[2])
                form_function = single_query(function_query)
                print form_function
                insert_data_query = ''
                # update_instance=""
                print "_____________________________________________"
                if form_function is not None:
                    if 'view' in form_function:
                        insert_data_query = 'REFRESH MATERIALIZED VIEW %s' % (form_function[5:])
                        print
                        'inside update'
                        cursor = connections['iom'].cursor()
                        cursor.execute(insert_data_query)
                        cursor.close()
                        "overlay('Txxxxas' placing 'hom' from 2 for 4)"
                        # update_csv = "update user_csv_status set isvalid=0 where profile_id = any(select distinct profile_id from usermodule_profileorganization where organization_id = any (select distinct id from vwbranchvillagecoverage_mat where up_code = (select SUBSTRING (json->>'upazila'::text, 3 ) from logger_instance where id=%s)))"%(each[1])
                        # update_table(update_csv)
                        print
                        'inside update'
                        update_instance = "update instance_queue set status = 'old' , updated_at = now() where instance_id = %s" % (
                            each[1])
                        update_table(update_instance)

                    else:
                        print "_____________________________________________1"
                        insert_data_query = "select %s(%s)" % (form_function, each[1])
                        print  insert_data_query
                        result = single_query(insert_data_query)
                        print "#######"
                        print "Form id " + str(each[2])
                        print result
                        if result == '0' or result == '-1':
                            print 'inside update'
                            update_instance = "update instance_queue set status = 'old' , updated_at = now() where instance_id = %s" % (
                                each[1])
                        if result is None:
                            update_instance = "update instance_queue set status = 'failed' , updated_at = now() where instance_id = %s" % (
                                each[1])
                        update_table(update_instance)
                else:
                    update_instance = "update instance_queue set status = 'function not defined' , updated_at = now() where instance_id = %s" % (
                        each[1])
                    update_table(update_instance)
                    # generate_all_schedule(each[1])
            print "Done!!"
        except Exception, e:
            print "lock error"
            print str(e)
        finally:
            print "#####################task exit###################"
            release_lock()
    else:
        print("Other task is running, skipping")


'''
@periodic_task(run_every=timedelta(seconds=10), name="create_schedule_iom")
def schedule_insert(lock_expire=1200):
    print "Started create_schedule"
    lock_key = 'create_schedule_iom'
    acquire_lock = lambda: cache.add(lock_key, '1', lock_expire)
    release_lock = lambda: cache.delete(lock_key)
    if acquire_lock():
        print "Done!!"
        try:
            instance_query = "select id, instance_id, xform_id from instance_queue where status <> 'new' and coalesce(sch_status,'new')= 'new' order by created_at"

            instance_queue = __db_fetch_values(instance_query)

            print("create_schedule")
            #print(instance_queue)

            for each in instance_queue:
                print "_____________________________________________"
                generate_all_schedule(each[1])
                update_instance = "update instance_queue set sch_status = 'old' , updated_at = now() where instance_id = %s"% (each[1])
                __db_change_query(update_instance)
                
        except Exception, e:
            print "lock error"
            print str(e)
        finally:
            print "#####################task exit###################"
            release_lock()
    else:
        print("Other task is running, skipping")
'''
'''
 Schedule will be generated only when
        1)  In asf_victim table id_status = 'final'
        2)  In asf_case table assaign_to is not null
        3)  Each victim must have rsc 
        4)  Current month will have to be quarter month [3,6,9,12] 
'''


@periodic_task(run_every=timedelta(seconds=10), name="generate_schedule_iom")
def schedule_generate(lock_expire=1200):
    print "Started schedule_generate********************************************"
    lock_key = 'generate_schedule_iom'
    acquire_lock = lambda: cache.add(lock_key, '1', lock_expire)
    release_lock = lambda: cache.delete(lock_key)
    if acquire_lock():
        print "Done!!"
        try:
            # Inactive schedules which have expired
            inactive_schedule()

            sche_date = ''

            expire_date = ''

            sche_def = __db_fetch_values_dict("select * from schedule_def")

            q = "select * from vw_victim where id_status = 'final' and assaign_to is not null and rsc is not null  and victim_id is not null"

            dataset = __db_fetch_values_dict(q)

            for temp in dataset:

                victim_tbl_id = temp['id']

                schedule_user = int(temp['assaign_to'])

                for sd in sche_def:
                    # half_yearly,quarterly
                    sche_type = sd['sche_type']

                    form = sd['form_id']

                    if check_sche_applicable(sche_type):

                        dataset = check_sche_applicable(sche_type)

                        for d in dataset:
                            sche_date = d['schedule_date']
                            expire_date = d['expire_date']
                            prev_sche_month = d['prev_sche_month']

                        prev_sche = check_sche_exist(victim_tbl_id, form, sche_date)

                        if not prev_sche:
                            priority = get_priority_value(victim_tbl_id, form, prev_sche_month)

                            generate_beneficiary_schedule(victim_tbl_id, schedule_user, form, sche_date, expire_date,
                                                          priority)



        except Exception, e:

            print "lock error"

            print str(e)

        finally:
            print "#####################task exit###################"
            release_lock()
    else:
        print("Other task is running, skipping")


def check_sche_exist(victim_tbl_id, form_id, sche_date):
    dataset = __db_fetch_values_dict(
        "select id from schedule where beneficiary_id =" + str(victim_tbl_id) + " and scheduled_form_id =" + str(
            form_id) + " and status='ACTIVE' and (date(schedule_date))::text = '" + sche_date + "'")
    return dataset


def generate_beneficiary_schedule(victim_tbl_id, schedule_user, form, sche_date, expire_date, priority):
    cursor = connections['iom'].cursor()

    created_date = datetime.datetime.now()

    cursor.execute(
        """INSERT INTO public.schedule(beneficiary_id,created_date,status, schedule_date, scheduled_form_id, schedule_user_id,priority, expire_date)VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
        (victim_tbl_id, created_date, 'ACTIVE', sche_date, form, schedule_user, priority, expire_date))

    connections['iom'].commit()


def check_sche_applicable(sche_type):
    q = "select month,prev_sche_month,schedule_date::text,expire_date::text from vw_schedule_time where BTRIM(sche_type,' ') = '" + sche_type + "' and month::text = ( EXTRACT(MONTH FROM current_date))::text"

    dataset = __db_fetch_values_dict(q)

    return dataset


def inactive_schedule():
    expired_sche = __db_fetch_values_dict

    q = "update schedule set status= 'INACTIVE' where id = ANY(select id from schedule where status='ACTIVE' and expire_date < current_date )"

    update_table(q)


def get_priority_value(victim_tbl_id, form, prev_sche_month):
    inactive_schedule = __db_fetch_values_dict("select * from schedule where beneficiary_id=" + str(
        victim_tbl_id) + " and status ='INACTIVE' and scheduled_form_id = " + str(
        form) + " and EXTRACT(MONTH FROM schedule_date)::int = " + str(prev_sche_month))

    priority = 0

    if inactive_schedule:
        priority = 1

    return priority
