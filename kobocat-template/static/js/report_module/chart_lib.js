/**
 * Created by devashish on 9/3/19.
 */
function generateBarChart(container, type, title, subtitle, categories, data_series, cat_label, tooltip_sym, cbp, showlegend, stacking, rotation, dlf, datasum, tooltipData, showtooltip, height,colors,filename,multiple) {
    var  tooltip_text;


    if (multiple == 'group'){
      tooltip_text = {headerFormat: '<span style="font-size:10px">{point.key}</span><table>',
        pointFormat: '<tr><td style="color:{series.color};padding:0">{series.name}: </td>' +
            '<td style="padding:0"><b>{point.y} </b></td></tr>',
        footerFormat: '</table>',
       shared: true,
        useHTML: true}
    }
    else {
        tooltip_text = {pointFormat:'<span style="color:{series.color}">{point.name}</span>: <b>{point.y}</b>',
        shared: true,
        useHTML: true}
    }

    Highcharts.setOptions({
        colors: colors,
    });
    var options = {
        legend: {
            enabled: showlegend
        },
        chart: {
            renderTo: container,
            type: type,
            height: height
        },
        title: {
            text: title,
            useHTML: true,
            style: {
                'white-space': 'normal',
                'text-align': 'center',
                'font-size': '16px',
                'font-weight': '400',
                'color': '#000'
            }
        },
        subtitle: {
            text: subtitle
        },
        xAxis: {
            categories: categories.map(function (x) {
                return capitalize(x)
            }),
            title: {
                text: null
            },
            reserveSpace: true
        },
        yAxis: {
            min: 0,
            title: {
                text: cat_label,
                align: 'high'
            },
            labels: {
                overflow: 'justify',
                formatter: function () {
                    if (datasum) {
                        return Math.round(this.value / datasum * 100) + "%";
                    } else {
                        return this.value + "";
                    }
                }
            }
        },
        tooltip: tooltip_text
        // {
        //     enabled: showtooltip,
        //     formatter: function () {
        //         if (tooltipData) {
        //             if (tooltipData['indicator_type'][0].trim() == this.x.trim()) {
        //                 var def = tooltipData['indicator_title'][0];
        //             } else if (tooltipData['indicator_type'][1].trim() == this.x.trim()) {
        //                 var def = tooltipData['indicator_title'][1];
        //             } else if (tooltipData['indicator_type'][2].trim() == this.x.trim()) {
        //                 var def = tooltipData['indicator_title'][2];
        //             } else if (tooltipData['indicator_type'][3].trim() == this.x.trim()) {
        //                 var def = tooltipData['indicator_title'][3];
        //             }
        //             return '<b><span style="font-size:12px">' + this.x + '</span></b><table><tr><td style="font-size:10px">' + def + '</td></tr><tr></td><td style="padding:0"><b>' + this.y + '' + tooltip_sym + '</b></td></tr></table>';
        //         } else {
        //             return '<b><span style="font-size:12px">' + this.x + '</span></b><table></tr><tr></td><td style="padding:0"><b>' + this.y + '' + tooltip_sym + '</b></td></tr></table>';
        //         }
        //     },
        //     shared: true,
        //     useHTML: true
        // }
        ,
        plotOptions: {
            series: {
                colorByPoint: cbp,
                dataLabels: {
                    formatter: function () {

                        // return this.y;
                        if (dlf) {
                            return Highcharts.numberFormat(this.y / datasum * 100, 1) + '%';
                        } else {
                            return this.y + tooltip_sym;
                        }
                    },
                    allowOverlap: true,
                    enabled: true,
                    rotation: rotation,
                    crop: false,
                    overflow: 'none'
                }
            },
            column: {
                dataLabels: {
                    enabled: true,
                    crop: false,
                    overflow: 'none'
                }
            }
        },
        exporting: {
            buttons: {
                exportButton: {
                    text: '<span><b>Export Data</b></span>',
                    onclick: function () {
                        // alert('You pressed the button!');
                        get_excel(filename);
                    }
                },

            }
        },
        credits: {
            enabled: false
        },
        series: data_series
    };

    var chart = new Highcharts.Chart(options);
}


