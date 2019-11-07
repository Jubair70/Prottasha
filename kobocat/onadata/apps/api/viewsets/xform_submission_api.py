import re
import StringIO
import sys
import json
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from django.http import HttpResponse

from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework import mixins
from rest_framework.authentication import (
    BasicAuthentication,
    TokenAuthentication)
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer

from onadata.apps.logger.models import Instance
from onadata.apps.main.models.user_profile import UserProfile
from onadata.libs import filters
from onadata.libs.authentication import DigestAuthentication
from onadata.libs.mixins.openrosa_headers_mixin import OpenRosaHeadersMixin
from onadata.libs.renderers.renderers import TemplateXMLRenderer
from onadata.libs.serializers.data_serializer import SubmissionSerializer
from onadata.libs.utils.logger_tools import dict2xform, safe_create_instance
from rest_framework import authentication
import logging
from django.contrib.auth import authenticate
from onadata.libs.tasks import instance_parse
from onadata.libs.utils.export_tools import query_mongo
from onadata.apps.viewer.tasks import create_async_export, create_db_async_export

from onadata.apps.scheduling.schedule_utils import create_user_schedule, update_schedule_status
from onadata.apps.scheduling.models.beneficiary_info import insert_beneficiary_info

from onadata.apps.approval.views import update_instance_approval_status
from collections import OrderedDict
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import sys
import os
import zipfile
import pandas

# 10,000,000 bytes
DEFAULT_CONTENT_LENGTH = getattr(settings, 'DEFAULT_CONTENT_LENGTH', 10000000)
xml_error_re = re.compile('>(.*)<')


def is_json(request):
    return 'application/json' in request.content_type.lower()


def dict_lists2strings(d):
    """Convert lists in a dict to joined strings.

    :param d: The dict to convert.
    :returns: The converted dict."""
    for k, v in d.items():
        if isinstance(v, list) and all([isinstance(e, basestring) for e in v]):
            d[k] = ' '.join(v)
        elif isinstance(v, dict):
            d[k] = dict_lists2strings(v)

    return d


def create_instance_from_xml(username, request):
    xml_file_list = request.FILES.pop('xml_submission_file', [])
    xml_file = xml_file_list[0] if len(xml_file_list) else None
    media_files = request.FILES.values()

    return safe_create_instance(username, xml_file, media_files, None, request)


def create_instance_from_json(username, request):
    request.accepted_renderer = JSONRenderer()
    request.accepted_media_type = JSONRenderer.media_type
    dict_form = request.DATA
    submission = dict_form.get('submission')

    if submission is None:
        # return an error
        return [_(u"No submission key provided."), None]

    # convert lists in submission dict to joined strings
    submission_joined = dict_lists2strings(submission)
    xml_string = dict2xform(submission_joined, dict_form.get('id'))

    xml_file = StringIO.StringIO(xml_string)

    return safe_create_instance(username, xml_file, [], None, request)


