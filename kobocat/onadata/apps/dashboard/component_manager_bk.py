from onadata.apps.dashboard.forms import *
from onadata.apps.dashboard.models import *
import json

import simplejson as sjson


"""
*****************COMPONENT(Graph/Table/Map/Customized Something) CREATION  *******************


**To Introduce TYPE of Component:
1. Create a class that implements Component Interface
2. execute function returns a Dictionary having these attribute:
    'chart_html'
    'js_chart_calling_function'
    'js_chart_calling_function_with_param'
3. Add Newly Created Class inside ComponentManager Class (get_chart_content function)
"""

class Component:
    """
    Interface For Any Component, Ex- Graph, Table, Map ect
    """

    def execute(self):
        """
        :return: JSON having these attribute 'chart_html', 'js_chart_calling_function' ,'js_chart_calling_function_with_param'
        """
        pass


class ComponentManager:
    """
    ENTRY POINT
    Create COMPONENT/ CHART For each navigation Tab
    """

    def __init__(self, nav_id):
	print "navigation id"+str(nav_id)
        self.nav_id = nav_id
        self.components = []
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''

    def get_chart_content(self):
        """
        GET ALL HTML and JS Content
        :return: JSON having these attribute 'chart_html', 'js_chart_calling_function' ,'js_chart_calling_function_with_param'
        """
        max_content_row = DashboardGenerator.objects.filter(navigation_bar_id=self.nav_id).latest('content_row').content_row
        print "###############Max content Row ################"
        #print max_content_row
        chart_defs = DashboardGenerator.objects.filter(navigation_bar_id=self.nav_id).order_by(
            'content_order')
        for chart_def in chart_defs:
            if chart_def.content_type == 0:  # GRAPH
                self.components.append(Graph(chart_def))
            elif chart_def.content_type == 1:  # Table
                self.components.append(SimpleTable(chart_def))
            elif chart_def.content_type == 2:  # MAP
                self.components.append(SimpleMap(chart_def))
            elif chart_def.content_type == 3:  # Customized Component
                self.components.append(CustomizedComponent(chart_def))
            elif chart_def.content_type == 4:  # Card Component
                self.components.append(Cards(chart_def))
                # Add New Component here................

        for i in range(max_content_row+1):
            self.chart_html += '<div class="row">'
            for c in self.components:
                if c.row==i:
                    jsondata = c.execute()

                    # print "############# CHART ##############"
                    # print jsondata['chart_html']
                    self.chart_html += jsondata['chart_html']
                    self.js_chart_calling_function += jsondata['js_chart_calling_function']
                    self.js_chart_calling_function_with_param += jsondata['js_chart_calling_function_with_param']
            self.chart_html += '</div>'



            # print i+1
            # chart_defs = DashboardGenerator.objects.filter(navigation_bar_id=self.nav_id, content_row=i+1).order_by('content_order')
            # print chart_defs
            # for chart_def in chart_defs:
            #     if chart_def.content_type == 0:  # GRAPH
            #         self.components.append(Graph(chart_def))
            #     elif chart_def.content_type == 1:  # Table
            #         self.components.append(SimpleTable(chart_def))
            #     elif chart_def.content_type == 2:  # MAP
            #         self.components.append(SimpleMap(chart_def))
            #     elif chart_def.content_type == 3:  # Customized Component
            #         self.components.append(CustomizedComponent(chart_def))
            #     elif chart_def.content_type == 4:  # Card Component
            #         self.components.append(Cards(chart_def))
            #         # Add New Component here................

        print self.js_chart_calling_function

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class Graph(Component):
    """
    Graph is a Component
    Its Taking Data from Chart Definition and making Required HTML and JS Functions
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def
        self.row =chart_def.content_row


    def execute(self):
        """
        Get HTML and JS for GRAPH
        :return: JSON
        """
	print "graph"
        appearance = sjson.loads(self.chart_def.chart_object)
        width = "100%"
        md = '3'
        div_row=''
        customized = False





        if "customized" in appearance:
            customized = appearance["customized"]
	#font-weight: bold !important;
	tab_title =''
        if "head" in appearance and appearance["head"] !='':
            print "head"
            print appearance["head"]
            tab_title = "<div class='portlet-title' style='width:100%'>" + appearance["head"] + "</div>"

        self.chart_html += tab_title
        if "width" in appearance:
            width = int(appearance["width"])
            if width<=30 and width>25:
                md = '4'
            if width>30 and width<=50:
                md = '6'
            if width>50 and width<=75:
                md= '8'
            if width>75 and width<=100:
                md = '12'
                # self.chart_html +='<div class="row">'
                # div_row = '</div>'
        if customized == False:
            self.chart_html +="""

            <div    class="col-md-{md} middle-item">
                <div  id="{element_id}">
                </div>
            </div>

            """.format(md=md, element_id=self.chart_def.element_id);
        self.chart_html +=div_row
        self.js_chart_calling_function += """
                mpowerRequestForChart("{post_url}", "{element_id}", {chart_object}, {{}});
            """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id, chart_object=self.chart_def.chart_object)


        self.js_chart_calling_function_with_param += """
                        mpowerRequestForChart("{post_url}", "{element_id}", {chart_object}, parameters);
            """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id, chart_object=self.chart_def.chart_object)
        # print self.chart_html

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function, 'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class SimpleTable(Component):
    """
    SimpleTable is a Component
    Its Taking Data from Chart Definition and making Required HTML and JS Functions For SimpleTable Generation
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def
        self.row = chart_def.content_row

    def execute(self):
        """
        Get HTML and JS for table
        :return: JSON
        """



        print "table"
        appearance = sjson.loads(self.chart_def.chart_object,strict=False)
        width = "100%"
        md = '3'
        if "width" in appearance:
            width = int(appearance["width"])
            if width<=30 and width>25:
                md = '4'
            if width>30 and width<=50:
                md = '6'
            if width>50 and width<=75:
                md= '8'
            if width>75 and width<=100:
                md = '12'



        tab_title =''
        if "head" in appearance:
	        #print "head"
	        #print appearance["head"]
            	tab_title = "<div class='portlet-title'>"+appearance["head"]+"</div>"


        self.chart_html += tab_title

        self.chart_html += """
                    <div   class="col-md-{md} middle-item">

                        <div id="{element_id}_parent"></div>

                    </div>
                    """.format(md=md, element_id=self.chart_def.element_id)


        self.js_chart_calling_function += """
                        mpowerRequestForTable("{post_url}", "{element_id}", {chart_object}, {{}});
                    """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id,
                               chart_object=self.chart_def.chart_object)

        self.js_chart_calling_function_with_param += """
                                mpowerRequestForTable("{post_url}", "{element_id}", {chart_object}, parameters);
                    """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id,
                               chart_object=self.chart_def.chart_object)
        #print self.chart_html

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class SimpleMap(Component):
    """
    SimpleMap is a Component
    Its Taking Data from Chart Definition and making Required HTML and JS Functions For SimpleMap Generation
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def
        self.row = chart_def.content_row


    def execute(self):



        appearance = sjson.loads(self.chart_def.chart_object)
        width = "100%"
        if "width" in appearance:
            width = appearance["width"];

        tab_title = ''

        if "head" in appearance:
            print "head"
            print appearance["head"]
            tab_title = "<div class='dashboard-full-width'><h3 style=' margin-top:20px; text-align: center;' class='dashboard-	title'>" + \
                    appearance["head"] + "</h3></div>"


        self.chart_html += tab_title

        self.chart_html += """
            <div style="width:{width}%" class="map" id="{element_id}"></div>
            <div id="legend" class="legend"></div>
        """.format(width=width, element_id=self.chart_def.element_id)


        self.js_chart_calling_function += """
                                mpowerRequestForMap("{post_url}", "{element_id}", {chart_object}, {{}});
                            """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id,
                                       chart_object=self.chart_def.chart_object)

        self.js_chart_calling_function_with_param += """
                                        mpowerRequestForMap("{post_url}", "{element_id}", {chart_object}, parameters);
                            """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id,
                                       chart_object=self.chart_def.chart_object)

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class CustomizedComponent(Component):
    """
    CustomizedComponent is a Component
    Its Reading HTML AND JS Directly from DB
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def
        self.row = chart_def.content_row

    def execute(self):


        appearance = json.loads(self.chart_def.chart_object)
        width = "100"
        if "width" in appearance:
            width = appearance["width"]

        # self.chart_html += '<div id="' + self.chart_def.element_id + '" style="width:' + str(
        #     width) + '%" class="middle-item ">' + self.chart_def.html_code + '</div>'

        self.chart_html += """
                    <div id="{element_id}" style="width:{width}%" class="middle-item ">
                        {html_code}
                    </div>
                """.format(width=width, element_id=self.chart_def.element_id, html_code=self.chart_def.html_code)

        if self.chart_def.js_code is not None:
            if "@parameter" in self.chart_def.js_code:
                global_caller = self.chart_def.js_code
                filter_caller = self.chart_def.js_code
                global_caller = global_caller.replace("@parameter", "{}")
                filter_caller = filter_caller.replace("@parameter", "parameters")
                self.js_chart_calling_function += global_caller
                self.js_chart_calling_function_with_param += filter_caller
            else:
                self.js_chart_calling_function += self.chart_def.js_code
                self.js_chart_calling_function_with_param += self.chart_def.js_code

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}


