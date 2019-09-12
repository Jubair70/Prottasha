/***
 * Dropdown ELEMENT CREATE
 * @param element  --New created element id field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function dropdownControlCreate(element, parent_div_id, control_name, control_label, has_cascaded_element, jsondata, appearance, username) {
    var col_md = 12;
    if ('col_md' in appearance)
        col_md = appearance['col_md'];
    var wrapper_class = ""
    if ('wrapper_class' in appearance)
        wrapper_class = appearance['wrapper_class'];

    //Default value select
    var select_default = '#none';
    if ('select_default' in appearance)
        select_default = appearance['select_default'];


    //Select 1st option
    var select_initial = false;
    if ('select_initial' in appearance)
        select_initial = appearance['select_initial'];
    if (select_initial == true) select_initial = 'selected';

    var start_wrapper = '<div class ="  "> <div class ="col-md-' + col_md + ' ' + wrapper_class + ' " >';
    var end_wrapper = '</div></div>';
    var label = '<label>' + control_label + '</label>';
    var dropdown_html = start_wrapper + label + '<select style="width:100%" id="' + element + '" name="' + control_name + '" class="form-control" onchange="' + has_cascaded_element + '"> <option value="">Select</option>';

    if (jsondata) {
        for (var i = 0; i < jsondata.length; i++) {
            if (jsondata[i].id == select_default) select_initial = 'selected';
            dropdown_html += '<option ' + select_initial + '    value="' + jsondata[i].id + '">' + jsondata[i].name + '</option>';
            select_initial = '';
        }
    }
    dropdown_html += '</select>' + end_wrapper;
    $("#" + parent_div_id).append(dropdown_html);
} //END of checkboxControlCreate


/***
 * Button (Submit Type) CREATE
 * @param element  --New created element id field
 * @param parent_div_id  -- parent div of new elements
 * @param control_label -- visible label
 *
 * @author persia
 */
function buttonControlCreate(element, parent_div_id, control_label) {
    var start_wrapper = '<div class="mp_submit" ><div class ="col-md-2" >  ';
    var end_wrapper = '</div></div>';
    var button_html = start_wrapper + '<input id="' + element + '" type="submit" class="btn btn-primary"  value="' + control_label + '"     >' + end_wrapper;
    $("#" + parent_div_id).append(button_html);
} //END of checkboxControlCreate


/***
 * Multiple Select ELEMENT CREATE
 * @param element  --New created element id field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function multipleSelectControlCreate(element, parent_div_id, control_name, control_label, has_cascaded_element, jsondata, appearance, username) {
    if (jsondata == null) {
        console.log(control_label + " element cannot be created -mpower");
        return;
    }
    var col_md = 12;
    if ('col_md' in appearance)
        col_md = appearance['col_md'];
    var wrapper_class = ""
    if ('wrapper_class' in appearance)
        wrapper_class = appearance['wrapper_class'];
    var start_wrapper = '<div class ="  "> <div class ="col-md-' + col_md + ' ' + wrapper_class + '" >';
    var end_wrapper = '</div></div>';
    var label = '<label class="control-label">' + control_label + '</label> <div  >';
    var multiple_select_html = start_wrapper + label + '<select multiple="multiple"   onchange="' + has_cascaded_element + '" id="' + element + '" name="' + control_name + '" class="form-control">';
    for (var i = 0; i < jsondata.length; i++) {
        multiple_select_html += '<option value="' + jsondata[i].id + '">' + jsondata[i].name + '</option>';
    }
    multiple_select_html += '</select></div>' + end_wrapper;
    $("#" + parent_div_id).append(multiple_select_html);
    console.log("here In multiselect " + element);
    handleMultipleSelect(element);
} //END of multipleSelectControlCreate


/***
 * CHECKBOX ELEMENT CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function checkboxControlCreate(element, parent_div_id, control_name, control_label, jsondata) {
    var start_wrapper = '<div class ="controls  "> <div class ="form-group" >';
    var end_wrapper = '</div></div>';
    var label = '<label>' + control_label + '</label>';
    var checkbox_html = start_wrapper + label + '<div class="checkbox-list">';
    for (var i = 0; i < jsondata.length; i++) {
        checkbox_html += '<label><input class="' + element + '" type="checkbox" name="' + control_name + '" value="' + jsondata[i].id + '">' + jsondata[i].name + '</label>';
    }
    checkbox_html += '</div>' + end_wrapper;
    $("#" + parent_div_id).append(checkbox_html);
} //END of checkboxControlCreate


/***
 * Radio button ELEMENT CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param jsondata  --json having id and name
 *
 * @author persia
 */
function radioControlCreate(element, parent_div_id, control_name, control_label, jsondata) {
    var start_wrapper = '<div class ="controls  "> <div class ="form-group" >';
    var end_wrapper = '</div></div>';
    var label = '<label>' + control_label + '</label>';
    var radio_html = start_wrapper + label + '<div class="checkbox-list">';
    for (var i = 0; i < jsondata.length; i++) {
        radio_html += '<label><input class="' + element + '" type="radio" name="' + control_name + '" value="' + jsondata[i].id + '">' + jsondata[i].name + '</label>';
    }
    radio_html += '</div>' + end_wrapper;
    $("#" + parent_div_id).append(radio_html);
} //END of radioControlCreate


/***
 * range slider  ELEMENT CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param appearance  --json having initial value, range
 *
 * @author zinia
 */
