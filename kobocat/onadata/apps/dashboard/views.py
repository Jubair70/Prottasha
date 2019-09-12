import decimal
import simplejson
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test

from onadata.apps.usermodule.models import UserModuleProfile
from django.contrib import messages
from django.http import (HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404, render
from onadata.apps.dashboard.forms import *
from django.db.models import ProtectedError
from django.db import connection
from onadata.apps.dashboard.models import *
import json
import re
from django.views.decorators.csrf import csrf_exempt
from onadata.apps.dashboard import utility_functions
from onadata.apps.dashboard.highcharts_config import *
from onadata.apps.dashboard.component_manager import *
from onadata.apps.dashboard.filtering_controls import *
from onadata.apps.dashboard.table_config import *
from django.conf import settings
from django.http import HttpResponse

# from onadata.settings import database_router
import pandas as pd
import xlwt
import os
import AdvancedHTMLParser
from AdvancedHTMLParser.Tags import AdvancedTag



'''
****************************  Dashboard *****************************************
*All Routing URL's Action is Here.
This File contains 3 Sections of Code
1. DYNAMIC DASHBOARD
2. SAVE CURRENT TEMPLATE
3. PROJECT SPECIFIC CODE

@persia
'''





'''
********************         1             ***********************
******************  DYNAMIC DASHBOARD      ***********************
*******************                       ***********************
'''

def index(request):
    """
    Hello World
    :param request:
    :return:
    """
    db_name = connection.settings_dict['NAME']
    print db_name
    return render(request, "dashboard/index.html")


def getDashboardDatatable(query):
    """
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
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    for eachval in fetchVal:
        data_list.append(list(eachval))
    return json.dumps({'col_name': col_names, 'data': data_list})






def getClusteredMap(query):
    """
     MAP JSON
    :param query: SQL Query
    :return: JSON Required For MAPBOX
    **JSON STRUCTURE AS EXAMPLE:
    {
      "type": "FeatureCollection",
      "features": [
        {
          "geometry": {
            "type": "Point",
            "coordinates": [
              89.1296383333333,
              22.6219383333333
            ]
          },
          "type": "Feature",
          "properties": {
            "name_wmg": "Rallia",
            "Zone": "Khulna",
            "District": "Khulna"
          }
        },
        {
          "geometry": {
            "type": "Point",
            "coordinates": [
              89.4156049999999,
              22.8005183333333
            ]
          },
          "type": "Feature",
          "properties": {
            "name_wmg": "Bunarabad Goriardanga",
            "Zone": "Khulna",
            "District": "Khulna"
          }
        }
      ]
    }
    """
    jsondata={ "type": "FeatureCollection", "features": []}
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    for eachval in fetchVal:
        if eachval[0] is not None:
	    #eachjson=json.loads(json.dumps(eachval[0]))
            eachjson=json.loads(json.dumps(eachval[0]))
            jsondata["features"].append(eachjson)
    return jsondata


def getCardData(query):

    jsondata={}
    cursor = connection.cursor()
    #print query
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    for eachval in fetchVal:
        if eachval[0] is not None:
	    #eachjson=json.loads(json.dumps(eachval[0]))
            #print "CARDS#######################3"
            #print eachval
            jsondata['number'] = eachval[0]
            jsondata['details'] = eachval[1]
            if len(eachval)>=3:
                jsondata['percentage'] = str(eachval[2])
            else: 
                jsondata['percentage'] = ''
    return jsondata

@csrf_exempt
def generate_component_handler(request, graph_id):
    """
     AJAX Request Handler: Component generate
     Router of Component Generation
    :param request:
    :param graph_id: Component ID from DashboardGenerator table
    :return: JSON for creating respective component
    """
    dashboardGenerator = DashboardGenerator.objects.filter(id=graph_id).first()
    #print dashboardGenerator
    jsondata = {}
    if dashboardGenerator.content_type == 0:  # GRAPH
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            highchartsConfig = HighchartsConfig(graph_id)
            jsondata = highchartsConfig.execute_query(dashboardGenerator.chart_type, query)


            #jsondata = execute_query(dashboardGenerator.chart_type.id, query)
        elif dashboardGenerator.datasource_type == "2":  # 2 = URL
            # TODO: URL will Return a json
            jsondata = HttpResponseRedirect(dashboardGenerator.datasource)
        else:  # 3 = JSON
            # TODO: URL will Return a json
            jsondata = dashboardGenerator.datasource

    elif dashboardGenerator.content_type == 1:  # Table
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            #chart object
            appearance = sjson.loads(dashboardGenerator.chart_object)
            #filtered query
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            tableConfig= TableConfig(graph_id,request, appearance);
            jsondata = tableConfig.execute_query(query) #getDashboardDatatable(query)
            #print " (**************** TABLE DATA ***************8 ",jsondata
            return HttpResponse(jsondata)
        else:  # 2 = URL
            # TODO: URL will Return a json
            jsondata = json.dumps(HttpResponseRedirect(dashboardGenerator.datasource))
    elif dashboardGenerator.content_type == 4:  # cards
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            #chart object
            appearance = sjson.loads(dashboardGenerator.chart_object)
            #filtered query
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            # tableConfig= TableConfig(graph_id,request, appearance);
            # jsondata = tableConfig.execute_query(query) #getDashboardDatatable(query)
            jsondata = getCardData(query)
            #print " (**************** TABLE DATA ***************8 ",jsondata
            return HttpResponse(json.dumps(jsondata))
        else:  # 2 = URL
            # TODO: URL will Return a json
            jsondata = json.dumps(HttpResponseRedirect(dashboardGenerator.datasource))
    else:  # MAP
        if dashboardGenerator.datasource_type == "1":  # 1 = QUERY
            query = get_filtered_query(request.POST, dashboardGenerator.datasource)
            return HttpResponse(json.dumps(getClusteredMap(query)))

        elif dashboardGenerator.datasource_type == "2":  # 2 = URL
            # TODO: URL will Return a json
            jsondata = HttpResponseRedirect(dashboardGenerator.datasource)
        else:  # Static JSON
            jsondata = dashboardGenerator.datasource
        return HttpResponse(jsondata)

    return HttpResponse(jsondata, content_type="application/json")




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

@csrf_exempt
def on_change_element(request):
    """
    On change for Single Select Cascading
    :param request:
    :return: JSON Data of newly selected option
    """
    cursor = connection.cursor()
    test_data = {}
    control_id = request.POST.get("control_id")
    cascaded_elements = DashboardControlsCascaded.objects.filter(cascaded_parent_id=control_id)
    print "here in request"
    print request.POST
    for elements in cascaded_elements:
        element = elements.cascaded_child
        print element
        element_datasource = element.datasource
        cursor.execute(get_filtered_query(request.POST, element_datasource))
        row = cursor.fetchone()
        temp_data = utility_functions.unicodoToString(row[0])
        test_data[element.control_id] = {'control_type':element.control_type,'data':temp_data}

    #print utility_functions.unicodoToString(test_data)
    jsondata = {"jsondata": test_data}
    print jsondata
    return HttpResponse(json.dumps(jsondata), content_type="application/json")


@csrf_exempt
def on_change_multiple_select(request):
    """
    On change for Multiple Select Cascading
    :param request:
    :return: JSON Data of newly selected options
    """
    "id of changed multiselector"
    print "onchange"
    control_id = request.POST.get("control_id")
    print "changed val"
    print request.POST
    controls_js = ''
    coated_param_val = []
    cursor = connection.cursor()
    data = {}
    test_data = {}
    cascaded_element = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_id)
    cascaded_elements =DashboardControlsCascaded.objects.filter(cascaded_parent_id=control_id)

    for elements in cascaded_elements:
        element = elements.cascaded_child
        element_datasource = element.datasource
        cursor.execute(get_filtered_query(request.POST,element_datasource))
        row = cursor.fetchone()
        temp_data = utility_functions.unicodoToString(row[0])
        test_data[element.control_id] = {'control_type':element.control_type,'data':temp_data}
    # print utility_functions.unicodoToString(test_data)
    jsondata = {"jsondata": test_data}
    print "#################### json dat data change ###########################"
    print jsondata
    return HttpResponse(json.dumps(jsondata), content_type="application/json")


def on_change_element_pre(request):
    """
    On change for Single Select Cascading
    :param request:
    :return: JSON Data of newly selected option
    """
    control_id = request.POST.get("control_id")
    changed_val = request.POST.get("changed_val")
    #print 'change'
    #print changed_val
    #print control_id
    ds_data =''
    controls_js = ''
    cascaded_control_id = ''
    cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_id).first()
    if cascaded_elements is not None:
    # parent_div_id = cascaded_elements.allignment + '_' + str(cascaded_elements.id)
        cursor = connection.cursor()
        onchange_function_js = ""
        #print cascaded_elements.datasource.replace("@id", changed_val)
        cursor.execute(cascaded_elements.datasource.replace("@id", changed_val))
        cascaded_elements_next = DashboardControlsGenerator.objects.filter(cascaded_by_id=cascaded_elements.id).first()
        if cascaded_elements_next is not None:
            onchange_function_js = 'onChangeElement(' + str(control_id) + ');'
        row = cursor.fetchone()

        ds_data = utility_functions.unicodoToString(row[0])
        cascaded_control_id = cascaded_elements.control_id
        #print type(ds_data)
    
    jsondata = {"jsondata": ds_data, "element":cascaded_control_id }

    return HttpResponse(json.dumps(jsondata), content_type="application/json")


def on_change_multiple_select_pre(request):
    """
    On change for Multiple Select Cascading
    :param request:
    :return: JSON Data of newly selected options
    """
    "id of changed multiselector"
    control_id = request.POST.get("control_id")
    #"changed values"
    changed_vals = request.POST.getlist("changed_val[]")
    #print "changed val"
    #print changed_vals
    controls_js = ''

    coated_param_val = []

    ################# change zinia ################
    if not changed_vals:
       changed_val = 'NULL'
    else:
        for val in changed_vals:
            coated_param_val.append("'" + val + "'")
        "concatenated changed values"
        changed_val = ",".join([str(item) for item in coated_param_val])
    cursor = connection.cursor()
    "all elements cascaded by control id"
    "Testing Data"
    data = {}

    test_data = {}
    cascaded_element = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_id)
    for element in cascaded_element:
        element_datasource = element.datasource
        if changed_val == 'NULL':
            cursor.execute(element_datasource.replace("@id", "NULL"))
        else:
            cursor.execute(element_datasource.replace("@id",   changed_val ))
        row = cursor.fetchone()
        temp_data = utility_functions.unicodoToString(row[0])
        test_data[element.control_id] = temp_data

        elements_next = DashboardControlsGenerator.objects.filter(cascaded_by_id=element.id)
        if elements_next is not None:
            for next in elements_next:
                cursor.execute(next.datasource.replace("@id", "NULL"))
                row = cursor.fetchone()
                test_data[next.control_id] =  utility_functions.unicodoToString(row[0])


    #print utility_functions.unicodoToString(test_data)
    # print json.dumps(cascaded_elements), '  JSON  '
    # controls_js += '\nvar jsondata_' + str(cascaded_elements.id) + '=JSON.parse(' + json.dumps(row[ 0]) + ');\n dropdownControlCreate("' + cascaded_elements.control_id + '","' + parent_div_id + '","' + cascaded_elements.control_name + '","' + cascaded_elements.control_label + '","' + onchange_function_js + '", jsondata_' + str(cascaded_elements.id) + ' );'
    # jsondata={"jsondata":row[0], "element": cascaded_elements.control_id ,"parent_div_id": parent_div_id , "control_name": cascaded_elements.control_label ,"control_label": cascaded_elements.control_name, "has_cascaded_element":onchange_function_js  }
    jsondata = {"jsondata": test_data}
    #print "#################### json dat data change ###########################"
    #print jsondata
    return HttpResponse(json.dumps(jsondata), content_type="application/json")

################# change zinia ################


class GenerateDashboard:
    """
    ..........................
    """
    def __init__(self,username):
        self.username = username
        self.parser = AdvancedHTMLParser.AdvancedHTMLParser()
        self.nav_list = None
        self.nav_content = None
        self.js_code =""
        self.isActive = " active "


    def generate_inner_components(self,leaf_data):
        """
        Generate Filtering fields, graph, table and customized component's JS AND HTML
        :param leaf_data: component id
        :return: N/A, Set value in class variable
        """
        leaf_id = str(leaf_data.id)

        #GEt Tab Title if exists
        appearance = {}
        #change for TUP
        if leaf_data.appearance is not None:
            #print leaf_data.appearance
            appearance = json.loads(leaf_data.appearance)
	    #font-weight: bold !important;
        tab_title = " "
        if "title" in appearance:
            tab_title = "<div class='dashboard-full-width'><h2 class='dashboard-title' style=''>"+appearance["title"]+"</h2></div>";

        # Creating Filtering Control for each tab
        filteringControl = FilteringControls(leaf_data.id,self.username)
        controls_info = filteringControl.get_content()

        # Creating CHART/Component for each tab
        componentManager = ComponentManager(leaf_data.id)
        chart_content = componentManager.get_chart_content()
        chart_component_div = self.parser.getElementById('container_' + leaf_id)
        chart_component_div.appendInnerHTML("<div>"+tab_title+chart_content['chart_html']+"</div>")

        # JS Code
        #Initialize Current TAB Function and filtering submission function
        #***For String Format: {{ used instead of single {
        self.js_code +="""
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
            {js_chart_calling_function_with_param}
            {control_js_after_form_submit}

        }} );
        """.format(leaf_id=leaf_id,controls_js=controls_info['controls_js'], js_chart_calling_function_with_param=chart_content['js_chart_calling_function_with_param'], control_js_after_form_submit=controls_info['control_js_after_form_submit'],control_js_trigger=controls_info['control_js_trigger'])
        #,js_chart_calling_function=chart_content['js_chart_calling_function']

        if self.isActive == " active ":
            self.js_code += 'init_tab_' + leaf_id + '(); \n'
            self.isActive = ''


    def get_dashboard(self):
        """
         It's generating the Main Skeleton (Navigation Bar and container for holding graph/table )of Page and
         Required JS for making components
        :return:{'html_code': self.parser.getHTML(), 'js_code': self.js_code}
        """

        #Main Skeleton
        self.parser.parseStr("""
            <div id="parent_body" class="portlet-body">
                <ul id="nav_list" class="nav nav-pills">
                <!-- Navigation Bar: Two Level Tree -->
                </ul>
                <div id="nav_content" class="tab-content">
                <!-- Navigation Bar Link Content -->
                </div>
            </div>
            """)
        self.nav_list = self.parser.getElementById('nav_list')
        self.nav_content = self.parser.getElementById('nav_content')
        #print self.nav_list
        #Get Navigation Bar Information from DB
        #Get only Parent Link 1st
        navigationBarParent = DashboardNavigationBar.objects.filter(parent_link_id__isnull=True).order_by('order')
        inner_tab_parser = AdvancedHTMLParser.AdvancedHTMLParser()
        #Iterate through all Parent Link
        for eachrow in navigationBarParent:
            #Get child Link of current parent
            navigationBarChild = DashboardNavigationBar.objects.filter(parent_link_id=eachrow.id).order_by('order')
            inner_list = AdvancedTag('li')
            inner_list.setAttributes({'class': self.isActive})
            #if: Parent has no child
            if not navigationBarChild:
                #1st Level: make current parent as leaf
                #print self.inner_list

                self.isActive = ""
                inner_list = self.createLeaf(eachrow, inner_list)
                self.generate_inner_components(eachrow)
            # Otherwise: Parent has some child
            else:
                #As current parent has child, It need to show a dropdown
                inner_list.setAttributes({'class':"dropdown "+self.isActive})
                #insert a Link <a>
                newLink = AdvancedTag('a')
                newLink.setAttributes({
                    'class':'dropdown-toggle ',
                    'data-toggle': 'dropdown',
                    'href':'#',
                    'id': 'tabDrop_'+ str(eachrow.id)
                })
                newLink.appendInnerHTML(eachrow.link_name)
                #Insert a dropdown icon <i>
                newIcon=AdvancedTag('i')
                newIcon.setAttributes({"class":"fa fa-angle-down"})

                #Append Icon with Link
                newLink.appendNode(newIcon)
                # Append Icon with Link
                inner_list.appendNode(newLink)

                #Now Create Inner List for little children :P
                inner_nav_list = AdvancedTag('ul')
                inner_nav_list.setAttributes({
                    'class': 'dropdown-menu',
                    'role': "menu",
                    'aria-labelledby': 'tabDrop_' + str(eachrow.id)
                })
                for eachchildrow in navigationBarChild:
                    inner_nav_list_item = AdvancedTag('li')
                    print self.isActive
                    inner_nav_list_item.setAttributes({'class': self.isActive})
                    #2nd Level: Create Leaf
                    inner_nav_list_item =self.createLeaf(eachchildrow,inner_nav_list_item)
                    inner_nav_list.appendNode(inner_nav_list_item)
                    self.generate_inner_components(eachchildrow)
                    self.isActive=""
                #Append little children List with Parent List
                inner_list.appendNode(inner_nav_list)
            #Append Parent List with Main Navivagation Bar
            self.nav_list.appendNode(inner_list)

        context={'html_code': self.parser.getHTML(), 'js_code': self.js_code}
        return context

    # Change by Zinia
    def get_dashboard_page(self, id):
        """
         It's generating the Main Skeleton (Navigation Bar and container for holding graph/table )of Page and
         Required JS for making components
        :return:{'html_code': self.parser.getHTML(), 'js_code': self.js_code}
        """

        #Main Skeleton
        self.parser.parseStr("""
            <div id="parent_body" class="portlet-body">

                <div id="nav_content" >
                <div id="accordion" >
                <!-- Navigation Bar Link Content -->
                <form id="form_{leaf_id}">
                </form>
                </div>
                </div>
            </div>
            """.format(leaf_id=str(id)))

        self.nav_content = self.parser.getElementById('form_'+str(id))
        #print self.nav_list
        #Get Navigation Bar Information from DB
        #Get only Parent Link 1st
        navigationBarParent = DashboardNavigationBar.objects.filter(id = id).first()
        self.skeleten_content(navigationBarParent)
        self.generate_inner_components(navigationBarParent)
        #print self.parser.getHTML()
        context={'html_code': self.parser.getHTML(), 'js_code': self.js_code}
        return context

    def skeleten_content(self,leaf_data):
        leaf_id = str(leaf_data.id)
        # < button
        # type = "button"
        #
        # class ="btn btn-secondary  red" > < i class ="glyphicon glyphicon-search" > < / i > < / button >
        tab_content_skeleton = """


                           <form id="form_{leaf_id}" >
                              <div class="row">
                        <div id="toggle_left_{leaf_id}" style="display: none; position:fixed; z-index: 20; left: -5px" class="input-group" onclick="openNav('left_{leaf_id}',this);"  >
                            <div class="input-group-btn"  style="text-align: left; ">
                                <button type="button" class="btn btn-secondary"><i class="fa fa-search"></i></button>
                                <button type="button" class="btn btn-secondary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                  <i id="icon_caret_left_{leaf_id}" class="fa fa-caret-right" aria-hidden="true"></i> <i id="icon_cross_left_{leaf_id}" style="display:none;" class=" fa fa-times" aria-hidden="true"></i>
                                </button>
                                <!--
                                <div class="dropdown-menu" id="floating_filtering_body_{leaf_id}"  >
                                    TODO: ADD ALL Filtering Here If Possible
                                </div>
                                -->
                            </div>
                        </div>






                    </div>
                      <div class ="row">
                        <div class ="" style="">
                        <div  id="toggle_right_{leaf_id}" onclick="openNav('right_{leaf_id}',this);"  >
                            <div  class="input-group-btn float-filter"  style="text-align: right;position:fixed;">
                                <button type="button" class="btn btn-secondary red"><i class="fa fa-search"></i></button>
                                <button type="button" class="btn btn-secondary red dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                <i id="icon_caret_right_{leaf_id}" class="fa fa-caret-left" aria-hidden="true"></i> <i id="icon_cross_right_{leaf_id}" style="display:none;" class=" fa fa-times" aria-hidden="true"></i>
                                </button>
                                <!--
                                <div class="dropdown-menu" id="floating_filtering_body_{leaf_id}"  >
                                    TODO: ADD ALL Filtering Here If Possible
                                </div>
                                -->
                            </div>
                        </div>

                        <div id = "filter_right_{leaf_id}" >
                            <div class = "mpower-section right sidenav sidenav_right" id="right_{leaf_id}"  style="position:fixed;">
                            <div class = "portlet-title-sub reset_button" style="text-align:right;">

                                <div class="reload">Filter Reset
                                    <button type="button" class="btn btn-default btn-sm right reset-button" onclick="reset_button_{leaf_id}();">
                                        <span class="glyphicon glyphicon-refresh"></span>
                                    </button>
                                </div>
                            </div>


                            <!-- SLIDING FILTERING BAR DISABLE <a href="javascript:void(0)" class="closebtn " onclick="closeNav('right_{leaf_id}',this);">&times;</a> -->
                            </div>


                        </div>
                        </div>

                      </div>
                      <div  class="" id="flex_div_{leaf_id}" >
                         <!-- Left Section Filtering-->
                         <div  id="left_{leaf_id}" class="mpower-section left sidenav sidenav_left" style=" " >
                            <!-- SLIDING FILTERING BAR DISABLE  <a href="javascript:void(0)" class="closebtn" onclick="closeNav('left_{leaf_id}',this);">&times;</a>-->
                         </div>

                        <!-- Middle Section-->
                         <div  id="middle_{leaf_id}" class=" " >
                            <!-- Middle Section Filtering-->
                             <div class="mpower-section middle-top">
                                <div class="form-group"  id="top_{leaf_id}"> </div>
                            </div>
                             <!-- Middle Section CONTAINER-->
                             <div data-load="unloaded" class="" id="container_{leaf_id}"></div>
                         </div>
                         <!-- Right Section Filtering-->
                      <div class="row">
                          <!-- <div class="  customizer border-left-blue-grey border-left-lighten-4 d-none d-xl-block input-group-btn mpower-section right sidenav sidenav_right" style="text-align: center;">

                            <button id = "toggle_right_{leaf_id}" onclick="openNav('right_{leaf_id}',this);" type="button" class="btn btn-secondary customizer-toggle bg-danger box-shadow-3t " data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"> Filter
                                      <i id="icon_caret_right_{leaf_id}" class="fa fa-caret-left" aria-hidden="true"></i> <i id="icon_cross_right_{leaf_id}" style="display:none;" class=" fa fa-times" aria-hidden="true"></i>
                            </button>
                            <div class = "customizer-content" id="right_{leaf_id}" >


                            </div>
                            </div>
                          </div> -->

                      </div>
                      </div>
                           </form>

                        """.format(leaf_id=leaf_id)
        #print tab_content_skeleton
        self.nav_content.appendInnerHTML(tab_content_skeleton)

    def createLeaf(self ,leaf_data, nav_leaf):
        """
         Creating Leaf of Navigation Bar Tree with Last link
        :param newList_li (List that will hold leaf)
        :param leaf_data (Leaf Data from database)
        :return:
        """
        leaf_id = str(leaf_data.id)

        newLink = AdvancedTag('a')
        newLink.setAttributes({
            'data-toggle': 'tab',
            'onclick': 'init_tab_' + leaf_id + '();',
            'href': '#tab_' + leaf_id
        })
        newLink.appendInnerHTML(leaf_data.link_name)
        # Append leaf Link with it's parent
        nav_leaf.appendNode(newLink)


        tab_content_skeleton = """
                <div><div class="tab-pane {isActive}" id="tab_{leaf_id}"  >

                   <form id="form_{leaf_id}" >
                      <div class="row">
                        <div id="toggle_left_{leaf_id}" style="display: none; position:fixed; z-index: 20; left: -5px" class="input-group" onclick="openNav('left_{leaf_id}',this);"  >
                            <div class="input-group-btn"  style="text-align: left; ">
                                <button type="button" class="btn btn-secondary"><i class="fa fa-search"></i></button>
                                <button type="button" class="btn btn-secondary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                  <i id="icon_caret_left_{leaf_id}" class="fa fa-caret-right" aria-hidden="true"></i> <i id="icon_cross_left_{leaf_id}" style="display:none;" class=" fa fa-times" aria-hidden="true"></i>
                                </button>
                                <!--
                                <div class="dropdown-menu" id="floating_filtering_body_{leaf_id}"  >
                                    TODO: ADD ALL Filtering Here If Possible
                                </div>
                                -->
                            </div>
                        </div>



                        <div  class="input-group  "  id="toggle_right_{leaf_id}" onclick="openNav('right_{leaf_id}',this);" style="display: none; position:fixed; z-index: 20; left: 285px;"  >
                            <div  class="input-group-btn"  style="text-align: right; width:1000px; ">
                                <button type="button" class="btn btn-secondary"><i class="fa fa-search"></i></button>
                                <button type="button" class="btn btn-secondary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                  <i id="icon_caret_right_{leaf_id}" class="fa fa-caret-left" aria-hidden="true"></i> <i id="icon_cross_right_{leaf_id}" style="display:none;" class=" fa fa-times" aria-hidden="true"></i>
                                </button>
                                <!--
                                <div class="dropdown-menu" id="floating_filtering_body_{leaf_id}"  >
                                    TODO: ADD ALL Filtering Here If Possible
                                </div>
                                -->
                            </div>
                        </div>


                    </div>
                      <div  class="flex " id="flex_div_{leaf_id}" >
                         <!-- Left Section Filtering-->
                         <div  id="left_{leaf_id}" class="mpower-section left sidenav sidenav_left" style="position:fixed; " >
                            <!-- SLIDING FILTERING BAR DISABLE  <a href="javascript:void(0)" class="closebtn" onclick="closeNav('left_{leaf_id}',this);">&times;</a>-->
                         </div>
                         <!-- SLIDING FILTERING BAR DISABLE
                         <a  href="#" style="display:none;" id="left_link_{leaf_id}" onclick="openNav('left_{leaf_id}');">
                         <i class="fa fa-filter"></i></a>
                         -->

                        <!-- Middle Section-->
                         <div  id="middle_{leaf_id}" class="mpower-section middle " >
                            <!-- Middle Section Filtering-->
                             <div class="mpower-section middle-top">
                                <div class="form-group"  id="top_{leaf_id}"> </div>
                            </div>
                             <!-- Middle Section CONTAINER-->
                             <div data-load="unloaded" class="middle-container" id="container_{leaf_id}"></div>
                         </div>

                         <!-- Right Section Filtering-->
                         <div id="right_{leaf_id}" class="mpower-section right  sidenav sidenav_right" style="position:fixed; ">
                            <!-- SLIDING FILTERING BAR DISABLE <a href="javascript:void(0)" class="closebtn " onclick="closeNav('right_{leaf_id}',this);">&times;</a> -->
                         </div>
                         <!-- SLIDING FILTERING BAR DISABLE
                         <a href="#" id="right_link_{leaf_id}" onclick="openNav('right_{leaf_id}','container_{leaf_id}');" style="display:none;">
                            <i class="fa fa-filter"></i>
                         </a>
                         -->
                      </div>
                   </form>
                </div></div>
                """.format(leaf_id=leaf_id,isActive=self.isActive)


        self.nav_content.appendInnerHTML(tab_content_skeleton)

        return nav_leaf


def generate_saved_report(request, id):
    """
    Entry Point
    Generate Report From saved Data
    :param request:
    :param id:
    :return:
    """
    json_output = {}
    if id == "0":
        generateDashboard = GenerateDashboard()
        ready_dashboard = generateDashboard.get_dashboard()
        json_output = {'html_code': ready_dashboard["html_code"], 'js_code': ready_dashboard["js_code"]}

    else:
        loaded_dashboard_instance = DashboardLoader.objects.get(pk=id)
        json_output = {'html_code': loaded_dashboard_instance.html_code, 'js_code': loaded_dashboard_instance.js_code}

    return render(request, "dashboard/generate_saved_report.html", json_output)

@login_required
def generate_report(request, id):
    """
    Entry Point
    Generate Report From saved Data
    :param request:
    :param id:
    :return:
    """
    json_output = {}
    if id != "0":
        # user object
        user = request.user
        # user profile object

        generateDashboard = GenerateDashboard(user.username)
        ready_dashboard = generateDashboard.get_dashboard_page(id)
        """$('#toggle_right_%s').BootSideMenu({
          side: "right",
          // animation speed
          duration: 500,
          // restore last menu status on page refresh
          remember: false,
          // auto close
          autoClose: true,
          // push the whole page
          pushBody: true,
          // close on click
          closeOnClick: true,
          // width
          width: "300px"

      });"""
        #print
        js_code = """$(document).ready(function (){  init_tab_%s(); }); """%(str(id))
        js_code = js_code + ready_dashboard["js_code"]
        json_output = {'html_code': ready_dashboard["html_code"], 'js_code': js_code}


    return render(request, "dashboard/generate_saved_report.html", json_output)




'''
********************         2             ***********************
******************  SAVE CURRENT TEMPLATE ***********************
*******************                       ***********************
'''


def save_loaded_dashboard(request):
    """
    Save Current Dynamic Dashboard
    :param request:
    :return:
    """

    generated_saved_report = generate_dynamic_report(request)
    if request.method == "POST":

        try:
            dashboardLoader = DashboardLoader()
            dashboardLoader.html_code = generated_saved_report['html_code']
            dashboardLoader.js_code = generated_saved_report['js_code']
            dashboardLoader.name = request.POST.get("dashboard_name")
            dashboardLoader.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> Dashboard Saved Successfully',
                             extra_tags='alert-success crop-both-side')
        except:
            messages.success(request, '<i class="fa fa-cross-circle"></i> Dashboard saving failed.',
                             extra_tags='alert-danger crop-both-side')
        return index(request)

def getDatatable(query):
    data_list = []
    col_names = []
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall();
    col_names = [i[0] for i in cursor.description]
    col_names.append('Action')
    for eachval in fetchVal:
        delete_button = '<a class="delete-program-item tooltips" data-placement="top" href="#" data-original-title="Delete"  onclick="delete_entity(' + str(
            eachval[0]) + ')"><i class="fa fa-2x fa-trash-o"></i></a>'
        # delete_button = ''
        edit_button = '<a class="tooltips" data-placement="top" data-original-title="Edit Program" href="#" onclick="edit_entity(' + str(
            eachval[0]) + ');"><i class="fa fa-2x fa-pencil-square-o"></i></a>' + ' ' + delete_button
        eachval = eachval + (edit_button,)
        data_list.append(list(eachval))
    return json.dumps({'col_name': col_names, 'data': data_list})



def show_template_get_json(request):
    """
    Show List of Saved Template
    :param request:
    :return:
    """
    datajson = getDatatable(
        'select id ,\'<a href="/dashboard/generate_saved_report/\' || id::text || \'/">\' || name ::text || \'</a> \' as name , created_at::text as Date from dashboard_loader order by created_at desc')
    return HttpResponse(datajson, content_type='application/json')


def update_loaded_dashboard(request, loaded_db_id):
    """
    Update loaded_dashboard
    :param request:
    :param loaded_db_id:
    :return:
    """
    LOADED_DASHBOARD_ID = loaded_db_id
    if request.method == "GET":
        loaded_dashboard_form_instance = DashboardLoader.objects.filter(id=LOADED_DASHBOARD_ID).first()
        loaded_dashboard_form = DashboardLoaderUpdateForm(instance=loaded_dashboard_form_instance)
        context = {
            "loaded_dashboard_form": loaded_dashboard_form,
            "LOADED_DASHBOARD_ID": LOADED_DASHBOARD_ID
        }
    if request.method == "POST":
        loaded_dashboard_form_instance = DashboardLoader.objects.filter(id=loaded_db_id).first()
        loaded_dashboard_form = DashboardLoaderUpdateForm(data=request.POST, instance=loaded_dashboard_form_instance)
        if loaded_dashboard_form.is_valid():
            loaded_dashboard_form_instance = loaded_dashboard_form.save()
            messages.success(request, '<i class="fa fa-check-circle"></i> Dashboard Saved Successfully',
                             extra_tags='alert-success crop-both-side')
            return index(request)
        else:
            messages.success(request, '<i class="fa fa-cross-circle"></i> Dashboard saving failed. Please Try again.',
                             extra_tags='alert-danger crop-both-side')
            context = {
                "loaded_dashboard_form": loaded_dashboard_form,
                "LOADED_DASHBOARD_ID": LOADED_DASHBOARD_ID
            }
            return render(request, "dashboard/update_loaded_dashboard.html", context, status=500);
    return render(request, "dashboard/update_loaded_dashboard.html", context);


def delete_loaded_dashboard(request, loaded_db_id):
    """
    Delete Loaded Dashboard
    :param request:
    :param loaded_db_id:
    :return:
    """
    loaded_dashboard_instance = DashboardLoader.objects.get(pk=loaded_db_id)
    try:
        loaded_dashboard_name = loaded_dashboard_instance.name;
        loaded_dashboard_instance.delete()
        data = getAjaxMessage("success",
                              '<i class="fa fa-check-circle"></i> Dashboard -' + loaded_dashboard_name + ' has been deleted successfully!')
    except ProtectedError:
        loaded_dashboard_del_message = "Dashboard could not be deleted."
        data = getAjaxMessage("danger", loaded_dashboard_del_message)
    return HttpResponse(simplejson.dumps(data), content_type="application/json")



'''
********************         3           ***********************
******************   PROJECT SPECIFIC CODE      ***********************
*******************       BLUE GOLD             ***********************
'''



def get_json(query,coulumns):
    df = pd.read_sql(query,connection)
    df = df.T
    df['x'] = df.index
    df = df[df.columns[::-1]]
    df.columns = coulumns
    df = df.to_json(orient='split')
    return df




def get_wmg_tracker_Excel(request,json_data):

    data = json_data
    tables = data.get('data')
    wb = xlwt.Workbook()
    ws = wb.add_sheet("My Sheet", cell_overwrite_ok=True)
    countLine = 0;
    for t in tables:
        ws.write(countLine, 0, t[1])
        subtables = data.get('subtables')
        table = subtables.get(t[1])
        countLine+=2

        table = json.loads(table)
        columns = table.get('columns')
        colcount= len(columns)
        for j, col in enumerate(columns):
            ws.write(countLine, j, col)
        countLine+=1
        tabledata = table.get('data')
        for rowdata in tabledata:
            colLine=0
            for row in rowdata:
                ws.write(countLine, colLine, row)
                colLine+=1
            countLine+=1
        countLine+=2

    #current_user = UserModuleProfile.objects.filter(user=user)
    user_path_filename = os.path.join(settings.MEDIA_ROOT, request.user.username)
    user_path_filename = os.path.join(user_path_filename, "export_wmg_tracker")
    if not os.path.exists(user_path_filename):
        os.makedirs(user_path_filename)

    filename=os.path.join(user_path_filename, "WMG_Summery_Tracker_Report.xls")
    wb.save(filename)
    return filename



def getExcel(request):
    """
    GET Excel of Table
    :param request:
    :return:
    """
    #print "################"
    #print request
    #print request.GET.get('path')
    path_filename = request.GET.get('path')
    file_path = os.path.join(settings.MEDIA_ROOT, path_filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    return HttpResponse(status=404)

def getWMGTrackerExcel(request):
    """
    GET Excel of WMG Tracker Summery Report
    :param request:
    :return:
    """
    data = get_wmg_tracker_report_json(request.GET)
    path_filename = get_wmg_tracker_Excel(request,data)
    file_path = os.path.join(settings.MEDIA_ROOT, path_filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    return HttpResponse(status=404)


def get_wmg_tracker_report_json(post_dict):
    """
    Returnong JSON for get_wmg_tracker_report
    :param request:
    :return: json
    """
    filtering = " where (zon::integer in (@zone) OR (@zone) IS NULL ) and (district::integer in (@geo_district) OR (@geo_district) IS NULL )  and (polder::text in (@polder) OR (@polder) IS NULL ) "
    sections_name = ["Results of", "WMG Funds", "Use of WMG Funds", "Type of Business investment", "Training Course",
                     "Modules/ Topices for Learning Session", "Name of Crops",
                     "Initiatives Activities for Horizantal Learnng", "Name of Technologies and new parctices adopted",
                     "Collective Action for Economic Activities"]
    headers = []
    for names in sections_name:
        headers.append(["", names])
    headers_col = ["WMG Summary Report"]

    subtables = {}

    # Results of
    # View:: vwwmg_tracker_1_2
    section = sections_name[0]
    query = get_filtered_query(post_dict,
                               'select count( ta_ffs_no) as "No. of TA-FFS conducted", sum(ta_ffs_male) as "No. of enrolled TA-FFS male members"   ,  sum(ta_ffs_female) as "No. of enrolled TA-FFS female members"   ,  ((sum(ta_ffs_female)/(sum(ta_ffs_female)+sum(ta_ffs_male)))*100) as "% of TA FFS female members"   ,  count(dae_ffs_no) as "No. of DAE-FFS conducted"   ,  sum(dae_ffs_male) as "No. of enrolled DAE-FFS male members"   ,  sum(dae_ffs_female) as "No. of enrolled DAE-FFS female members"   ,  ((sum(dae_ffs_female)/(sum(dae_ffs_male)+sum(dae_ffs_female)))*100) as "% of DAE FFS female members"   ,  count(mfs_no) as "No. of MFS conducted"   ,  sum(mfs_male) as "No. of enrolled MFS male members"   ,  sum(mfs_female) as "No. of enrolled MFS female members"   ,  ((sum(mfs_female)/(sum(mfs_male)+sum(mfs_female)))*100) as "% of MFS female members"   ,  count(lcs_group_no) as "No. of LCS groups formed"   ,  sum(lcs_male) as "No. of enrolled LCS male member"   ,  sum(lcs_female) as "No. of enrolled LCSFemale member"   ,  ((sum(lcs_female)/(sum(lcs_male)+sum(lcs_female)))*100) as "% of LCS female member"  from vwwmg_tracker_1_2  where (zon::integer in (@zone) OR (@zone) IS NULL ) and (district::integer in (@geo_district) OR (@geo_district) IS NULL )')
    subtables[section] = get_json(query, [section, "Progress"])


    # WMG Funds
    # View:: vwwmg_tracker_1_2
    section = sections_name[1]
    query = get_filtered_query(post_dict,
                               'select Sum(WMG_fund_addmission_fee) as "Admission fee (TK)"  , sum(WMG_fund_savings_male) as "Savings (Tk) from Male"  , sum(WMG_fund_savings_female) as "Savings (Tk) from Female"  , sum(WMG_fund_OM_fee_male) as "O&M fee (Tk) collected from Male"  , sum(WMG_fund_OM_fee_female) as "O&M fee (Tk) collected from female"  , sum(WMG_fund_miscell_fee_male) as "Miscellaneous Fees (Tk) collected from Male"  , sum(WMG_fund_miscell_fee_female) as "Miscellaneous Fees (Tk) collected from Female"  , sum(WMG_fund_profit) as "Undistributed Profit/Income (TK)"  , 0 as "Total WMG Funds (Tk)"   from vwwmg_tracker_1_2' + filtering)
    subtables[section] = get_json(query, [section, "Progress"])


    # Use of WMG Funds
    # View:: vwwmg_tracker_1_2
    section = sections_name[2]
    query = get_filtered_query(post_dict,
                               ' select Sum(WMG_fund_use_invest_IGA_amount) as "WMG fund invested in collective IGAs (TK) "  ,  Sum(use_WMG_fund_profit_distribute) as "Profit distributed (TK) "  ,  Sum(use_WMG_fund_bank_deposit) as "Deposit in Bank (Tk) "  ,  Sum(use_WMG_fund_expense) as "Expenditure of this month (Tk) "  ,  Sum(use_WMG_fund_cash_in_hand) as "Cask in hand (Tk) "  ,  Sum(use_WMG_fund_up_to_month_expens) as "Expenditure upto this month (Tk)"  from vwwmg_tracker_1_2' + filtering)
    subtables[section] = get_json(query, [section, "Progress"])


    # Type of Business investment
    # View:: vwbusiness_investment
    section = sections_name[3]
    query = get_filtered_query(post_dict,
                               'select business as "Type of Business investment", sum(wmg_fund_use_invest_iga_amount) as "No. of Person involved" , sum(wmg_fund_use_invest_iga_amount) as "Investment Amount" from vwbusiness_investment  ' + filtering + ' group by business')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Training Course
    # View:: vwtraining_course
    section = sections_name[4]
    query = get_filtered_query(post_dict,
                               'with t as( select course as "Training Course", sum(capacity_build_act_male) as "Male" , sum(capacity_build_act_female) as "Female" from vwtraining_course ' + filtering + '  group by course, course_order order by course_order) select t.*,("Male"+"Female") total,COALESCE(round(("Female"*100.00)/NULLIF(("Male"+"Female"),0),2),0) "% of Female Participants" from t')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df
    # Modules/ Topices for Learning Session
    # View:: vwwmg_tracker_1_2
    section = sections_name[5]
    query = get_filtered_query(post_dict,
                               'select module_topic as "Modules/ Topices for Learning Session", sum(module_learn_male) as "Male" , sum(module_learn_female) as "Female"  from vwmodules_learning_session  ' + filtering + ' group by module_topic ')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Name of Crops
    # View:: vwwmg_tracker_1_2
    section = sections_name[6]
    query = get_filtered_query(post_dict,
                               'select crop_name as "Name of Crops", sum(demons_crop_plot_own_male) as "Male" , sum(demons_crop_plot_own_female) as "Female"  from vwname_crop ' + filtering + '  group by crop_name')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df
    # Initiatives Activities for Horizantal Learnng
    # View:: vwwmg_tracker_1_2
    section = sections_name[7]
    query = get_filtered_query(post_dict,
                               'select activities as "Initiatives Activities for Horizantal Learnng", sum(horizontal_learning_act_male) as "Male" , sum(horizontal_learning_act_male) as "Female"  from vwinitiatives_activities_horizantal_learnng  ' + filtering + ' group by activities')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Name of Technologies and new parctices adopted
    # View:: vwwmg_tracker_1_2
    section = sections_name[8]
    query = get_filtered_query(post_dict,
                               'select technologies as "Name of Technologies and new parctices adopted", sum(wmg_mem_num) as "No. of WMG members"  from vwtechnologies_parctices_adopted  ' + filtering + ' group by technologies')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    # Collective Action for Economic Activities
    # View:: vwcollective_action_for_economic_activities
    section = sections_name[9]
    query = get_filtered_query(post_dict,
                               'select activities as "Collective Action for Economic Activities", sum(eco_act_male) as "No. of Male involved" , sum(eco_act_male) as "No. of Female involved", sum(eco_act_investment)  as "Investment in Tk" from vwcollective_action_for_economic_activities  ' + filtering + ' group by activities')
    df = pd.read_sql(query, connection)
    df = df.to_json(orient='split')
    subtables[section] = df

    data = {'col_name': headers_col, 'data': headers, 'subtables': subtables}
    return data

def get_wmg_tracker_report(request):
    """
    Blue Gold: WMG Tracker Summery Report
    WMG Tracker Form
    :return: JSON
    """
    data=get_wmg_tracker_report_json(request.POST)
    data = json.dumps(data)
    return HttpResponse(data)

@csrf_exempt
def get_enterprise_option_graph(request, element):
    """
        TUP Enterprise Option Asset Training Graph
        WMG Tracker Form
        :return: JSON
        """
    data = get_enterprise_option_graph_json(request.POST, element)



    data = json.dumps(data)
    print data
    return HttpResponse(data)

def get_enterprise_option_graph_json(post_dict, element):

    print "###################### ENTERPRISE GRAPH JSON ###############################"
    print post_dict
    cohort_id = post_dict['cohort_id'][0]
    dashboardGenerator = DashboardGenerator.objects.filter(element_id=element).first()
    child_chart = DashboardGenerator.objects.filter(parent_chart=dashboardGenerator.id)
    query = "select max(value_text) from xform_extracted where xform_id = (select xform_id::bigint from vwform_cohort_module where cohort_id = '"+cohort_id+"' and module_name = 'enterprise_selection') and field_name = 'enterprise_option'"
    max_enterprise = utility_functions.__db_fetch_single_value(query)
    print max_enterprise
    visible_element = {}
    for child in child_chart:
        print child.filtering
        if int(child.filtering)>int(max_enterprise):
            visible_element[child.element_id] = False


    return visible_element




@csrf_exempt
def get_cohort_name(request,cohort_id):

   query = "select cohort_name from cohort where id = %d"%(int(cohort_id))
   df = pd.read_sql(query, connection)
   cohort_name = df ['cohort_name'].tolist()[0]

   return HttpResponse(json.dumps({'cohort_name':cohort_name}))