class Cards(Component):
    """
    Cards is a Component
    Its Taking Data from Card Definition and making Required HTML and JS Functions For SimpleTable Generation
    """

    def __init__(self, chart_def):
        self.chart_html = ''
        self.js_chart_calling_function = ''
        self.js_chart_calling_function_with_param = ''
        self.chart_def = chart_def
        self.row = chart_def.content_row

    def execute(self):
        """
        Get HTML and JS for cards
        :return: JSON
        """




        appearance = sjson.loads(self.chart_def.chart_object,strict=False)
        width = "25"
        color = 'green'
        md = '3'
        if "width" in appearance:
            width = int(appearance["width"])
            if width < 25:
                md = '2'
            if width > 25 and width <= 30 :
                md = '4'
            if width > 30 and width <= 50:
                md = '6'
            if width > 50 and width <= 75:
                md = '8'
            if width > 75 and width <= 100:
                md = '12'

        if "colors" in appearance:
            color = appearance["colors"]

        tab_title =''
        if "head" in appearance and  appearance["head"] !='':
	        #print "head"
	        #print appearance["head"]
            	tab_title = "<div style='width:100%' class='portlet-title'>"+appearance["head"]+"</div>"


        self.chart_html += tab_title

        self.chart_html += """
                    <div    class="middle-item col-md-{md}  ">

                        <div id="{element_id}" class = "dashboard-stat {color}" style="min-height: 120px;"></div>

                    </div>
                    """.format(md=md,tab_title=tab_title, element_id=self.chart_def.element_id,color=color)


        self.js_chart_calling_function += """
                        mpowerRequestForCard("{post_url}", "{element_id}", {chart_object}, {{}});
                    """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id,
                               chart_object=self.chart_def.chart_object)

        self.js_chart_calling_function_with_param += """
                                mpowerRequestForCard("{post_url}", "{element_id}", {chart_object}, parameters);
                    """.format(post_url=self.chart_def.post_url, element_id=self.chart_def.element_id,
                               chart_object=self.chart_def.chart_object)
        #print self.chart_html

        return {'chart_html': self.chart_html, 'js_chart_calling_function': self.js_chart_calling_function,
                'js_chart_calling_function_with_param': self.js_chart_calling_function_with_param}