function sliderControlCreate(element, parent_div_id, control_name, control_label, appearance) {
    var col_md = 12;
    var initial = 100;
    var range = "min";
    if ('col_md' in appearance)
        col_md = appearance['col_md'];
    if ('initial' in appearance)
        initial = appearance['initial'];
    if ('range' in appearance)
        range = appearance['range'];

    var start_wrapper = '<div class ="col-md-' + col_md + ' controls " > <div class ="form-group" >';
    var end_wrapper = '</div></div>';
    var label = '<label>' + control_label + '</label>';
    var slider_html = start_wrapper + '<p> ' + label + ': <input type = "text" id = "no_' + element + '"style = "border:0; color:#b9cd6d; font-weight:bold;"  > <input type="hidden" id="' + element + '" value = "" class="form_control" name="' + control_name + '"></p>';
    slider_html += '<div id = "slider_' + element + '"></div>' + end_wrapper;
    $("#" + parent_div_id).append(slider_html);
    handleSlider(element, initial, range);
}

/***
 * Date Field CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param initialdate  --initial date
 *
 * @author zinia
 */
function dateControlCreate(element, parent_div_id, control_name, control_label, appearance_json, initialdate) {

    var start_wrapper = '<div class ="controls "> <div class ="col-md-12" > ';
    var end_wrapper = '</div></div>';
    var label = '<label>' + control_label + '</label>';
    var date_input_html = start_wrapper + label + '<div class="input-group input-medium date " >';
    date_input_html += '<input type="text" id="' + element + '" name="' + control_name + '" class="form-control datepicker"    /> ';
    date_input_html += '<span class="input-group-btn"><button class="btn default" type="button"><i class="fa fa-calendar"></i></button></span>' + end_wrapper;

    $("#" + parent_div_id).append(date_input_html);

    handleDatePickers(appearance_json);

} //END of radioControlCreate


/***
 * TEXT Input Field CREATE
 * @param element  --New created element class field
 * @param parent_div_id  -- parent div of new elements
 * @param control_name   -- name field of control
 * @param control_label -- visible label
 * @param initialvalue  --initial value
 *
 * @author persia
 */
function textinputControlCreate(element, parent_div_id, control_name, control_label, initialvalue) {
    var start_wrapper = '<div class ="controls  "> <div class ="form-group" > ';
    var end_wrapper = '</div></div>';
    var label = '<label>' + control_label + '</label>';
    var text_input_html = start_wrapper + label;
    text_input_html += '<input type="text" id="' + element + '" name="' + control_name + '" class="form-control" value="' + initialvalue + '" /> ' + end_wrapper;
    $("#" + parent_div_id).append(text_input_html);
    //handleDatePickers();
} //END of textinputControlCreate


/**
 * Bootstrap Datepicker Function
 * @param element
 *
 * @author zinia
 */
var handleDatePickers = function (appearance_json) {
    // rtl: App.isRTL(),
    appearance_json["autoclose"] = true;
    console.log(appearance_json);
    $('.datepicker').datepicker(appearance_json);
    if (jQuery().datepicker) {
        $('.datepicker').datepicker(appearance_json);
        $('body').removeClass("modal-open"); // fix bug when inline picker is used in modal
    }


} // End of handleDatePickers


/**
 * Bootstrap Multiple Select Function
 * @param element
 *
 * @persia
 */
var handleMultipleSelect = function (element) {
    console.log("everything");
    console.log('All selected');
    $("#" + element).multiselect({
        enableFiltering: true,
        //filterBehavior: 'value',
        maxHeight: 200,
        numberDisplayed: 1,
        includeSelectAllOption: true,
        buttonWidth: '100%',
        allSelectedText: 'All Selected'
    });
}

/**
 * Bootstrap slider function
 * @param element
 * @param initial value
 * @param range
 * @author zinia
 */
var handleSlider = function (element, initial, range) {

    $("#no_" + element).val(" 0 - " + initial);
    $("#" + element).val("" + initial);
    $("#slider_" + element).slider({
        range: "min",
        min: 0,
        max: 200,
        value: initial,
        change: function (event, ui) {
            console.log(ui.value);
            $("#no_" + element).val(" 0 - " + ui.value);
            $("#" + element).val("" + ui.value);
            //console.log(ui.values[0]); console.log(ui.values[1]);

        }
    });
}


function onChangeElement_pre(control_id, changed_val) {
    $.ajax({
        type: 'POST',
        url: '/dashboard/on_change_element/',
        data: {'control_id': control_id, 'changed_val': changed_val},
        beforeSend: function () {
        },
        success: function (data) {
            $('#' + data.element).find('option').remove();//.append('<option value="">Select</option>);
            dropdown_html = '<option value="">Select</option>';
            jsondata = JSON.parse(data.jsondata);
            if (jsondata) {
                for (var i = 0; i < jsondata.length; i++) {
                    dropdown_html += '<option value="' + jsondata[i].id + '">' + jsondata[i].name + '</option>';
                }
            }
            $('#' + data.element).append(dropdown_html);
        },
        error: function (data) {
        }
    });
} //END of onChangeElement


