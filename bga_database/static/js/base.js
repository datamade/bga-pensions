class DataYearController {
    constructor (yearData) {
        this.yearData = yearData
    }
    selectYear (year) {
        return this.yearData[year]
    }
    selectFund (year, fund) {
        return this.selectYear(year)['data_by_fund'][fund]
    }
}

class ChartHelper {
    constructor () {
        Highcharts.setOptions({
            lang: {
              thousandsSep: ',',
            },
            colors: ['#01406c', '#eaebee'],
        });
    }
    makeBarChart (data) {
        Highcharts.chart(data.container, {
            plotOptions: {
                bar: {
                    dataLabels: {
                        enabled: true,
                        format: data.label_format,
                    },
                    enableMouseTracking: false,
                },
                series: data.stacked ? {'stacking': 'normal'} : {},
            },
            chart: {
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false,
                type: 'bar',
            },
            title: {
                text: data.name,
            },
            xAxis: {
                categories: data.x_axis_categories,
                title: {
                    text: null
                }
            },
            yAxis: {
                min: 0,
                title: {
                    text: 'Percent',
                },
            },
            legend: {
                verticalAlign: 'top',
            },
            tooltip: {
                pointFormat: '{series.name}: <b>' + data.label_format + '</b>'
            },
            series: [data.funded, data.unfunded],
        });
    }
    makePieChart (data) {
        Highcharts.chart(data.container, {
            chart: {
                type: 'pie'
            },
            title: {
                text: data.name,
                align: 'left',
            },
            tooltip: {
                enabled: false,
            },
            legend: {
                enabled: false,
            },
            plotOptions: {
                pie: {
                    dataLabels: {
                        enabled: true,
                        format: '<b>{point.name}</b>:<br />' + data.label_format,
                    },
                    enableMouseTracking: false,
                }
            },
            series: [data.series_data],
        });
    }
}

export { DataYearController, ChartHelper };