class XFormSubmissionApi(OpenRosaHeadersMixin,
                         mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
Implements OpenRosa Api [FormSubmissionAPI](\
    https://bitbucket.org/javarosa/javarosa/wiki/FormSubmissionAPI)

## Submit an XML XForm submission

<pre class="prettyprint">
<b>POST</b> /api/v1/submissions</pre>
> Example
>
>       curl -X POST -F xml_submission_file=@/path/to/submission.xml \
https://example.com/api/v1/submissions

## Submit an JSON XForm submission

<pre class="prettyprint">
<b>POST</b> /api/v1/submissions</pre>
> Example
>
>       curl -X POST -d '{"id": "[form ID]", "submission": [the JSON]} \
http://localhost:8000/api/v1/submissions -u user:pass -H "Content-Type: \
application/json"

Here is some example JSON, it would replace `[the JSON]` above:
>       {
>           "transport": {
>               "available_transportation_types_to_referral_facility": \
["ambulance", "bicycle"],
>               "loop_over_transport_types_frequency": {
>                   "ambulance": {
>                       "frequency_to_referral_facility": "daily"
>                   },
>                   "bicycle": {
>                       "frequency_to_referral_facility": "weekly"
>                   },
>                   "boat_canoe": null,
>                   "bus": null,
>                   "donkey_mule_cart": null,
>                   "keke_pepe": null,
>                   "lorry": null,
>                   "motorbike": null,
>                   "taxi": null,
>                   "other": null
>               }
>           }
>           "meta": {
>               "instanceID": "uuid:f3d8dc65-91a6-4d0f-9e97-802128083390"
>           }
>       }
"""
    authentication_classes = (DigestAuthentication,
                              BasicAuthentication,
                              TokenAuthentication)
    filter_backends = (filters.AnonDjangoObjectPermissionFilter,)
    model = Instance
    permission_classes = (permissions.AllowAny,)
    renderer_classes = (TemplateXMLRenderer,
                        JSONRenderer,
                        BrowsableAPIRenderer)
    serializer_class = SubmissionSerializer
    template_name = 'submission.xml'
    print("before create *******************************")

    def send_option(self, request, *args, **kwargs):
        print("inside options *******************************")
        # if request.method.upper() == 'HEAD':
        access_control_headers = request.META['HTTP_ACCESS_CONTROL_REQUEST_HEADERS'];
        response = HttpResponse(200)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST"
        response["Access-Control-Allow-Headers"] = access_control_headers
        response["Access-Control-Allow-Credentials"] = False
        return response

    def dictfetchall(self, cursor):
        desc = cursor.description
        return [
            OrderedDict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()]

    def __db_fetch_values_dict(self, query):
        cursor = connection.cursor()
        cursor.execute(query)
        fetchVal = self.dictfetchall(cursor)
        cursor.close()
        return fetchVal

    def convert_array_json(self, array_json, upto_name=""):
        tmp = []
        for obj in array_json:
            tmp.append(self.kobo_to_formBuilder_json(obj, {}, upto_name))
        return tmp

    def kobo_to_formBuilder_json(self, kobo_json, form_builder_json={}, upto_name=""):
        for key in sorted(kobo_json.keys()):
            # print(key)
            key = str(key)
            if upto_name == "":
                current_hierchical_name = key
            else:
                current_hierchical_name = key[len(upto_name) + 1:]
            split_hierchical_name = current_hierchical_name.split('/')
            if (len(split_hierchical_name) == 1):
                if type(kobo_json[key]) != list:
                    form_builder_json[split_hierchical_name[-1]] = kobo_json[key]
                else:
                    form_builder_json[split_hierchical_name[-1]] = self.convert_array_json(kobo_json[key], key)
            elif (len(split_hierchical_name) > 1):
                tmp = form_builder_json
                for x in split_hierchical_name:
                    if x not in tmp:
                        tmp[x] = {}
                    if x == split_hierchical_name[-1]:
                        if type(kobo_json[key]) != list:
                            tmp[x] = kobo_json[key]
                        else:
                            tmp[x] = self.convert_array_json(kobo_json[key], key)
                    else:
                        tmp = tmp[x]
                        # print(form_builder_json)
        return form_builder_json

    def get_form_attribute(self, request, *args, **kwargs):
        print("inside get_form_attribute *********")
        data = json.loads(request.body)
        print(data)
        form_id = data['id']
        url = data['url']
        username = data['username']
        preset_data = {}
        if 'beneficiary_id' in data:
            preset_data['beneficiary_id'] = data['beneficiary_id']
        if 'iom_reference' in data:
            preset_data['iom_reference'] = data['iom_reference']
        if 'victim_tbl_id' in data:
            preset_data['victim_tbl_id'] = data['victim_tbl_id']
        if 'event_id' in data:
            preset_data['event_id'] = data['event_id']
        # get returnee id
        if 'instance_id' in data:
            instance_id = data['instance_id']
        else:
            instance_id = "-1"
        
        #------------Do not delete -------------#
        # csv_path = '/get_all_csv'
        # if form_id == '716':
        #     csv_path = '/get_group_event_form_csv'
        # csv_url = "http://" + url + "/" + username + csv_path
        #------------Do not delete -------------#

        submission_url = "http://" + url + "/" + username + "/submission"
        csv_url = "http://" + url + "/" + username + "/get_all_csv"
        try:
            qry = "select json::json,uuid,id_string from logger_xform where id =" + str(form_id)
            data = self.__db_fetch_values_dict(qry)[0]
            data['submission_url'] = submission_url
            data['csv'] = csv_url
            if str(instance_id) != "-1":
                qry_data = "select id,json from logger_instance where id =" + str(instance_id)
                print "##################################################################"
                print qry_data
                data_ins = self.__db_fetch_values_dict(qry_data)
                if len(data_ins) > 0:
                    data_json = data_ins[0]['json']
                    print(data_json)
                    data['data_json'] = self.kobo_to_formBuilder_json(data_json,{},"")
            else:
                # get_preloaded_json(form_id,returnee_id)
                # data['data_json']={"beneficiary_id": "JhaRaj001","medical_support": {"disease": "1"}}
                print("in preset")
                data['data_json'] = self.get_preloaded_json(form_id, preset_data)


            print "ASDEXSasa##################################################################1"
            print data['data_json']
            print "ASDEXSasa##################################################################1"
            response = HttpResponse(json.dumps(data))
            print response
            response["Access-Control-Allow-Origin"] = "*"
            return response

        except Exception as e:
            print(e)
            return HttpResponse(status=404)

    def get_preloaded_json(self, form_id, preset_data):
        json = {}

        qry = "select form_id from forms_categories_relation where category_id = any('{1,2,10,20,30,40,50,60,70}')"
        df = pandas.read_sql(qry,connection)
        form_list_for_beneficiary = df.form_id.tolist()

        qry = "select form_id from forms_categories_relation where category_id = any('{100,101,102,200,201,202,300,301,302,400,401,402}')"
        df = pandas.read_sql(qry, connection)
        form_list_for_event = df.form_id.tolist()

        form_list_for_ref = [684]
        # form_list_for_vic_tbl_id = [752]


        print(form_id,form_list_for_beneficiary)
        _list = []
        if int(form_id) in form_list_for_beneficiary:
            json['beneficiary_id'] = str(preset_data['beneficiary_id'])
        if int(form_id) in form_list_for_ref:
            json['iom_mimosa_returnee_id'] = str(preset_data['iom_reference'])
        if int(form_id) in form_list_for_beneficiary:
            json['victim_tbl_id'] = str(preset_data['victim_tbl_id'])


        if int(form_id) in form_list_for_event:
            json['event_id'] = str(preset_data['event_id'])

        print(json)
        return json

    def get_all_csv(self, request, *args, **kwargs):
        print("inside get_all_csv *********")
        username = self.kwargs.get('username')
        # user_path_filename = os.path.join(settings.MEDIA_ROOT, username)
        user_path_filename = os.path.join(settings.MEDIA_ROOT, 'formid-media')
        if not os.path.isdir(user_path_filename):
            os.makedirs(user_path_filename)
        geo_q = "select division_geocode division_code,division_name,district_geocode district_code,district_name,upazila_geocode upazila_code ,upazila_name,union_geocode union_code,union_name from vwunion"
        geo_df = pandas.read_sql(geo_q, connection)
        final_path_event = user_path_filename + '/geo.csv'
        geo_df.to_csv(final_path_event, encoding='utf-8', index=False)

        event_q = "select event_name as event_label, code as event_name from iom_event"
        event_df = pandas.read_sql(event_q, connection)
        final_path_event = user_path_filename + '/event.csv'
        event_df.to_csv(final_path_event, encoding='utf-8', index=False)
        try:
            list_of_files = os.listdir(user_path_filename)

        except Exception as e:
            print(e)
            return HttpResponse(status=404)

        print(list_of_files)
        print(user_path_filename)
        zip_subdir = "itemsetfiles"
        zip_filename = "%s.zip" % zip_subdir
        s = StringIO.StringIO()
        # The zip compressor
        zf = zipfile.ZipFile(s, "w")
        for fpath in list_of_files:
            # Calculate path for file in zip
            fpath = user_path_filename + '/' + fpath
            print(fpath)
            if os.path.exists(fpath):
                fdir, fname = os.path.split(fpath)
                zip_path = os.path.join(zip_subdir, fname)
                print(zip_path)
                # Add file, at correct path
                zf.write(fpath, fname)
        # Must close zip for all contents to be written
        zf.close()
        # Grab ZIP file from in-memory, make response with correct MIME-type
        resp = HttpResponse(s.getvalue(), mimetype="application/x-zip-compressed")
        # ..and correct content-disposition
        resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
        resp["Access-Control-Allow-Origin"] = "*"
        return resp

    # ------------------- Do not delete --------------------#    
    # def get_group_event_form_csv(self,request, *args, **kwargs):
    #     print("inside get_group_event_form_csv *********")
    #     username = self.kwargs.get('username')
    #     user_path_filename = os.path.join(settings.MEDIA_ROOT, username)
    #     user_path_filename = os.path.join(user_path_filename, 'formid-media')
    #     if not os.path.isdir(user_path_filename):
    #         os.makedirs(user_path_filename)
    #     event_q = "select event_name as event_label, code as event_name from iom_event"
    #     event_df = pd.read_sql(event_q, connection)
    #     final_path_event = user_path_filename + '/event.csv'
    #     final_path_geo = user_path_filename + '/geo.csv'
    #     event_df.to_csv(final_path_event, encoding='utf-8', index=False)
    #     filenames = []
    #     filenames.append(final_path_event)
    #     filenames.append(final_path_geo)
    #     zip_subdir = "itemsetfiles"
    #     zip_filename = "%s.zip" % zip_subdir
    #     s = StringIO.StringIO()
    #     zf = zipfile.ZipFile(s, "w")
    #     for fpath in filenames:
    #         if os.path.exists(fpath):
    #             fdir, fname = os.path.split(fpath)
    #             print fdir + "  " + fname
    #             zip_path = os.path.join(zip_subdir, fname)
    #             zf.write(fpath, fname)
    #     zf.close()
    #     resp = HttpResponse(s.getvalue())
    #     resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename
    #     resp["Access-Control-Allow-Origin"] = "*"
    #     return resp
    # ------------------- Do not delete --------------------#

    def create(self, request, *args, **kwargs):
        print("CREATE@@@@@@@@@@@@@@@@@@@")
        username = self.kwargs.get('username')
        password = self.request.GET.get('password')
        if self.request.user.is_anonymous():
            if username is None and password is None:
                # raises a permission denied exception, forces authentication
                self.permission_denied(self.request)
            else:
                user = get_object_or_404(User, username=username.lower())

                profile, created = UserProfile.objects.get_or_create(user=user)

                if profile.require_auth:
                    # raises a permission denied exception,
                    # forces authentication
                    self.permission_denied(self.request)
        elif not username:
            # get the username from the user if not set
            username = (request.user and request.user.username)

        if request.method.upper() == 'HEAD':
            return Response(status=status.HTTP_204_NO_CONTENT,
                            headers=self.get_openrosa_headers(request),
                            template_name=self.template_name)

        is_json_request = is_json(request)

        error, instance = (create_instance_from_json if is_json_request else
                           create_instance_from_xml)(username, request)

        if error or not instance:
            return self.error_response(error, is_json_request, request)

        # print('instance.xform.id_string')
        # print(instance.xform.id_string)
        # print('\n\n\n\n\n')

        ret_msg = ''
        # creating schedule for current submission
        # if instance.xform.id_string == "household_information":
        #    ret_msg = insert_beneficiary_info(username, instance)
        # create_user_schedule(username, instance)
        # else:
        #   dict_form = request.DATA
        #   schedule_id = dict_form.get("scheduleId");
        #   if schedule_id is not None:
        #       update_schedule_status(schedule_id)

        if ret_msg is not None and len(ret_msg) > 0:
            return self.mobile_user_response(instance, ret_msg, request)

        context = self.get_serializer_context()
        serializer = SubmissionSerializer(instance, context=context)
        instance_parse()  # After new db parse implement stop it

        query_dict = {'_id': str(instance.id)}
        options = {
            'group_delimiter': '/',
            'split_select_multiples': True,
            'binary_select_multiples': False,
            # 'meta': meta.replace(",", "") if meta else None,
            'exp_data_typ': 'lbl'
        }

        if instance.xform.db_export:
            # print 'Entered'
            create_db_async_export(instance.xform, 'dbtable', json.dumps(query_dict), False, options)

        update_instance_approval_status(instance.id, 'Submitted')

        response = Response(serializer.data,
                            headers=self.get_openrosa_headers(request),
                            status=status.HTTP_201_CREATED,
                            template_name=self.template_name)
        response["Access-Control-Allow-Origin"] = "*"
        return response

    def mobile_user_response(self, instance, message, request):
        final_msg = {
            'message': _("Successful submission." + message),
            'formid': instance.xform.id_string,
            'encrypted': instance.xform.encrypted,
            'instanceID': u'uuid:%s' % instance.uuid,
            'submissionDate': instance.date_created.isoformat(),
            'markedAsCompleteDate': instance.date_modified.isoformat()
        }
        return Response(final_msg,
                        headers=self.get_openrosa_headers(request),
                        status=status.HTTP_201_CREATED,
                        template_name=self.template_name)

    def error_response(self, error, is_json_request, request):
        print("Error&&&&&&&&&&&&&&&&")
        if not error:
            error_msg = _(u"Unable to create submission.")
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(error, basestring):
            error_msg = error
            status_code = status.HTTP_400_BAD_REQUEST
        elif not is_json_request:
            return error
        else:
            error_msg = xml_error_re.search(error.content).groups()[0]
            status_code = error.status_code

        return Response({'error': error_msg},
                        headers=self.get_openrosa_headers(request),
                        status=status_code)
