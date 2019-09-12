/**
 * Created by devashish on 9/3/19.
 */
function generateBarChart(container, type, title, subtitle, categories, data_series, cat_label, tooltip_sym, cbp, showlegend, stacking, rotation, dlf, datasum, tooltipData, showtooltip, height,colors) {

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