function onChangeElement(control_id, changed_val, nav_id) {
    console.log(nav_id);
    parameters = $('#form_' + nav_id).serializeArray();
    parameters.push({name: 'control_id', value: control_id})
    console.log(parameters);
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });
    $.ajax({
        type: 'POST',
        url: '/dashboard/on_change_element/',
        data: parameters,
        beforeSend: function () {
        },
        success: function (data) {
            try {
                jsondata = JSON.parse(data.jsondata);
            } catch (e) {
                jsondata = data.jsondata;
            }
            if (jsondata) {
                var keys = Object.keys(jsondata);
                for (var i = 0; i < keys.length; i++) {
                    $('#' + keys[i]).find('option').remove();
                    var dropdown_html = '<option value="">Select</option>';
                    var option_data = jsondata[keys[i]]['data'];
                    console.log(option_data);
                    for (var j = 0; j < option_data.length; j++) {
                        dropdown_html += '<option value="' + option_data[j].id + '">' + option_data[j].name + '</option>';
                    }
                    console.log("Onchange Single select");
                    console.log(keys[i]);
                    $('#' +keys[i]).append(dropdown_html);
                    console.log(dropdown_html);
                    if (jsondata[keys[i]]['control_type'] == 'multiple_select') {
                        $('#' + keys[i]).multiselect('rebuild');
                    }

                }
            }
        },
        error: function (data) {
        }
    });
} //END of onChangeElement

function onChangeMultipleSelect(control_id, changed_val, nav_id) {
    parameters = $('#form_' + nav_id).serializeArray();
    parameters.push({name: 'control_id', value: control_id})
    console.log(parameters);

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });
    $.ajax({
        type: 'POST',
        url: '/dashboard/on_change_multiple_select/',
        data: parameters,
        beforeSend: function () {
        },
        success: function (data) {
            var jsondata = ''
            try {
                console.log("JSON");
                jsondata = JSON.parse(data.jsondata);
            } catch (e) {
                jsondata = data.jsondata;
            }
            if (jsondata) {
                var keys = Object.keys(jsondata);
                for (var i = 0; i < keys.length; i++) {
                    console.log(keys[i]);
                    data = JSON.parse(jsondata[keys[i]]['data']);
                    $('#' + keys[i] + "  option").remove();
                    var multiple_select_html = ''
                    if (data) {
                        for (var j = 0; j < data.length; j++) {
                            multiple_select_html += '<option value="' + data[j].id + '">' + data[j].name + '</option>';
                        }
                    }

                    $('#' + keys[i]).append(multiple_select_html);
                    if (jsondata[keys[i]]['control_type'] == 'multiple_select') {
                        $('#' + keys[i]).multiselect('rebuild');
                    }
                    // $('#' + keys[i]).multiselect('rebuild');
                }
            }
        },
        error: function (data) {
        }
    });
} //END of onChangeMultipleSelect

function onChangeMultipleSelect_pre(control_id, changed_val) {

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: '/dashboard/on_change_multiple_select/',
        data: {'control_id': control_id, 'changed_val': changed_val},
        beforeSend: function () {
        },
        success: function (data) {

            "change by zinia"
            //$('#'+data.element).multiselect('destroy');
            var jsondata = ''
            try {
                console.log("JSON");
                jsondata = JSON.parse(data.jsondata);

            } catch (e) {
                // You can read e for more info
                // Let's assume the error is that we already have parsed the payload
                // So just return that
                console.log("java script object");
                jsondata = data.jsondata;
            }


            // jsondata=JSON.parse(data.jsondata);
            console.log("DELETED");
            console.log(jsondata)
            if (jsondata) {
                var keys = Object.keys(jsondata);

                for (var i = 0; i < keys.length; i++) {
                    console.log(keys[i]);
                    data = JSON.parse(jsondata[keys[i]]);
                    console.log("removed options")
                    console.log(data)
                    console.log("removed options")
                    $('#' + keys[i] + "  option").remove();
                    var multiple_select_html = ''
                    if (data) {

                        for (var j = 0; j < data.length; j++) {
                            multiple_select_html += '<option value="' + data[j].id + '">' + data[j].name + '</option>';
                        }
                    }
                    console.log(multiple_select_html)

                    $('#' + keys[i]).append(multiple_select_html);
                    //$('#'+data.element).multiselect('refresh');
                    $('#' + keys[i]).multiselect('rebuild');

                }
            }


            "change by zinia"


            // $('#'+data.element +"  option").remove();
            // var multiple_select_html=''//'<option value="">Select</option>' ;
            // if(jsondata){
            //     for (var i = 0; i < jsondata.length; i++) {
            //         multiple_select_html += '<option value="'+jsondata[i].id+'">'+jsondata[i].name+'</option>';
            //     }
            //  }
            // $('#'+data.element).append(multiple_select_html);
            // //$('#'+data.element).multiselect('refresh');
            // $('#'+data.element).multiselect('rebuild');
            // //handleMultipleSelect(data.element);

        },
        error: function (data) {
        }
    });
} //END of onChangeElement


/**
 * Asynchronous request For Chart generation
 * @author persia
 **/
