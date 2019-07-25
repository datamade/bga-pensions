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
        });
    }
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
                pointFormat: '{series.name}: <b>${point.y}</b>'
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
