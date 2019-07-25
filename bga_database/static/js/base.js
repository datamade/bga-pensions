class DataYearController {
    constructor (yearData) {
        this.yearData = yearData
    }
    select (year) {
        return this.yearData[year]
    }
}

class ChartHelper {
    makeChart (data) {
        Highcharts.chart(data[0].container, {
            chart: {
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false,
                type: 'pie'
            },
            title: {
                text: data[0].name,
            },
            tooltip: {
                pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: false
                    },
                    showInLegend: true,
                    colors: ['navy', 'silver'],
                }
            },
            series: data,
        });
    }
}

export { DataYearController, ChartHelper };