function mpowerRequestForChart(post_url, element, chart_object, filtering) {

    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function () {
            $(element).html("Please Wait...loading....");
        },
        success: function (data) {
            console.log("Here in Graph");
            console.log(chart_object);
            chart_object['filtering'] = filtering;
            chart_object['dataset'] = data;
            mPowerChartGeneration(chart_object);
        },
        error: function (data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForChart


/**
 * Chart Generation Function
 * @author persia
 * @param obj -> containing all properties including dataset
 */
function mPowerChartGeneration(obj) {

    //All Variable Declaration
    var height, filtering, divId, chartType, stackLabelEnabled, plotColumnDatalabelEnabled, stackLabelEnabled, chart_title, colorByPoint, colors, stacking, new_yAxis, legend_enabled, dataLabel, tooltip_text;

    var yAxis1_title, yAxis2_title, calculation_type, grouping, categoryfontSize;

    //**Exploring Chart Properties from object**


    //Mandatory properties
    dataset = obj['dataset'];
    console.log(dataset);
    divId = obj['element'];
    chartType = obj['chartType'];
    filtering = obj['filtering'];
    console.log("############################");
    console.log(filtering);

    for (var temp in filtering)
        if (filtering[temp]['name'] == 'cal_type') {
            calculation_type = filtering[temp]['value'];
            console.log(calculation_type);
        }

    if ('grouping' in obj)
        grouping = obj['grouping'];
    else grouping = true;
    //Optional properties
    if ('height' in obj)
        height = obj['height'];
    else height = 400;
    if ('categoryfontSize' in obj)
        categoryfontSize = obj['categoryfontSize'];
    else
        categoryfontSize = "11px";

    if ('title' in obj)
        chart_title = obj['title'];
    else chart_title = false;

    if ('stackLabelEnabled' in obj)
        stackLabelEnabled = obj['stackLabelEnabled'];
    else stackLabelEnabled = false;

    if ('plotColumnDatalabelEnabled' in obj)
        plotColumnDatalabelEnabled = obj['plotColumnDatalabelEnabled'];
    else plotColumnDatalabelEnabled = false;

    if ('stackLabelEnabled' in obj)
        chartType = obj['stackLabelEnabled'];
    else stackLabelEnabled = false;

    if ('colorByPoint' in obj)
        colorByPoint = obj['colorByPoint'];
    else colorByPoint = false;


    if ('legend_enabled' in obj)
        legend_enabled = obj['legend_enabled'];
    else legend_enabled = true;

    if ('yAxis1_title' in obj)
        yAxis1_title = obj['yAxis1_title'];
    else yAxis1_title = "No. of Participants";
    console.log(yAxis1_title);

    if ('yAxis2_title' in obj)
        yAxis2_title = obj['yAxis2_title'];
    else yAxis2_title = "";

    if ('colors' in obj)
        colors = obj['colors'];
    else
        colors = ['#058DC7', '#50B432', '#ED561B', '#DDDF00', '#24CBE5', '#64E572', '#FF9655', '#FFF263', '#6AF9C4'];
    //['#2f7ed8', '#0d233a', '#8bbc21', '#910000', '#1aadce','#492970', '#f28f43', '#77a1e5', '#c42525', '#a6c96a'];

    //colors = ['#4572A7', '#AA4643', '#89A54E', '#80699B', '#3D96AE',
    //'#DB843D', '#92A8CD', '#A47D7C', '#B5CA92'];
    //"colors": ["#058dc7","#50b432","#ed561b","#dddf00","#24cbe5","#64e572","#ff9655","#fff263","#6af9c4"]
    if ('stacking' in obj) {
        stacking = obj['stacking'];
        console.log(stacking);
    }
    else stacking = null;

    if ('yAxis' in obj)
        new_yAxis = obj['yAxis'];
    else new_yAxis = null;

    if ('dataLabel' in obj)
        dataLabel = obj['dataLabel'];
    else dataLabel = false;
    // fetching from filtering property
    //if ('cal_type' in obj)
//
//         var pieColors = (function () {
//     var colors = [],
//         base = Highcharts.getOptions().colors[0],
//         i;
//
//     for (i = 0; i < 10; i += 1) {
//         // Start out with a darkened base color (negative brighten), and end
//         // up with a much brighter color
//         colors.push(Highcharts.Color(base).brighten((i - 3) / 7).get());
//     }
//     return colors;
// }());

    /**************Customized HighCharts Theme**************/
    Highcharts.theme = {
        colors: colors,
        height: 1000,
        chart: {
            // backgroundColor: {
            //     linearGradient: [0, 0, 500, 500],
            //     stops: [
            //         [0, 'rgb(255, 255, 255)'],
            //         [1, 'rgb(240, 240, 255)']
            //     ]
            // },
            backgroundColor: '#FFFFFF',
        },
        title: {
            style: {
                color: '#000',
                font: 'bold 16px "Trebuchet MS", Verdana, sans-serif'
            }
        },
        subtitle: {
            style: {
                color: '#666666',
                font: 'bold 12px "Trebuchet MS", Verdana, sans-serif'
            }
        },

        legend: {
            itemStyle: {
                font: '9pt Trebuchet MS, Verdana, sans-serif',
                color: 'black'
            },
            itemHoverStyle: {
                color: 'gray'
            }
        },
        responsive: {
            rules: [{
                condition: {
                    //maxWidth: 500
                },
                chartOptions: {
                    legend: {
                        align: 'center',
                        verticalAlign: 'bottom',
                        layout: 'horizontal'
                    },
                    yAxis: {
                        labels: {
                            align: 'left',
                            x: 0,
                            y: -5
                        },
                        title: {
                            text: null
                        }
                    },
                    subtitle: {
                        text: null
                    },
                    credits: {
                        enabled: false
                    }
                }
            }]
        }
    };

    /*Highcharts.setOptions({
     chart: {
     backgroundColor: {
     linearGradient: [0, 0, 500, 500],
     stops: [
     [0, 'rgb(255, 255, 255)'],
     [1, 'rgb(240, 240, 255)']
     ]
     },
     borderWidth: 2,
     plotBackgroundColor: 'rgba(255, 255, 255, .9)',
     plotShadow: true,
     plotBorderWidth: 1
     }
     });*/
    Highcharts.setOptions(Highcharts.theme);
    var chart = {
        type: chartType,
        height: height,

    };
    var title = {
        text: chart_title,
    };


    var subtitle = {
        text: ' ',
    };
    var xAxis = {
        categories: dataset.categories,
        title: {
            enabled: false
        },
        labels: {
            style: {
                color: (Highcharts.theme && Highcharts.theme.textColor) || 'black',
                fontWeight: 'bold',

                "fontSize": categoryfontSize,

            }
        }
    };
    var yAxis = {
        allowDecimals: true,
        min: 0,
        title: {
            enabled: true,
            text: yAxis1_title
        }
    };

    /*stackLabels: {
     enabled: stackLabelEnabled,
     style: {
     fontWeight: 'bold',
     color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
     }

     }*/

    /*{
     allowDecimals: true,
     min: 0,
     title: {
     text: yAxis2_title
     },
     stackLabels: {
     enabled: stackLabelEnabled,
     style: {
     fontWeight: 'bold',
     color: (Highcharts.theme && Highcharts.theme.textColor) || 'gray'
     }
     },
     opposite: true
     }*/

    var legend = {
        layout: 'vertical',
        align: 'right',
        verticalAlign: 'top',
        enabled: legend_enabled
    };

    //Tooltip Options
    if (chartType == 'area') {
        tooltip_text = '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ';

    }
    else if (stacking == 'percent') {
        tooltip_text = '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ({point.percentage:.0f}%)<br/>';
    }
    else if (chartType == 'pie') {
        if (calculation_type == 'percentage') {
            tooltip_text = '<b>{point.name}</b>: {point.y} %'
        }
        else {
            tooltip_text = '<b>{point.name}</b>: {point.y}'
        }
    }
    else if (chartType == 'semi_donut') {
        if (calculation_type == 'percentage') {
            tooltip_text = '<b>{point.name}</b>: {point.y} %'
        }
        else {
            tooltip_text = '<b>{point.name}</b>: {point.y}'
        }
    }
    else if (chartType == 'bar') {
        if (calculation_type == 'percentage') {
            tooltip_text = '<b>{point.name}</b>: {point.y} %'
        }
        else {
            tooltip_text = '<b>{point.name}</b>: {point.y}'
        }
    }

    else {
        tooltip_text = '<span style="color:{series.color}">{point.name}</span>: <b>{point.y}</b> ';
    }

    var tooltip = {
        // pointFormat: '{series.name}: <b>{point.y:.1f}%</b>'
        //pointFormat: '<b>{point.y}</b>'
        pointFormat: tooltip_text

    };

    var series = dataset.seriesdata


    /****** Setting plotOptions according to chart type******/
    var plotOptions = {}
    if (chartType == 'bar') {
        plotOptions = {
            bar: {
                allowPointSelect: true,
                showInLegend: true,
                stacking: stacking,
                "grouping": grouping,
                shadow: false,
                borderWidth: 0,
                /*dataLabels: {
                 enabled: plotColumnDatalabelEnabled,
                 color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                 },*/
                colorByPoint: colorByPoint,
                dataLabels: {
                    enabled: dataLabel,
                    formatter: function () {
                        if (calculation_type == 'percentage') {
                            // return Highcharts.numberFormat(this.y) + '%';
                            return this.y + '%';
                        }
                        //if(this.percentage==null)
                        //  return this.y;
                        return this.y;
                        //return Math.round(this.percentage)   + '%';
                    }

                }
            }
        };
    }
    else if (chartType == 'column') {
        plotOptions = {
            column: {
                allowPointSelect: true,
                showInLegend: true,
                stacking: stacking,
                "grouping": grouping,
                shadow: false,
                borderWidth: 0,
                /*
                 dataLabels: {
                 enabled: plotColumnDatalabelEnabled,
                 color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                 },*/
                colorByPoint: colorByPoint,
                dataLabels: {
                    enabled: dataLabel,
                    formatter: function () {
                        if (calculation_type == 'percentage') {
                            // return Highcharts.numberFormat(this.y) + '%';
                            return this.y + '%';
                        }
                        //if(this.percentage==null)
                        //  return this.y;
                        return this.y;
                        //return Math.round(this.percentage)   + '%';
                    }
                }
            }

        };
    }
    else if (chartType == 'area') {
        plotOptions = {
            area: {
                stacking: stacking,
                allowPointSelect: true,
                showInLegend: true,
                dataLabels: {
                    enabled: dataLabel,
                    formatter: function () {
                        if (calculation_type == 'percentage') {
                            // return Highcharts.numberFormat(this.y) + '%';
                            return this.y + '%';
                        }
                        //if(this.percentage==null)
                        //  return this.y;
                        return this.y;
                        //return Math.round(this.percentage)   + '%';
                    }
                }
                /*dataLabels: {
                 enabled: plotColumnDatalabelEnabled,
                 color: (Highcharts.theme && Highcharts.theme.dataLabelsColor) || 'white'
                 },*/
            }

        };
    }
    else if (chartType == 'pie') {
        plotOptions = {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: true,
                    format: tooltip_text,
                    distance: -80,
                    /*style: {
                     color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                     }*/
                }
            }
        };
    }

    else if (chartType == 'donut') {
        console.log(chartType);
        plotOptions = {
            pie: {
                dataLabels: {
                    enabled: true,
                    distance: -50,
                    style: {
                        fontWeight: 'bold',
                        color: 'white'
                    },
                    format: tooltip_text,
                },
                startAngle: -180,
                endAngle: 180,
                center: ['50%', '50%'],
                size: '90%'
            }
        }
    }

    else if (chartType == 'semi_donut') {
        console.log(chartType);
        plotOptions = {
            pie: {
                dataLabels: {
                    enabled: true,
                    distance: -50,
                    style: {
                        fontWeight: 'bold',
                        color: 'white'
                    },
                    format: tooltip_text,
                },
                startAngle: -90,
                endAngle: 90,
                center: ['50%', '50%'],
                size: '90%'
            }
        }
    }


    var credits = {

        enabled: false
    }


    var exporting = {
        buttons: {
            contextButton: {
                enabled: true
            }
        }
    }

    var json = {};
    json.chart = chart;
    json.title = title;
    json.subtitle = subtitle;
    json.xAxis = xAxis;
    json.yAxis = yAxis;
    json.legend = legend;
    json.tooltip = tooltip;
    json.series = series;
    json.plotOptions = plotOptions;
    json.credits = credits;
    json.height = 700;
    json.exporting = exporting;
    //json.responsive=responsiveness;
    console.log("Here");
    console.log(divId);
    console.log(json);
    $('#' + divId).highcharts(json);


}