function generatePieChart(container, title, subtitle, series_name, data_series) {
    Highcharts.setOptions({
        colors: ['#1e90ff', '#e65100', '#8d6e63', '#00c853']
    });

    var options = {
        chart: {
            renderTo: container,
            plotBackgroundColor: null,
            plotBorderWidth: 0,
            plotShadow: false,
            margin: [0, 0, 80, -100],
            height: 300
        },
        title: {
            text: title,
            useHTML: true,
            style: {
                'white-space': 'normal',
                'text-align': 'center',
                'font-size': '16px',
                'font-weight': '400',
                'color': '#000'
            }
        },
        subtitle: {
            text: subtitle
        },
        tooltip: {
            pointFormat: '<b>{point.percentage:.1f}%</b>'
        },
        plotOptions: {
            pie: {
                dataLabels: {
                    enabled: false,
                    distance: 20,
                    allowOverlap: true,
                    color: '#000000',
                    connectorColor: '#000000',
                    style: {
                        fontWeight: 'bold',
                        color: 'white'
                    }
                },
                showInLegend: true,
                startAngle: -270,
                endAngle: 90,
                center: ['50%', '75%']
            }
        },
        series: [{
            type: 'pie',
            name: series_name,
            innerSize: '50%',
            data: data_series
        }],
        legend: {
            align: 'right',
            verticalAlign: 'top',
            layout: 'vertical',
            x: 15,
            y: 100,
            useHTML: true,
            labelFormatter: function () {
                return '<div>' + this.name + ' (' + this.percentage.toFixed(1) + '%)</div>';
            },
            credits: {
                enabled: false
            }
        }
    }

    var chart = new Highcharts.Chart(options);

}


function generateSolidGauge(container, title, dataseries, suffix) {
    var gaugeOptions = {

        chart: {
            type: 'solidgauge',
            height: 300
        },

        title: null,

        pane: {
            center: ['50%', '85%'],
            size: '100%',
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                innerRadius: '60%',
                outerRadius: '100%',
                shape: 'arc'
            }
        },

        tooltip: {
            enabled: false
        },

        // the value axis
        yAxis: {
            lineWidth: 0,
            minorTickInterval: null,
            tickAmount: 2,
            title: {
                y: -160
            },
            labels: {
                y: 16
            }
        },

        plotOptions: {
            solidgauge: {
                dataLabels: {
                    y: -35,
                    borderWidth: 0,
                    useHTML: true
                }
            }
        }
    };

    var chart = Highcharts.chart(container, Highcharts.merge(gaugeOptions, {
        yAxis: {
            min: 0,
            max: 100,
            title: {
                text: title,
                useHTML: true,
                style: {
                    'white-space': 'normal',
                    'position': 'relative',
                    'text-align': 'center',
                    'font-size': '15px',
                    'padding': '5px',
                    'color': '#000'

                }
            }
        },

        credits: {
            enabled: false
        },

        series: [{
            name: 'Data',
            data: dataseries,
            dataLabels: {
                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y} ' + suffix + '</span></div>'
            },
            tooltip: {
                valueSuffix: ' ' + suffix
            }
        }]

    }));
}


function getDistricts(obj) {
    dv_id = obj.value;
    $.ajax({
        url: "/reportmodule/get_districts/",
        type: 'POST',
        data: {'dv_id': dv_id},
        dataType: 'json',
        success: function (response) {
            $('#district_id option:not(:first)').remove();
            for (var idx in response) {
                if (idx != 'sum') {
                    $('#district_id').append('<option value="' + response[idx].zl + '">' + response[idx].zila_name + '</option>');
                }
            }
        }
    });
}


function capitalize(string) {
    var splitStr = string.split(/[_-]+/);
    var fullStr = '';
    splitStr.forEach(function (element) {
        var currentSplit = element.charAt(0).toUpperCase() + element.slice(1);
        fullStr += currentSplit + " "
    });
    return fullStr;
}


