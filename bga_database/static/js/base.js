class PensionsController {
    constructor (yearData, selectedYear, selectedFund, chartHelper) {
        this.yearData = yearData
        this.selectedYear = selectedYear
        this.selectedFund = selectedFund
        this.chartHelper = chartHelper
    }
    get (year) {
        return this.yearData[year];
    }
    selectYear (year) {
        this.selectedYear = year;

        var data = this.get(year);

        $('#yearDropdownMenuButton').text(year);

        if ( data.aggregate_funding.length > 0 ) {
            $('#funding-by-system').show();
            $('#funding-by-system-no-data').hide();

            // Set local variable for this access within loop.
            var self = this;

            data.aggregate_funding.forEach(function (el) {
                self.chartHelper.makePieChart(el);
                $('#' + el.container).prev().find('span[id^="total"]').text(el.total_liability);
            })

            $('span.data-year').text(this.selectedYear);
        } else {
            $('#funding-by-system').hide();
            $('#funding-by-system-no-data').show();
        };

        return data;
    }
    selectFund (fund) {
        this.selectedFund = fund;

        var data = this.get(this.selectedYear)['data_by_fund'][fund];

        if ( Object.entries(data).length > 0 ) {
            $('#fund-detail').show();
            $('#fund-detail-no-data').hide();

            $('#fundDropdownMenuButton').text(fund);

            this.chartHelper.makePieChart(data.aggregate_funding);
            this.chartHelper.makeBarChart(data.amortization_cost);

            $('#funding-level').text(data.funding_level + '%');

            $('#employer-name').text(this.selectedFund);
            $('#employer-data-year').text(this.selectedYear);
            $('#employer-contribution-amount').text(data.employer_contribution);
        } else {
            $('#fund-detail').hide();
            $('#fund-detail-no-data').show();
        };

        return data;
    }
}

class ChartHelper {
    constructor () {
        Highcharts.setOptions({
            lang: {
              thousandsSep: ',',
            },
            colors: ['#01406c', '#dc3545'],
        });
    }
    makeBarChart (data) {
        Highcharts.chart(data.container, {
            plotOptions: {
                bar: {
                    dataLabels: {
                        enabled: true,
                        formatter: function () {
                            if ( this.point.series.name.indexOf('Amortization Cost') > 0 ) {
                                return '$' + data.pretty_amortization_cost
                            } else {
                                return '$' + data.pretty_employer_normal_cost
                            };
                        },
                    },
                    enableMouseTracking: false,
                    pointWidth: 75,
                },
                series: {
                    stacking: data.stacked ? 'normal' : undefined,
                },
            },
            chart: {
                plotBackgroundColor: null,
                plotBorderWidth: null,
                plotShadow: false,
                type: 'bar',
            },
            title: {
                text: '', // data.name,
                align: data.name_align ? data.name_align : 'center',
            },
            xAxis: {
                categories: data.x_axis_categories,
                title: {
                    text: null,
                },
                labels: {
                    style: {
                        fontSize: '15px',
                    }
                },
            },
            yAxis: {
                min: 0,
                max: data.stacked ? (data.funded.data[0] + data.unfunded.data[0]) : null,
                endOnTick: false,
                title: {
                    text: null,
                },
                labels: {
                    enabled: false,
                },
                lineWidth: 0,
                gridLineWidth: 0,
            },
            legend: {
                verticalAlign: 'top',
                align: 'center',
                itemStyle: {
                    'fontWeight': 'normal',
                },
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
                text: '', // data.name,
                align: data.name_align ? data.name_align : 'left',
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
                        distance: 10,
                    },
                    enableMouseTracking: false,
                    size: '75%',
                }
            },
            series: [data.series_data],
        });
    }
}

export { PensionsController, ChartHelper };