/**
 * Asynchronous request For Table generation
 * @author persia
 **/
function mpowerRequestForTable(post_url, element, chart_object, filtering) {

    var grouping = true, collapsed, readyHTML = false, treeHTML = false;
    if ('grouping' in chart_object)
        grouping = chart_object['grouping'];
    else grouping = false;

    if ('collapsed' in chart_object)
        collapsed = chart_object['collapsed'];
    else collapsed = false;

    if ('readyHTML' in chart_object)
        readyHTML = chart_object['readyHTML'];
    else readyHTML = false;

    if ('treeHTML' in chart_object)
        treeHTML = chart_object['treeHTML'];
    else treeHTML = false;

    console.log("For TAble ");
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function () {
            $(element).html("Please Wait...loading....");
        },
        success: function (dataset) {
            //console.log(dataset);
            if (grouping) {
                var json_dataset = JSON.parse(dataset);
                initGroupedDataTable(element, json_dataset.data, json_dataset.col_name, chart_object);
            }
            else if (collapsed) {
                var json_dataset = JSON.parse(dataset);
                initCollapsedDataTable(element, json_dataset.data, json_dataset.col_name, chart_object);
            }
            else if (readyHTML) {
                var json_dataset = JSON.parse(dataset);
                initReadyHTML(element, json_dataset, chart_object);
            }
            else if (treeHTML) {
                var json_dataset = JSON.parse(dataset);
                initTreeTable(element, json_dataset.data, json_dataset.col_name, chart_object);
            }

            else {
                var json_dataset = JSON.parse(dataset);
                initDataTable(element, json_dataset.data, json_dataset.col_name, chart_object);
            }
            $('#' + element).show();
        },
        error: function (data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForTable


/**
 * Asynchronous request For Card generation
 * @author persia
 **/
function mpowerRequestForCard(post_url, element, chart_object, filtering) {

    // var grouping=true,collapsed,readyHTML=false;
    // if('grouping'  in chart_object)
    //         grouping=chart_object['grouping'];
    //     else grouping=false;
    //
    // if('collapsed'  in chart_object)
    //         collapsed=chart_object['collapsed'];
    //     else collapsed=false;
    //
    // if('readyHTML'  in chart_object)
    //         readyHTML=chart_object['readyHTML'];
    //     else readyHTML=false;


    var calculation_type = 'number';
    for (var temp in filtering)
        if (filtering[temp]['name'] == 'cal_type') {
            calculation_type = filtering[temp]['value'];
            console.log(calculation_type);
        }
    console.log("For Cards calculation");
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });


    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function () {
            $(element).html("Please Wait...loading....");
        },
        success: function (dataset) {
            var json_dataset = JSON.parse(dataset);
            var body_html = ""
            console.log(chart_object);
            var visual = '<div class="visual"><i class=""></i> </div>';
            // visual = '';
            console.log(json_dataset.number);
            if (calculation_type == 'percentage' && json_dataset.percentage != '') {
                var details_html = ' <div class="details"><div class="number"><span class="count">' + json_dataset.percentage + '%</span></div><div class="desc">' + json_dataset.details + ' </div></div>'
                var progress_bar = '<div class ="more"><div class="progress mb-0" style="height: 7px;"> <div class="progress-bar progress-bar-striped"  role="progressbar" style="width: 80% ;background-color:#233F53" aria-valuenow="80" aria-valuemin="0" aria-valuemax="100"></div>';
            }
            else {
                var details_html = ' <div class="details"><div class="number"><span class="count">' + json_dataset.number + '</span></div><div class="desc">' + json_dataset.details + ' </div></div>'
                var progress_bar = '<div class ="more"><div class="progress mb-0" style="height: 7px;"> <div class="progress-bar progress-bar-striped"  role="progressbar" style="width: 80% ;background-color:#233F53" aria-valuenow="80" aria-valuemin="0" aria-valuemax="100"></div>';
            }

            body_html += visual + details_html;
            $("#" + element).html(body_html);
            $('#' + element).show();



        },
        error: function (data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForChart


/**
 * Asynchronous request For Map generation
 * @author persia
 **/
function mpowerRequestForMap(post_url, element, chart_object, filtering) {
    console.log(post_url + "    " + element + "    " + chart_object);
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                        if (cookie.substring(0, name.length + 1) == (name + '=')) {
                            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                            break;
                        }
                    }
                }
                return cookieValue;
            }

            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    $.ajax({
        type: 'POST',
        url: post_url,
        data: filtering,
        beforeSend: function () {
            $(element).html("Please Wait...loading....");
        },
        success: function (dataset) {
            dataset = JSON.parse(dataset);
            console.log("dataset " + dataset);
            chart_object['dataset'] = dataset;
            chart_object['element'] = element;
            mPowerMapGeneration(chart_object);
        },
        error: function (data) {
            $(element).html("Error occurred! Please reload.");
        }
    });
} // END of mpowerRequestForMap


