
from onadata.apps.dashboard.forms import *
from django.db import connection
from onadata.apps.dashboard.models import *
import json
from onadata.apps.dashboard import utility_functions




"""
*****************FILTERING CONTROLS/ Fields CREATION *******************


**To Introduce New Filtering Options:
1. JS: Add creating control function in mpower.dashbaord.js
2. SERVER SIDE: Add a function in FilteringControls Class that will return a caller function(JS as string) which is written in 1
3. Function Name at point 2 will be referenced in DashboardControlsGenerator Table(field 'control_type')

"""


class FilteringControls():
    """
    Add Filtering Control
    """

    def __init__(self, nav_id, username):
        self.username = username
        self.nav_id = nav_id
        self.parent_div_id = ''
        self.controls_js = ''
        self.control_js_after_form_submit = ''
        #this js for cascading dropdown changes based on initial value
        self.control_js_trigger = ''

    def get_content(self):

        control_defs = DashboardControlsGenerator.objects.filter(navigation_bar_id=self.nav_id).order_by(
            'element_order')

        def func_not_found(self):  # just in case we dont have the function
            print "No Function Found!"


        #****Important::::::Here (Below one if condition) I am guessing that, All controls in a page will be on same side (Left/Right)
        #if there is filtering field then show Filtering icon.
        if len(control_defs)>0 and control_defs[0].allignment!='top':
             self.controls_js += """
                $("#toggle_{allignment}_{nav_id}").show();
             """.format(allignment=control_defs[0].allignment,nav_id=str(self.nav_id))

             self.control_js_after_form_submit += """
               closeNav("{allignment}_{nav_id}", "#toggle_{allignment}_{nav_id}");
             """.format(allignment=control_defs[0].allignment, nav_id=str(self.nav_id))



        for control_def in control_defs:
            #Parent Div Id where current field will hook
            self.parent_div_id = control_def.allignment + '_' + str(self.nav_id)

            control_func_name = control_def.control_type
            control_function = getattr(self, control_func_name, func_not_found)
            control_function(control_def)

        result = {'controls_js': self.controls_js, 'control_js_after_form_submit':self.control_js_after_form_submit,'control_js_trigger':self.control_js_trigger }
        return result

    def get_cascaded_js(self, control_def, cascaded_elements):
        onchange_function_js = ''
        if control_def.control_type == 'single_select':
            onchange_function_js += "onChangeElement(" + str(
                    control_def.id) + ",changed_val,'" +str(self.nav_id)+"');"
        elif control_def.control_type == 'multiple_select':
            onchange_function_js = "onChangeMultipleSelect(" + str(
                    control_def.id) + ",changed_val,'" +str(self.nav_id)+"');"
        return onchange_function_js

    def single_select(self, control_def):
        """
        Single Select Create HTML AND JS
        :return: JSON including 2 attributes:  'controls_html', 'controls_js'
        @author zinia
        """
        onchange_function_js = ''
        cursor = connection.cursor()
        ds_data = '[]'
        param = {}
        if control_def.datasource_type == '1':
            # elements which will be cascaded by this element
            datasource = control_def.datasource
            cascaded_elements = DashboardControlsCascaded.objects.filter(cascaded_parent_id=control_def.id)

            if cascaded_elements is not None:
                onchange_function_js = 'var changed_val= $(this).val();'
                onchange_function_js += self.get_cascaded_js(control_def, cascaded_elements)

            # elements by which this element will be cascaded
            print control_def.id
            cascaded_by = DashboardControlsCascaded.objects.filter(cascaded_child_id=control_def.id).first()
            print cascaded_by
            if cascaded_by is not None:
                parent_element = cascaded_by.cascaded_parent
                appearance = json.loads(parent_element.appearance)

                if "select_default" in appearance:
                    param_val = str(appearance.get('select_default'))
                    datasource = datasource.replace('@'+parent_element.control_name,"'"+param_val+"'")
            
            cursor.execute(utility_functions.get_filtered_query({},datasource ))
            # cursor.execute(utility_functions.replace_all(control_def.datasource, param_val))
            row = cursor.fetchone()
            ds_data = utility_functions.unicodoToString(row[0])
        if control_def.datasource_type == '3':
            ds_data = control_def.datasource
        # print ds_data +"   ds_data\n\n\n*******************************"
        if control_def.appearance == "":
            appearance = "{}"
        else:
            appearance = control_def.appearance

        temp_appearance = json.loads(appearance)
        if 'select_initial'  in temp_appearance:
            self.control_js_trigger+="onChangeElement("+str(control_def.id)+",null,'"+str(self.nav_id)+"');"

        self.controls_js +='try {var jsondata_' + str(control_def.id) + ' = JSON.parse(' + json.dumps(
            ds_data) + ');} catch (e) {jsondata_' + str(control_def.id) + '=' + json.dumps(
            ds_data) + ' ;}\n dropdownControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '","' + onchange_function_js + '", jsondata_' + str(
            control_def.id) + ', ' + appearance + ' ,"' + str(self.username) + '");'
        # self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
        #     ds_data) + ');\n dropdownControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '","' + onchange_function_js + '", jsondata_' + str(
        #     control_def.id) + ', ' + appearance + ' ,"' + str(self.username) + '");'
        # print self.controls_js



    def multiple_select(self, control_def):
        """
        Multiole Select Create HTML AND JS
        :return: JSON including 2 attributes:  'controls_html', 'controls_js'
        """
        cursor = connection.cursor()
        trigger_change = ''
        onchange_function_js = ''
        ds_data = '[]'
        if control_def.datasource_type == '1':
            param_val = {}
            cursor.execute(utility_functions.get_filtered_query({}, control_def.datasource))
            cascaded_elements = DashboardControlsCascaded.objects.filter(cascaded_parent_id=control_def.id)
            if cascaded_elements is not None:
                onchange_function_js = 'var changed_val= $(this).val();'
                # for elements in cascaded_elements:
                #     element = elements.cascaded_child
                onchange_function_js += self.get_cascaded_js(control_def, cascaded_elements)
            row = cursor.fetchone()
            ds_data = utility_functions.unicodoToString(row[0])
        if control_def.datasource_type == '3':
            ds_data = control_def.datasource
        if control_def.appearance == "":
            appearance = "{}"
        else:
            appearance = control_def.appearance
        print type(self.username)
        self.controls_js +='try {var jsondata_' + str(control_def.id) + ' = JSON.parse(' + json.dumps(
            ds_data) + ');} catch (e) {jsondata_' + str(control_def.id) + '=' + json.dumps(
            ds_data) + ' ;}\n multipleSelectControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '",  "' + control_def.control_label + '"  ,"' + onchange_function_js + '", jsondata_' + str(
            control_def.id) + ', ' + appearance + ',"' + str(self.username) + '");'
        self.controls_js += trigger_change  



    def single_select_pre(self, control_def):
        """
        Single Select Create HTML AND JS
        :return: JSON including 2 attributes:  'controls_html', 'controls_js'
        """
        #print " in side single select" +str(control_def.id)
        onchange_function_js = ''
        cursor = connection.cursor()
        #if control_def.cascaded_by is None:
        #    cursor.execute(control_def.datasource.replace("@id", "%"))
        #else:
        #    cursor.execute(control_def.datasource.replace("@id", ""))

        ds_data='[]'
        if control_def.datasource_type == '1':
	    "need to change"
            param_val = "%"
            cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_def.id).first()
            """code by zinia"""
            cascaded_by = DashboardControlsGenerator.objects.filter(id=control_def.cascaded_by_id).first()
            if cascaded_by is not None:
                appearance = json.loads(cascaded_by.appearance)
                if "select_default" in appearance:
                    param_val = str(appearance.get('select_default'))
                    #print "select default" + param_val


            if cascaded_elements is not None:
                onchange_function_js = 'var changed_val= $(this).val();onChangeElement(' + str(
                    control_def.id) + ',changed_val);'

            cursor.execute(control_def.datasource.replace("@id", param_val))
            """code by zinia"""
            row = cursor.fetchone()
            
            ds_data = utility_functions.unicodoToString(row[0])
            #print ds_data
        if control_def.datasource_type == '3':
            ds_data = control_def.datasource

        # print ds_data +"   ds_data\n\n\n*******************************"
        if control_def.appearance=="":
            appearance = "{}"
        else:
            appearance = control_def.appearance
        #print appearance
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n dropdownControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '","' + onchange_function_js + '", jsondata_' + str(
            control_def.id) + ', '+ appearance+' );'
        #print self.controls_js

    def multiple_select_pre(self, control_def):
        """
        Multiole Select Create HTML AND JS
        :return: JSON including 2 attributes:  'controls_html', 'controls_js'
        """
        cursor = connection.cursor()
        onchange_function_js = ''
        ds_data = '[]'
        if control_def.datasource_type == '1':
            param_val = {}
            param_val['@id'] = "like '%'"
            param_val['@username'] = self.username


            #cursor.execute(utility_functions.replace_all(control_def.datasource, param_val))
            cursor.execute(control_def.datasource.replace("@id", "NULL"))
            cascaded_elements = DashboardControlsGenerator.objects.filter(cascaded_by_id=control_def.id).first()
            if cascaded_elements is not None:
                onchange_function_js = ' var changed_val= $(this).val(); onChangeMultipleSelect(' + str(
                    control_def.id) + ',changed_val);'
            row = cursor.fetchone()
            ds_data = utility_functions.unicodoToString(row[0])
        if control_def.datasource_type == '3':
            ds_data = control_def.datasource
        if control_def.appearance=="":
            appearance = "{}"
        else:
            appearance = control_def.appearance
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n multipleSelectControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '",  "' + control_def.control_label + '"  ,"' + onchange_function_js + '", jsondata_' + str(
            control_def.id) + ', '+appearance+',"'+self.username+'");'

    def checkbox(self, control_def):
        """
        Checkbox Create HTML AND JS
        :return: None
        """
        cursor = connection.cursor()
        cursor.execute(eachrow.datasource)
        row = cursor.fetchone()
        ds_data = utility_functions.unicodoToString(row[0])
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n checkboxControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", jsondata_' + str(
            control_def.id) + ' );'

    def radio(self, control_def):
        """
        Radio Create HTML AND JS
        :return: None
        """
        # controls_html += '<div id="' + parent_div_id + '"></div>'
        cursor = connection.cursor()
        cursor.execute(control_def.datasource)
        row = cursor.fetchone()
        ds_data = utility_functions.unicodoToString(row[0])
        self.controls_js += '\nvar jsondata_' + str(control_def.id) + '=JSON.parse(' + json.dumps(
            ds_data) + ');\n radioControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", jsondata_' + str(
            control_def.id) + ' );'

    def date(self, control_def):
        """
        Date Create HTML AND JS
        :return: None
        """
        if control_def.appearance == "":
            control_def.appearance = '{"format":"dd-mm-yyyy","viewmode":"days","minviewmode":"days", "minviewmode":"years"}'
        self.controls_js += '\n dateControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '",' + control_def.appearance + ', ""  );'

    def button(self, control_def):
        """
        Button Create HTML AND JS
        :return: None
        """
        self.controls_js += '\n buttonControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '", "' + control_def.control_label + '" );  '

    def text(self, control_def):
        """
        Text Box Create HTML AND JS
        :return: None
        """
        self.controls_js += '\n textinputControlCreate("' + control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", ""  );'


    def slider_range(self, control_def):
        """
        slider range create HTML and JS
        :param control_def:
        :return:
        """


        appearance = {}
        if control_def.appearance == "":
            appearance = {}
        else :
            appearance = control_def.appearance

        self.controls_js +='\n sliderControlCreate("' +control_def.control_id + '","' + self.parent_div_id + '","' + control_def.control_name + '","' + control_def.control_label + '", '+appearance+'  );'




