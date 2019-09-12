

import decimal
from onadata.apps.dashboard.forms import *
from django.db import connection
from onadata.apps.dashboard.models import *
import json
from onadata.apps.dashboard import utility_functions
import pandas as pd
import ast

import simplejson as sjson
import numpy as np
import xlwt
import os
from django.conf import settings

'''
***********************Table: Data Processing*******************************


******To Introdce New Chart:
1. Add chart type and acting functuan name in DashboardChartType Table
2. Implement that function (with exact same name!) inside TableConfig Class


Json generation Flow:
Get query
    |
    |query
    v
Run function to create DataFrame required for that Graph (From DashboardGenerator Table)
    |
    |Dataframe
    v
Run function to get json from chart type (From DashboardChartType Table)
'''

class TableConfig():
    """
    Table Functions.
    Creating JOSN for different charts
    """

    def __init__(self, graph_id, request, appearance):
        self.graph_id = graph_id
        self.dashboardGenerator= DashboardGenerator.objects.filter(id=self.graph_id).first()
        self.post_dict = request.POST
        self.request = request
        self.appearance = appearance


    def func_not_found(name_field, category_field, data_field, query):
        """
        Error Handler for Function calling from String
        """
        print "Exp: No Function Found!"
        return {}

    def execute_query(self, query):
        """
        Called From Outside
        :param chart_type: from DashboardChartType Table
        :param query: SQL
        :return: JSON/ HTML
        """
        jsondata = ''

        # GET DS Manipulator FUNCTION Name

        datasource_manipulator_func_name=getattr(self, self.dashboardGenerator.datasource_manipulator_func)
        dataset=datasource_manipulator_func_name(query)

        return dataset;


    def getDashboardDatatable(self, df):
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
        col_names = list(df.columns.values)
        for row in df.iterrows():
            index, data = row
            data_list.append(data.tolist())
        return json.dumps({'col_name': col_names, 'data': data_list})

    def getDashboardDatatable(self, df):
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
        col_names = list(df.columns.values)
        # for row in df.iterrows():
        #     index, data = row
        #     data_list.append(data.tolist())
        data_list = map(list, df.values)
        print "Every"

        return json.dumps({'col_name': col_names, 'data': data_list})

    def get_default(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        --------------------
        name   |category| value
        ------------------
        'Afrin'|'2017'  | 5.00
        'Arian'|'2016'  | 6.00
        ..................
        .................
        :param query:
        :return: JSON (panda dataframe. Structure
        name|category|value TO JSON)
        ..................
        ...................
        '''
        df = pd.read_sql(query, connection)
        return self.getDashboardDatatable(df)

    def simple_table(self, query):
        '''
                Use this function
                WHEN QUERY OUTPUT IS LIKE
                --------------------
                category| value
                ------------------
                '2017'  | 5.00
                '2016'  | 6.00
                ..................
                .................
                :param query:
                :return: JSON (panda dataframe. Structure
                name|category|value TO JSON)
                ..................
                ...................
                '''
        d = []
        df = pd.read_sql(query, connection)

        col_names = []
        value_list = []
        for row in df.iterrows():
            index, data = row
            print data
            col_names.append(data['category'])

            d.append(data['value'])
        d.append(sum(d))
        value_list.append(d)
        col_names.append('Total')

        return json.dumps({'col_name': col_names, 'data': value_list})


    def get_pivoted(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        --------------------
        name   |category| value
        ------------------
        'Afrin'|'2017'  | 5.00
        'Arian'|'2016'  | 6.00
        ..................
        .................
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''
        table_html=""
        table_classes="dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(element_id=self.dashboardGenerator.element_id)

        df = pd.read_sql(query, connection)
        if 'name_sorting' in  df:
            df = df.fillna(0)
            df = pd.pivot_table(df, values="value", rows=['name_sorting', "name"], cols=["category"])



        else:
            df = pd.pivot_table(df, values="value", index=["name"], columns=["category"])
            # df.index.name = 'Branch Name'
            # df.drop(['category'], axis=1)
            # print df.index.level
            df.columns.name= ""

        df = df.fillna(0)

        table_html = df.to_html(classes=table_classes)

        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)






    def get_transposed_df(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        col_1  | col_2 |col_3 |..................unlimited column
        ------------------------------------------
        33     | 2017  | 5.00 |


        :param query:
        :return: panda dataframe. Structure
        --------------
        category| value
        ---------------
        col_1   | 33
        col_2   | 2017
        col_3   | 5.00
        .............
        ............

        '''
        df = pd.read_sql(query, connection)
        df=df.T
        df['category'] = df.index
        df.columns=['value','category']
        return self.getDashboardDatatable(df)


    def get_outcome_progress_status(self,query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''


        table_html=""
        df = pd.read_sql(query, connection)
        table_classes="dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(element_id=self.dashboardGenerator.element_id)
        df = pd.pivot_table(df, values="value", rows=["name"], cols=["category"])
        df.index.name = 'Score'
        df = df.fillna(0)

        #Calculate Differce of two col and store it
        col_names=df.columns
        first_collection=0
        second_collection = 0
        if len(col_names)==2:
            first_collection = df[col_names[0]]
            second_collection = df[col_names[1]]
        elif len(col_names)==1:
            second_collection = df[col_names[0]]
        #STORE in a new column
        df['Progress']=second_collection-first_collection

        # Hide Column Name:  'Category' from Table
        df.columns.name = ""
        table_html = df.to_html(classes=table_classes)
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)

    def activity_wmg_fund(self, query):
        '''
                BLUEGOLD Reporting
               :param query:
               :return: HTML CODE
               ..................
               ...................

               '''

        # print "table query"
        # print query
        table_html = ""
        df = pd.read_sql(query, connection)
        "getting index_name from column"
        col_length = len(df.columns.values)

        index_name = str(df[df.columns.values[col_length - 1]][0])
        print index_name
        table_classes = "dataframe_{element_id} display table cell-border".format(
            element_id=self.dashboardGenerator.element_id)
        df = pd.pivot_table(df, values="value", rows=["sl","name"], cols=["category_sorting","category"])
        
	df.index.names = ['Sl',index_name]
        df = df.fillna(0)
        
	

        # Calculate Differce of two col and store it
        col_names = df.columns
        print col_names
        first_collection = 0
        second_collection = 0
        if len(col_names) == 2:
            first_collection = df[col_names[0]]
            second_collection = df[col_names[1]]
        elif len(col_names) == 1:
            second_collection = df[col_names[0]]
        # STORE in a new column
        df['3','Progress'] = second_collection - first_collection
        
	print "checking df########"
	print df
	#df = df.sort_index(ascending=False, axis = 1)
        '''sum_row = {col: df[col].sum() for col in df}

        print sum_row
        
        sum_df = pd.DataFrame(sum_row, index=["Total"])
        print sum_df
	#col_names = col_names.tolist() + ['Progress']
        #df = df.reindex_axis(col_names, axis=1)
        # Hide Column Name:  'Category' from Table
        df = df.append(sum_df)
	'''
	df.ix[('9','Total'), :] = df.sum()
	df.columns = df.columns.droplevel([0])
        #df.index.name = index_name
        df.columns.name = ""
	
        table_html = df.to_html(classes=table_classes)
        filename = self.excel_file(df)
	
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)

    def get_outcome_progress_trend(self,query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''

        # print "table query"
        # print query

        
        table_html=""
        df = pd.read_sql(query, connection)
        flag = False
        if "name_sorting" in df:
            flag = True
        "getting index_name from column"
        col_length =  len(df.columns.values)

        index_name = str(df[df.columns.values[col_length-1]][0])
        print index_name
        table_classes="dataframe_{element_id} display table cell-border".format(element_id=self.dashboardGenerator.element_id)
        if flag:
            df = pd.pivot_table(df, values="value", rows=["name_sorting","name"], cols=["category", "col_name"])
            df.index.names = ["SI",index_name]
        else:
            df = pd.pivot_table(df, values="value", rows=["name"], cols=["category", "col_name"])
            df.index.name= index_name

        df.index.name = index_name
        df = df.fillna(0)
	
        print "trend eco table of use"
        print df

        # Calculate Differce of two col and store it
        col_names = df.columns
        print col_names
        first_collection = 0
        second_collection = 0
        if len(col_names) == 2:
            first_collection = df[col_names[0]]
            second_collection = df[col_names[1]]
        elif len(col_names) == 1:
            second_collection = df[col_names[0]]
        # STORE in a new column
        df['Progress'] = second_collection - first_collection

        #Hide Column Name:  'Category' from Table
        if flag:
            df.columns.names=["",""]
        else:
            df.columns.names=["",""]

        table_html = df.to_html(classes=table_classes)
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)

    def use_wmg_fund(self,query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''

        # print "table query"
        # print query

        
        table_html=""
        df = pd.read_sql(query, connection)
        flag = False
        if "col_name" in df:
            flag = True
        "getting index_name from column"
        col_length =  len(df.columns.values)

        index_name = str(df[df.columns.values[col_length-1]][0])
        print index_name
        table_classes="dataframe_{element_id} display table cell-border".format(element_id=self.dashboardGenerator.element_id)
        if flag:
            df = pd.pivot_table(df, values="value", rows=["name"], cols=["category", "col_name"])
        else:
            df = pd.pivot_table(df, values="value", rows=["sl","name"], cols=["category_sorting","category"])

        df.index.names = ['Sl',index_name]
        df = df.fillna(0)
	#df = df.sort_index(ascending=False, axis = 1)
        print "trend eco table of use"
        print df

        # Calculate Differce of two col and store it
        col_names = df.columns
        print col_names
        first_collection = 0
        second_collection = 0
        if len(col_names) == 2:
            first_collection = df[col_names[0]]
            second_collection = df[col_names[1]]
        elif len(col_names) == 1:
            second_collection = df[col_names[0]]
        # STORE in a new column
        df['3','Progress'] = second_collection - first_collection

        #Hide Column Name:  'Category' from Table
        df.columns = df.columns.droplevel([0])
        if flag:
            df.columns.names=["",""]
        else:
            df.columns.names = [""]

	#col_names = col_names.tolist() +['Progress']
	#df = df.reindex_axis(col_names,axis=1)
        table_html = df.to_html(classes=table_classes)
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)



    def get_outcome_progress_trend_v2(self,query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''

        # print "table query"
        # print query
        table_html=""
        df = pd.read_sql(query, connection)
        "getting index_name from column"
        col_length =  len(df.columns.values)

        index_name = str(df[df.columns.values[col_length-1]][0])
        print index_name
        table_classes="dataframe_{element_id} display table cell-border".format(element_id=self.dashboardGenerator.element_id)
        df = pd.pivot_table(df, values="value", rows=["sl","Activities"], cols=["category"])
        df.index.name = index_name
        df = df.fillna(0)
	#df = df.sort_index(ascending=False, axis = 1)
        

        # Calculate Differce of two col and store it
        col_names = df.columns
        print col_names
        first_collection = 0
        second_collection = 0
        if len(col_names) == 2:
            first_collection = df[col_names[0]]
            second_collection = df[col_names[1]]
        elif len(col_names) == 1:
            second_collection = df[col_names[0]]
        # STORE in a new column
        df['Progress'] = second_collection - first_collection

        #Hide Column Name:  'Category' from Table
        df.columns.name=""

        #col_names = col_names.tolist() +['Progress']
	#df = df.reindex_axis(col_names,axis=1)
        df = np.round(df)
        table_html = df.to_html(classes=table_classes)
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)
    


    






    def get_polder_wise_avg_progress_marker_score(self,query):
        '''
         NEW NAME:::  Polder Wise WMG Performance Level
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''
        param_val = self.post_dict['calculation_type']


        table_html=""
       
        df = pd.read_sql(query, connection)
        table_classes="dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(element_id=self.dashboardGenerator.element_id)
        #df = pd.pivot_table(df, values="value", rows=["District","Polder"], cols=["name_sorting","name"] ,aggfunc=len, margins=True, dropna=True,fill_value=0)
        df = pd.pivot_table(df, values="value", rows=["Zone", "Polder"], cols=["name_sorting", "name"],
                            fill_value = 0,  dropna = True)
        df['Total'] = df.sum(axis=1)
	df.ix[('Total',''), :] = df.sum()
	df = np.round(df)
        if param_val =='Percentage':
            df = df.div( df.Total, axis='index')
            print "test"
            df = 100*np.round(df, decimals=3)
        # margins = True, dropna = True,

        df.index.name = 'Qualification'
        df = df.fillna(0)
        print "average progress marker score"
        print df
        #Hide Column Name
        #HIde name and name_soring Col name
        df.columns.names=["",""]

        table_html = df.to_html(classes=table_classes)
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)


    def get_polder_wise_wmg_performance(self,query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE of TABLE
        '''
        param_val = self.post_dict['theme']
        filtering_options = sjson.loads(str(self.dashboardGenerator.filtering), strict=False)
        print (type(filtering_options))
        # filtering_option = self.dashboardGenerator.filtering

        if param_val in filtering_options:
            query = filtering_options.get(param_val)
        table_html = ""


        print "query for performance"
        print query
        df = pd.read_sql(query, connection)
        print "original data"
        print df

        table_classes = "dataframe_{element_id} display table table-bordered cell-border".format(
            element_id=self.dashboardGenerator.element_id)
        df = pd.pivot_table(df, values="value", rows=["district","polder"], cols=["title","category"])
        # dg = pd.pivot_table(df, values="value", index=["district", "polder"], cols=["title", "category"], aggfunc=len)
        df.index.names = ['District','Polder']
        df = df.fillna(0)
        df = np.round(df, decimals=3)
        # print "performance"
        # print self.post_dict
        # Calculate Differce/Progress of two col in  each section and store it
        print "dataframe"
        print df
        for column in df:
            #PArent column have 1/2 child col
            print column
            child_col_names = df[column[0]].columns
            print "child"
            print child_col_names
            first_collection = 0
            second_collection = 0
            if len(child_col_names) == 2:
                first_collection = df[column[0],child_col_names[0]]
                second_collection = df[column[0],child_col_names[1]]
            elif len(child_col_names) == 1:
                second_collection = df[column[0],child_col_names[0]]
            elif len(child_col_names) == 3:
                #After Progress added, 2nd iteration would be 3
                continue;
            # STORE in a new column
            df[column[0],'Progress'] = second_collection - first_collection


        # Hide Column Name
        df.columns.names = ["", ""]

        table_html = df.to_html(classes=table_classes)

        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)


    def test_eco_activity(self, query):
        df = pd.read_sql(query, connection)

        table_classes = "dataframe_{element_id} display table table-bordered cell-border".format(
            element_id=self.dashboardGenerator.element_id)
        df = df.pivot( values="value", index="Activities", columns=["category", "name"])
        # dg = pd.pivot_table(df, values="value", index=["district", "polder"], cols=["title", "category"], aggfunc=len)
        df.index.name = 'Activities'
        df = df.fillna(0)

        # df.columns.names = ["", "", ""]

        table_html = df.to_html(classes=table_classes)

        return table_html



    def eco_dev_activity(self, query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE of TABLE
        '''
        df = pd.read_sql(query, connection)
    
        table_classes = "dataframe_{element_id} display table table-bordered cell-border".format(
            element_id=self.dashboardGenerator.element_id)
        print "getting index_name from column"
        col_length = len(df.columns.values)
    
        index_name = str(df[df.columns.values[col_length - 1]][0])
        print index_name
        if "category_sorting" in df :
            df = pd.pivot_table(df,values=["value"],  rows=["Activities"],  cols=["category_sorting","category","name"])
            
	    #shifting others in the last row
	    index_list = df.index.values.tolist()
	    reindex_list = [ x for x in index_list if x != 'Others' ]
	    reindex_list.append('Others')
	    df = df.reindex(reindex_list)	
	    df.index.name = index_name
            df = df.fillna(0)
            df.columns = df.columns.droplevel([0])
            df.columns = df.columns.droplevel([0])
            df.columns.names = ["", ""]
        else :
    
            df = pd.pivot_table(df, values=["value"], rows=["Activities"], cols=["category", "name"])
            # dg = pd.pivot_table(df, values="value", index=["district", "polder"], cols=["title", "category"], aggfunc=len)
            df.index.name = index_name
            df = df.fillna(0)
            df = df.sort_index(ascending=False, axis=1)
            # df.columns = df.columns.droplevel([0])
            # df.columns = df.columns.droplevel([0])
            print "##before dropping level"
            # print df
            # dropping one level of complex header
            df.columns = df.columns.droplevel([0])
            df = df.sort_index(ascending=False, axis=1)
            print "###3after drooping level"
            # print df
    
    
            # current columns tuple
            col_names = df.columns
            col = []
            # taking progress at last position
            for f in col_names:
                if 'Progress' not in f[0]:
                    col.append(f)
            for f in col_names:
                if 'Progress' in f[0]:
                    col.append(f)
            # reindexing according to order
            print "####rearrange col"
            print col
            df = df.reindex_axis(col, axis=1)
            # Hide Column Name
            df.columns.names = ["", ""]
    
        table_html = df.to_html(classes=table_classes)
    
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)
    





    def eco_investment_iga(self,query):
        '''
         BLUEGOLD Reporting
        :param query:
        :return: HTML CODE of TABLE
        '''
        df = pd.read_sql(query, connection)
        col_length =  len(df.columns.values)

        index_name = str(df[df.columns.values[col_length-1]][0])
        table_classes = "dataframe_{element_id} display table table-bordered cell-border".format(
            element_id=self.dashboardGenerator.element_id)
        print "sort"
        df =df.sort('name', ascending=False)
        df = pd.pivot_table(df,values=["value"],  rows=["Activities"],  cols=["category_sorting","category","name"])
        df.index.name = index_name
	# shifting others in the last row
	index_list = df.index.values.tolist()
	reindex_list = [ x for x in index_list if x != 'Others' ]
	reindex_list.append('Others')
	df = df.reindex(reindex_list)
	
        df = df.fillna(0)

	
        # dropping level one step
        df.columns = df.columns.droplevel([0])
	df.columns = df.columns.droplevel([0])
        "getting column names"
        idx = df.columns
        col = idx.tolist()

        "getting list of values"
        percentage = []
        if len(col)==6:
            quarter_fund = df[col[3]].tolist()
        else:
            quarter_fund = df[col[1]].tolist()

        total_fund = 0
        for f in quarter_fund:
            total_fund = total_fund+int(f)

        for f in quarter_fund:
            percent = float(f)/total_fund*100
            percentage.append(percent)


        percentage = np.round(percentage, decimals=2)


        df['Percentage of total investment (Last quarter)'] = percentage
        #print df['Progress','No. of person involved']
        df.ix[('Total Fund Invested in IGAs'), :] = df.sum()
        #print df.index.values
        df.columns.names = ["",""]

        table_html = df.to_html(classes=table_classes)
        #func_name = getattr(self,excel_file)
        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)


        # return table_html



    def excel_file(self, df):
        
        file = 'pandas_simple_' + self.graph_id
        if 'title' in self.appearance:
            file = str(self.appearance['title'])
            file = file.replace(' ', '_')

        # current_user = UserModuleProfile.objects.filter(user=user)
        user_path_filename = os.path.join(settings.MEDIA_ROOT, self.request.user.username)
        user_path_filename = os.path.join(user_path_filename, "exported_file")
        if not os.path.exists(user_path_filename):
            os.makedirs(user_path_filename)

        filename = os.path.join(user_path_filename, file + '.xls')

        writer = pd.ExcelWriter(filename, engine='xlwt')
        # Convert the dataframe to an XlsxWriter Excel object.
        df.to_excel(writer, sheet_name='Sheet1')

        # Close the Pandas Excel writer and output the Excel file.
        

        writer.save()

        return file+'.xls'





    def enterprise_group(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        --------------------
        name   |category| value
        ------------------
        'Afrin'|'2017'  | 5.00
        'Arian'|'2016'  | 6.00
        ..................
        .................
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''
        print query
        table_html=""
        table_classes="dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap dt-responsive".format(element_id=self.dashboardGenerator.element_id)

        df = pd.read_sql(query, connection)
        # col_length = len(df.columns.values)
        #print df
        #index_name = str(df[df.columns.values[col_length - 1]][0])
        df = pd.pivot_table(df, values="value",  index = ['index_name'],columns=["category"])

        df.columns.names = [""]
        df.index.name = None
        #print df.axes
        df = df.fillna(0)
        table_html = df.to_html(classes=table_classes)

        #filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': ''}
        #print table_html
        return json.dumps(data)


    def asset_enterpise(self,query):
        '''
        Use this function
        WHEN QUERY OUTPUT IS LIKE
        --------------------
        name   |category| value
        ------------------
        'Afrin'|'2017'  | 5.00
        'Arian'|'2016'  | 6.00
        ..................
        .................
        :param query:
        :return: HTML CODE
        ..................
        ...................

        '''
        print query
        table_html=""
        table_classes="dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(element_id=self.dashboardGenerator.element_id)

        df = pd.read_sql(query, connection)
        if df.empty == False:

            # column length of dataframe
            col_length = len(df.columns.values)
            # value of second last column
            cal_type = str(df[df.columns.values[col_length - 2]][0])

            # value of last column
            index_name = str(df[df.columns.values[col_length - 1]][0])


        df = pd.pivot_table(df, values="value", index=["name"], columns=["category"],aggfunc=pd.Series.nunique, fill_value=0)
        df.index.name = index_name

        # df.drop(['category'], axis=1)
        # print df.index.level
        df.columns.name = ""
        # df.columns.names = [""]
        df['Total'] = df.sum(axis=1)

        df = df.fillna(0)
        df = df.astype(int)
        if cal_type =='percent' or cal_type == 'percentage':
            df = df.div(df.Total, axis='index').applymap(lambda x: "{0:.0f}%".format(100*x))

        table_html = df.to_html(classes=table_classes)

        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        #print table_html
        return json.dumps(data)



    def total_table(self, query):
        '''
                        BLUEGOLD Reporting
                       :param query:
                       :return: HTML CODE
                       ..................
                       ...................

                       '''

        # print "table query"
        # print query
        table_html = ""
        df = pd.read_sql(query, connection)
        "getting index_name from column"
        col_length = len(df.columns.values)

        index_name = str(df[df.columns.values[col_length - 1]][0])
        print index_name
        table_classes = "dataframe_{element_id} display table cell-border dt-responsive".format(
            element_id=self.dashboardGenerator.element_id)
        df = pd.pivot_table(df, values="value", index = None, columns=["category"])

        df = df.fillna(0)
        table_html = df.to_html(classes=table_classes)

        filename = self.excel_file(df)
        data = {'table': table_html,
                'filename': filename}
        # print table_html
        return json.dumps(data)


    def comparison_matrix(self, query):
        '''
                                TUP Reporting
                               :param query:
                               :return: HTML CODE
                               ..................
                               ...................
                               @zinia
                               '''


        table_html = ""
        index_name = 'Final Selection'
        col_name = 'Primary Selection'
        cal_type = ''
        df = pd.read_sql(query, connection)
        #column length of dataframe
        col_length = len(df.columns.values)
        print "Group Comparison"
        #print df
        if df.empty==False:
            #value of last column
            cal_type = str(df[df.columns.values[col_length - 1]][0])
            #value of second last column
            index_name = str(df[df.columns.values[col_length - 2]][0])
            #value of third last column
            col_name = str(df[df.columns.values[col_length - 3]][0])
        #table classes defined
        table_classes = "dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(
            element_id=self.dashboardGenerator.element_id)
        # , margins = True, margins_name = "Total")
        #pivot table counting unique values
        df = pd.pivot_table(df, values="value", index='name', columns=["category"],  aggfunc=pd.Series.nunique, fill_value=0)

        #df = df.div(df.sum(axis=1), axis='index')
        #df.columns = ['Group-1','Group-2', 'Group-3', 'Not-Selected', 'Total']
        
        df = df.fillna(0)
        #setting index name of single level
        df.index.name = index_name
        # setting column name of single level
        df.columns.name = col_name
        #Casting All value as integer
        df = df.astype(int)
        #print df
        if cal_type =='percentage':
            #df = df.div(df.sum(axis=1), axis='index').applymap(lambda x: "{0:.0f}%".format(100*x))
            df = df.div(df.sum(axis=0), axis='columns').applymap(lambda x: "{0:.0f}%".format(100*x))
        table_html = df.to_html(classes=table_classes)
        filename = ''
        data = {'table': table_html,
                'filename': filename}
        #print table_html
        return json.dumps(data)


    def group_matrix(self, query):
        '''
                                TUP Reporting
                               :param query:
                               :return: HTML CODE
                               ..................
                               ...................
                               @zinia
                               '''
        #print "In the matrix"
        #print query
        table_html = ""
        df = pd.read_sql(query, connection)
        #column length of dataframe
        col_length = len(df.columns.values)
        index_name=''
        total_flag =''
        cal_type = ''
        if df.empty==False:
            #value of last column
            cal_type = str(df[df.columns.values[col_length - 1]][0])
            #value of second last column
            index_name = str(df[df.columns.values[col_length - 2]][0])
            #value of third last column
            total_flag = str(df[df.columns.values[col_length - 3]][0])
        #table classes defined
        table_classes = "dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(
            element_id=self.dashboardGenerator.element_id)
        # , margins = True, margins_name = "Total")
        #pivot table counting unique values
        df = pd.pivot_table(df, values="value", index='name', columns=["category"],  aggfunc=pd.Series.nunique, fill_value=0)


        df = df.fillna(0)
        #setting index name of single level
        df.index.name = index_name
        #Casting All value as integer
        df = df.astype(int)

        if total_flag == 'true':

            df['Total'] = df.sum(axis=1)
            if cal_type =='percentage':
                df = df.div(df.Total, axis='index').applymap(lambda x: "{0:.0f}%".format(100*x))
        
        else:

            if cal_type =='percentage':
                df = df.div(df.sum(axis=1), axis='index').applymap(lambda x: "{0:.0f}%".format(100*x))

        df.reset_index(inplace=True)

        table_html = df.to_html(classes=table_classes,index=False)

        filename = ''
        data = {'table': table_html,
                'filename': filename}
        #print table_html
        return json.dumps(data)


    def branch_exclusion(self, query):
        '''
                                TUP Reporting
                               :param query:
                               :return: HTML CODE
                               ..................
                               ...................
                               @zinia
                               '''
        print "In the matrix"
        #print query
        table_html = ""
        df = pd.read_sql(query, connection)
        #column length of dataframe
        col_length = len(df.columns.values)
        cal_type = ''
        if df.empty==False:
            #value of last column
            cal_type = str(df[df.columns.values[col_length - 1]][0])
            #value of second last column
            index_name = str(df[df.columns.values[col_length - 2]][0])
            #value of third last column
            total_flag = str(df[df.columns.values[col_length - 3]][0])
        #table classes defined
        table_classes = "dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(
            element_id=self.dashboardGenerator.element_id)
        # , margins = True, margins_name = "Total")
        #pivot table counting unique values
        #print df
        df2 = df[['Branch Name','total_group']]
        
        df2 = df2.drop_duplicates()
        df2=df2.set_index('Branch Name')
        #print df2
        df = pd.pivot_table(df, values="value", index=['Branch Name'], columns=["category"],  aggfunc=pd.Series.nunique, fill_value=0)


        
        df = df.fillna(0)
        #setting index name of single level
        #df.index.name = index_name
        #Casting All value as integer
        df = df.astype(int)
        df['Total'] = df.sum(axis=1)
        df.index.name = 'Branch Name'
        
        if cal_type =='percentage':
            #df = df.div(df.total_group, axis='index')
            df = df.merge(df2, left_index=True, right_index=True, how='inner')
            df = (df.T / df.total_group).T.applymap(lambda x: "{0:.2f}%".format(100*x))
            df_column_list = list(df.columns)
            #print df_column_list
            df_column_list.remove('total_group')
            df = df[df_column_list]

        #print df
        df.reset_index(inplace=True)
        table_html = df.to_html(classes=table_classes,index=False)
        
        filename = ''
        data = {'table': table_html,
                'filename': filename}
        #print table_html
        return json.dumps(data)



    def matrix_with_total(self, query):
        '''
                                TUP Reporting

        Use this function
        WHEN QUERY OUTPUT IS LIKE
        --------------------
        name   |category| value
        ------------------
        'Afrin'|'2017'  | 5.00
        'Arian'|'2016'  | 6.00
        and when aggregate function will be sum
                               :param query:
                               :return: HTML CODE
                               ..................
                               ...................

                               
                               @zinia
                               '''
        print "In the matrix"
        #print query
        table_html = ""
        total = 1
        df = pd.read_sql(query, connection)
        if 'total_asset' in df.columns:
            total = df['total_asset'][0]
        #column length of dataframe
        col_length = len(df.columns.values)
        index_name=''
        if df.empty==False:
            # value of last column
            cal_type = str(df['cal_type'][0])
            #value of second last column
            index_name = str(df['index_name'][0])
            #value of third last column
            total_flag = str(df['total_flag'][0])
        #table classes defined
        table_classes = "dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(
            element_id=self.dashboardGenerator.element_id)
        # , margins = True, margins_name = "Total")
        #pivot table counting unique values
        print df
	if 'category_sorting' in df.columns and df.empty==False:

            df = pd.pivot_table(df, values="value", index='name', columns=["category_sorting","category"])
            print df
            df.columns = df.columns.droplevel([0])
            print df
	else: 
	    df = pd.pivot_table(df, values="value", index='name', columns=["category"])
        df = df.fillna(0)
        #setting index name of single level
        df.index.name = index_name
        #Casting All value as integer
        df = df.astype(int)
        if total_flag == 'true':
            #df['Total'] = df.sum(axis=1)
            if cal_type =='percentage':
                df = df.div(int(total), axis='index').applymap(lambda x: "{0:.1f}%".format(100*x))
        else:
            if cal_type =='percentage':
                df = df.div(int(total), axis='index').applymap(lambda x: "{0:.1f}%".format(100*x))
        df.reset_index(inplace=True)
        table_html = df.to_html(classes=table_classes,index=False)
        filename = ''
        data = {'table': table_html,
                'filename': filename}
        #print table_html
        return json.dumps(data)


    def Branch_wise_asset_enterprise(self, query):
        df = pd.read_sql(query, connection)
        df1 = df[['Total','cal_type']]
        cal_type=''
        if df.empty == False:
            # value of last column
            cal_type = str(df['cal_type'][0])
        df1.fillna(1)
        df = df[['Branch','Enterprise','Training','Asset']]
        table_classes = "dataframe_{element_id} display table table-bordered table-striped table-condensed table-responsive nowrap".format(
        element_id=self.dashboardGenerator.element_id)
        table_html = df.to_html(classes=table_classes,index=False)
        if cal_type == 'percent' or cal_type == 'percentage':
            print "here in percentage"
            df = df.fillna('0.00%')
            # df = df.div(df1.Total, axis='index').applymap(lambda x: "{0:.0f}%".format(100 * x))
        else:
            df = df.fillna(0)
        table_html = df.to_html(classes=table_classes,index=False)
        filename = self.excel_file(df)
        data = {'table': table_html,
            'filename': filename}
        # print table_html
        return json.dumps(data)  


    def tree_table_simple(self, query):
        sql = "	with q as (select organization as \"name\", org_id, srm_name,rm_name,bm_name from branch_user_role), q2 as (select branch_id , (case when ( asset_value_doubled_percentage::numeric )::int < 0 then 'Decreased'::text when ( asset_value_doubled_percentage::numeric )::int = 0 then 'No Change (0%)'::text when (( asset_value_doubled_percentage::numeric )::int >1 and (asset_value_doubled_percentage::numeric)::int <= 25 ) then 'No Change (0%)'::text else '3 productive asset'::text end) as category, hh_id as value from household where last_graduation_date is not null )select * from q left join q2 on q.org_id = q2.branch_id::int"
        print query
        main_df = pd.read_sql(query, connection)
        cal_type = 'number'
        total = 50
        if 'cal_type' in main_df.columns:
            cal_type = main_df['cal_type'][0]
	if 'hh_count' in main_df.columns:
            total = main_df['hh_count'][0]
            print total


        #print df
        org_df = main_df[['name', 'rm_name', 'bm_name', 'srm_name','tl_name']]

        if 'category_sorting' in main_df.columns:
            df = pd.pivot_table(main_df, values="value", index='name', columns=["category_sorting","category"], aggfunc=pd.Series.nunique,
                                fill_value=0)
            if df.empty == False:
                df.columns = df.columns.droplevel([0])
 	else:
            df = pd.pivot_table(main_df, values="value", index='name', columns=["category"], aggfunc=pd.Series.nunique,
                                fill_value=0)
        print df
        if cal_type == 'percent' or cal_type == 'percentage':
            df = df.div(int(total), axis='index').applymap(lambda x: float("{0:.3f}".format(100 * x)))
            #.applymap(lambda x: "{0:.0f}".format(100 * x))

        df.reset_index(inplace=True)

        if df.empty:
	    if 'column' in self.appearance:
                columns = self.appearance['column']
                df = pd.DataFrame(columns=columns)
            else:
		df = pd.DataFrame(columns=['name','category'])
        # print df
        org_df = org_df.merge(df, on='name', how="left")
        col_names = list(org_df.columns)
        features_new = [str(x.encode('utf-8')) for x in col_names]
        org_df.columns = features_new

        org_df = org_df.fillna(0)
        print org_df.head(5)
        # org_df = org_df[[]]
        data_dict = org_df.to_dict('records')
        rm_data = {}
        temp_data = {}
        srm_data = {}
        tl_data = {}
        col_names = list(org_df.columns)
        print col_names
        for d in data_dict:
            l = len(d) - 1
            rm_name = d['rm_name']
            tl_name = d['tl_name']
            srm_name = d['srm_name']

            if rm_name not in rm_data:
                rm_data[rm_name] = set()

            if srm_name not in srm_data and srm_name != 0:
                srm_data[srm_name] = set()

            if tl_name not in tl_data and tl_name != 0:
                tl_data [tl_name] = set()

            rm_data[rm_name].add(d['name'])
            if srm_name != 0:
                srm_data[srm_name].add(rm_name)
            if tl_name != 0:
                tl_data[tl_name].add(srm_name)

            del d['rm_name']
            del d['bm_name']
            del d['srm_name']
            del d['tl_name']
            temp_data[d['name']] = d
            if rm_name not in temp_data and rm_name != 0:
                temp_data[rm_name] = {k: 0 for k, v in d.items()}
            if srm_name not in temp_data and srm_name != 0:
                temp_data[srm_name] = {k: 0 for k, v in d.items()}
            if tl_name not in temp_data and tl_name != 0:
                temp_data[tl_name] = {k: 0 for k, v in d.items()}

        temp_data = self.getting_child(rm_data, temp_data)
        temp_data = self.getting_child(srm_data, temp_data)
        temp_data = self.getting_child(tl_data, temp_data)
        #print temp_data.values()
        col_list = list(df.columns)

        col_dict = []
        for i in col_list:
            d = {}
            d["title"] = str(i.encode('utf-8')).capitalize()
            d["field"] = str(i.encode('utf-8'))
            # if i == 'name':
            #     d["headerFilter"] = "input"
            col_dict.append(d)
        return json.dumps({'col_name': col_dict, 'data': temp_data.values()})

    def getting_child(self,parent_data, temp_data):

        for key, value in parent_data.items():

            head_name = key
            if key in temp_data:
                temp_data[key]['name'] = key
                if len(value)>0:
                    temp_data[key]['_children']=[]
                    for val in value:
                        if val in temp_data:

                            temp_data[key]['_children'].append(temp_data[val])
                            del temp_data[val]

                    child_list = temp_data[key]['_children']
                    for child in child_list:
                        for k,v in child.items():
                            if k !='name'and k!='_children':

                                temp_data[key][k]+=child[k]
            else:
                print key

        return temp_data


    # def get_hh_list(self, query):
    #
    #     table_html = df.to_html(classes=table_classes)
    #     filename = ''
    #     data = {'table': table_html,
    #             'filename': filename}
    #     # print table_html
    #     return json.dumps(data)


"""
END OF Table Config
"""