/**
 * MAP Generation Function
 * @author persia
 * @param obj -> containing all properties including dataset
 */
function mPowerMapGeneration(obj) {

    //All Variable Declaration
    var divId, clustering;

    //**Exploring MAP Properties from object**

    //Mandatory properties
    dataset = obj['dataset'];
    divId = obj['element'];


    if ('clustering' in obj)
        clustering = obj['clustering'];
    else clustering = false;


    color_ranges = [['Excellent', 'darkgreen'], ['VeryGood', 'limegreen'], ['Good', 'lawngreen'], ['Satisfactory', 'orange'], ['Poor', 'red']];

    try {
        //SETTING DATA
        var geoJson = dataset;
        mapboxgl.accessToken = 'pk.eyJ1IjoiaWJ0YXNoYW0iLCJhIjoiY2lmejE0eGswNWpudXU3bHhoMXJ2Zm5weiJ9.5KD2N8Y7YiKI3DfdMZwodQ';
        var map = new mapboxgl.Map({
            container: divId,
            style: 'mapbox://styles/mapbox/streets-v8',
            center: [89.890137, 22.521279], //khulna 22.8456° N, 89.5403° E
            zoom: 8
        });


        map.on('load', function () {
            // Add a new source from our GeoJSON data and set the
            // 'cluster' option to true.
            map.addSource("earthquakes", {
                type: "geojson",
                // Point to GeoJSON data.
                data: geoJson, //"/geodata.geojson",
                cluster: clustering
                //clusterMaxZoom: 14, // Max zoom to cluster points on
                //clusterRadius: 50 // Radius of each cluster when clustering points (defaults to 50)

            });

            map.addLayer({
                'id': 'population',
                'type': 'circle',
                "source": "earthquakes",
                'source-layer': 'sf2010',
                'paint': {
                    // make circles larger as the user zooms from z12 to z22
                    'circle-radius': {
                        'base': 4,
                        'stops': [[12, 5], [22, 180]]
                    },
                    // color circles by ethnicity, using data-driven styles
                    'circle-color': {
                        property: 'title',
                        type: 'categorical',
                        stops: color_ranges
                    },
                    'circle-opacity': 0.8
                }
            });


            if (clustering == true) {
                // Display the earthquake data in three layers, each filtered to a range of
                // count values. Each range gets a different fill color.
                var layers = [
                    [150, '#f28cb1'],
                    [20, '#f1f075'],
                    [0, '#51bbd6']
                ];

                layers.forEach(function (layer, i) {
                    map.addLayer({
                        "id": "cluster-" + i,
                        "type": "circle",
                        "source": "earthquakes",
                        "paint": {
                            "circle-color": layer[1],
                            "circle-radius": 18
                        },
                        "filter": i == 0 ?
                            [">=", "point_count", layer[0]] :
                            ["all",
                                [">=", "point_count", layer[0]],
                                ["<", "point_count", layers[i - 1][0]]]
                    });
                });

                // Add a layer for the clusters' count labels
                map.addLayer({
                    "id": "cluster-count",
                    "type": "symbol",
                    "source": "earthquakes",
                    "layout": {
                        "text-field": "{point_count}",
                        "text-font": [
                            "DIN Offc Pro Medium",
                            "Arial Unicode MS Bold"
                        ],
                        "text-size": 12
                    }
                });
            } //END Clustering check if

            //LEGEND and Toolbar For https://www.mapbox.com/help/gl-dds-map-tutorial/


        });


        //Adding Legend

        map.addControl(new mapboxgl.Navigation());


        /***
         * LEGEND: Right Corner of MAP
         * Commented Due to Reuirement Update
         */
        /*
         var labels=""
         for (var i = 0; i < color_ranges.length; i++) {
         eachcolor = color_ranges[i];
         console.log("eachcolor  "+eachcolor);
         labels+='<div><span style="width: 15px; height: 15px; margin:auto; display: inline-block;  background-color:' + eachcolor[1] + ';"></span> ' + eachcolor[0] + '</div>';
         }
         $("#legend").html("<h4>Qualification</h4>"+labels);
         */

        var popup = new mapboxgl.Popup({
            closeButton: true,
            closeOnClick: true
        });


        map.on('mousemove', function (e) {
            var features = map.queryRenderedFeatures(e.point, {layers: ['population']});
            if (!features.length)
                return;
            var feature = features[0];

            // Populate the popup and set its coordinates
            // based on the feature found
            popup.setLngLat(feature.geometry.coordinates)
                .setHTML('<div id=\'popup\' class=\'popup\' style=\' padding: 0px 22px 0px; z-index: 10;\'> <h5> Detail:    </h5>' +
                    '<ul class=\'list-group\'>' +
                    '<li class=\'list-item\'> Qualification:  <span style="width: 15px; height: 15px; margin:auto; display: inline-block;  background-color:' + feature.properties['color'] + ';"></span> ' + feature.properties['title'] + '  </li>' +
                    '<li class=\'list-item\'> Score: <b>' + feature.properties['score'] + ' </b></li>' +
                    '<li class=\'list-item\'> Zone: <b>' + feature.properties['Zone'] + ' </b></li>' +
                    '<li class=\'list-item\'> District: <b>' + feature.properties['District'] + ' </b></li>' +
                    '<li class=\'list-item\'> Polder: <b>' + feature.properties['Polder'] + ' </b></li>' +
                    '<li class=\'list-item\'> WMG Name: <b>' + feature.properties['name_wmg'] + ' </b></li>' +
                    '<li class=\'list-item\'> Date: <b>' + feature.properties['Date'] + ' </b></li></ul></div>')
                .addTo(map);
        });

        map.on('mouseleave', 'population', function () {
            popup.remove();
        });


    }
    catch (e) {
        console.log("MAP Loading Failed  " + e);
    }

}