function generateSingleSolidGauge(container, title, dataseries, suffix, rb) {
    var gaugeOptions = {

        chart: {
            type: 'solidgauge',
            height: 300
        },

        title: null,

        pane: {
            center: ['50%', '85%'],
            size: '100%',
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: (Highcharts.theme && Highcharts.theme.background2) || '#EEE',
                innerRadius: '60%',
                outerRadius: '100%',
                shape: 'arc'
            }
        },

        tooltip: {
            enabled: false
        },

        // the value axis
        yAxis: {
            lineWidth: 0,
            minorTickInterval: null,
            tickAmount: 2,
            title: {
                y: -160
            },
            labels: {
                y: 16
            }
        },

        plotOptions: {
            solidgauge: {
                dataLabels: {
                    y: -35,
                    borderWidth: 0,
                    useHTML: true
                }
            }
        }
    };

    var chart = Highcharts.chart(container, Highcharts.merge(gaugeOptions, {
        yAxis: {
            min: 0,
            max: rb,
            tickPositioner: function () {
                return [this.min, this.max];
            },
            title: {
                text: title,
                useHTML: true,
                style: {
                    'white-space': 'normal',
                    position: 'relative',
                    'text-align': 'center',
                    'font-size': '15px',
                    'padding': '5px',
                    'color': '#000'

                }
            }
        },

        credits: {
            enabled: false
        },

        series: [{
            name: 'Data',
            data: dataseries,
            dataLabels: {
                format: '<div style="text-align:center"><span style="font-size:25px;color:' +
                ((Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black') + '">{y} ' + '</span></div>'
            },
            tooltip: {
                valueSuffix: ' ' + suffix
            }
        }]

    }));
}


function generateStackedBarChart(container, type, title, subtitle, categories, data_series, cat_label, tooltip_sym, cbp, showlegend, stacking, rotation, dlf, datasum, tooltipData, showtooltip, height) {
    var options = {
        legend: {
            enabled: showlegend,
            reversed: true
        },
        chart: {
            renderTo: container,
            type: 'bar',
            height: height
        },
        title: {
            text: title,
            useHTML: true,
            style: {
                'white-space': 'normal',
                'text-align': 'center',
                'font-size': '16px',
                'font-weight': '400',
                'color': '#000'
            }
        },
        subtitle: {
            text: subtitle
        },
        xAxis: {
            categories: categories.map(function (x) {
                return capitalize(x)
            }),
            title: {
                text: null
            },
            reserveSpace: true
        },
        yAxis: {
            min: 0,
            title: {
                text: cat_label,
                align: 'high'
            },
            labels: {
                overflow: 'justify',
                formatter: function () {
                    if (datasum) {
                        return Math.round(this.value / datasum * 100) + "%";
                    } else {
                        return this.value + "%";
                    }
                }
            }
        },
        tooltip: {
            enabled: showtooltip,
            formatter: function () {
                if (tooltipData) {
                    if (tooltipData['indicator_type'][0].trim() == this.x.trim()) {
                        var def = tooltipData['indicator_title'][0];
                    } else if (tooltipData['indicator_type'][1].trim() == this.x.trim()) {
                        var def = tooltipData['indicator_title'][1];
                    } else if (tooltipData['indicator_type'][2].trim() == this.x.trim()) {
                        var def = tooltipData['indicator_title'][2];
                    } else if (tooltipData['indicator_type'][3].trim() == this.x.trim()) {
                        var def = tooltipData['indicator_title'][3];
                    }
                    return '<b><span style="font-size:12px">' + this.x + '</span></b><table><tr><td style="font-size:10px">' + def + '</td></tr><tr></td><td style="padding:0"><b>' + this.y + '' + tooltip_sym + '</b></td></tr></table>';
                } else {
                    return '<b><span style="font-size:12px">' + this.x + '</span></b><table></tr><tr></td><td style="padding:0"><b>' + this.y + '' + tooltip_sym + '</b></td></tr></table>';
                }
            },
            shared: true,
            useHTML: true
        },
        plotOptions: {
            series: {
                stacking: stacking,
                colorByPoint: cbp,
                dataLabels: {
                    format: '{y:.1f}',
                    allowOverlap: true,
                    enabled: true,
                    rotation: rotation,
                    crop: false,
                    overflow: 'none'
                }
            },
            column: {
                dataLabels: {
                    enabled: true,
                    crop: false,
                    overflow: 'none'
                }
            }
        },
        credits: {
            enabled: false
        },
        series: data_series
    };

    var chart = new Highcharts.Chart(options);
}


Highcharts.wrap(Highcharts.Chart.prototype, 'print', function (proceed) {
    var chart = this,
        chartWidth = chart.chartWidth;
    this.setSize(800, chart.chartHeight, false);
    proceed.call(this);
    setTimeout(function () {
        chart.setSize(chartWidth, chart.chartHeight, false);
    }, 1000);
});


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
    else chart_title = '';

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