/***
 * Navigation Filter Option OPEN onclick
 * @param nav
 * @param main
 */
function openNav(nav, main) {
    current_width = $("#" + nav).width();
    if (current_width == "0") {
        $("#" + nav).css('display', 'block');
        $("#" + nav).css('width', 302);
        $("#" + nav).css('right', 0)
        $("#icon_cross_" + nav).css('display', 'block');
        $("#icon_caret_" + nav).css('display', 'none');
        $("#" + nav).css('padding', 10);

    }
    $(main).attr('onClick', 'closeNav("' + nav + '", this);');
}


/***
 * Navigation Filter Option CLOSE onclick
 * @param nav
 * @param main
 */

function closeNav(nav, main) {
    $("#" + nav).css('padding', 0);
    $("#" + nav).css('width', 0);
    $(main).attr('onClick', 'openNav("' + nav + '", this);');
    $("#icon_cross_" + nav).css('display', 'none');
    $("#icon_caret_" + nav).css('display', 'block');
    $("#" + nav).css('display', 'none');
}


$("#parent_body").on("click", function () {
    console.log("U clicked in Body");
});

/********* Project Specific  Code********/

function create_wmg_tracker_report(element, filtering) {
    var chart_object = {}
    console.log("In data ");
    $.ajax({
        type: 'POST',
        url: "/dashboard/get_wmg_tracker_report/",
        data: filtering,
        beforeSend: function () {
            $("#" + element).html("Please Wait...loading....");
        },
        success: function (dataset) {
            $("#" + element).html("");
            dataset = JSON.parse(dataset);
            initCollapsedCustomizedDataTable(element, dataset.data, dataset.col_name, dataset.subtables, chart_object);
            $('#' + element).show();
        },
        error: function (data) {
            console.log("Data  Error");
            $(element).html("Error occurred! Please reload.");
        }
    });
}


/*************** TUP Specific Code ********************/
function enterprise_asset_training_report(element, filtering) {
    var chart_object = {}
    console.log("In data ");
    $.ajax({
        type: 'POST',
        url: "/dashboard/get_enterprise_option_graph/" + element + "/",
        data: filtering,
        beforeSend: function () {
            $("#" + element).html("Please Wait...loading....");
        },
        success: function (dataset) {
            $("#" + element).html("");
            dataset = JSON.parse(dataset);
            console.log(dataset);
            console.log("Here Data Fetch")
            var elements = Object.keys(dataset);
            for (var elem in dataset) {
                console.log(elem);
                var pDoc = document.getElementById(elem);
                var parentDiv = pDoc.parentElement;
                parentDiv.style.display = "none";
            }
        },
        error: function (data) {
            console.log("Data  Error");
            $(element).html("Error occurred! Please reload.");
        }
    });
}


function get_wmg_tracker_excel(filename) {
    console.log(" data " + "/dashboard/getExcel?" + filename);
    // location.href = "/dashboard/getExcel?path="+filename;
    window.open('/media/bg/exported_file/' + filename);


}

/**
 * Headline Generation Function
 * @author zinia
 * @param obj -> containing all properties including dataset
 */

function get_modified_headline(element, title, filtering) {
    var cohort = '';
    console.log('headline');
    console.log(filtering);
    for (var i = 0, n = filtering.length; i < n; ++i) {
        if (filtering[i].name == 'cohort_id') {
            cohort = filtering[i].value;
            console.log(filtering[i]);
        }
    }
    console.log(cohort);
    $.ajax({
        type: 'GET',
        url: "/dashboard/get_cohort_name/" + cohort + "/",
        beforeSend: function () {
            $("#" + element).html("Please Wait...loading....");
        },
        success: function (dataset) {
            $("#" + element).html("");
            dataset = JSON.parse(dataset);
            console.log(dataset.cohort_name);
            $("#" + element).html('<div  class="dashboard-full-width" ><h2 class="dashboard-title" ><span style="color:#808088;"><b>' + title + ' (' + dataset.cohort_name + ')</b></span></h2></div>');

        },
        error: function (data) {
            console.log("Data  Error");
            $(element).html("Error occurred! Please reload.");
        }
    });


}

// /********************************
//     *           Customizer          *
//     ********************************/
//     // Customizer toggle & close button click events  [Remove customizer code from production]
//     $('.customizer-toggle').on('click',function(){
//         $('.customizer').toggleClass('open');
//     });
//     $('.customizer-close').on('click',function(){
//         $('.customizer').removeClass('open');
//     });
//     if($('.customizer-content').length > 0){
//         $('.customizer-content').perfectScrollbar({
//             theme:"dark"
//         });
//     }
