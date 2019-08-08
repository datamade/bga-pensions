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

        var yearHasData = (data !== undefined &&
            data.hasOwnProperty('aggregate_funding') &&
            data.aggregate_funding.length > 0);

        if ( yearHasData ) {
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

        $('#fundDropdownMenuButton').text(fund);
        $('.employer-name').text(this.selectedFund);
        $('.employer-data-year').text(this.selectedYear);

        if ( data.binned_benefit_data !== undefined ) {
            this.chartHelper.makeDistributionChart(data.binned_benefit_data);
            $('#median-benefit-amount').text(data.median_benefit);
            $('#total-benefits').text(data.total_benefits);
        }

        if ( data.aggregate_funding !== undefined ) {
            $('#fund-detail').show();
            $('#fund-detail-no-data').hide();

            this.chartHelper.makePieChart(data.aggregate_funding);
            this.chartHelper.makeBarChart(data.amortization_cost);

            $('#funding-level').text(data.funding_level + '%');

            $('#employer-liability-amount').text(data.total_liability);
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
                    pointWidth: 100,
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
                margin: [0, 0, 0, 0],
            },
            title: {
                text: '', // data.name,
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
                        style: {
                            'fontWeight': 'normal',
                        },
                    },
                    enableMouseTracking: false,
                    size: '75%',
                }
            },
            series: [data.series_data],
        });
    }
    makeDistributionChart (data) {
        var tooltip_format = function(point) {
            var edges = data[this.x];
            return this.y.toLocaleString() + ' benefits fall between $' + edges.lower_edge.toLocaleString() + ' and $' + edges.upper_edge.toLocaleString();
        };

        var axis_format = function() {
            var penultimate_bin = this.value === data.length - 1;
            var last_bin = this.value === data.length;

            var edges;

            if ( last_bin ) {
                edges = data[this.value - 1];
            } else {
                edges = data[this.value];
            }

            var composite_last_bin = edges.upper_edge !== 275000;

            if ( last_bin ) {
                if ( composite_last_bin ) {
                    return null;
                } else {
                    return '$' + edges.upper_edge.toLocaleString();
                }
            } else if ( penultimate_bin ) {
                if ( composite_last_bin ) {
                    return '$' + edges.lower_edge.toLocaleString() + '+';
                } else {
                    return '$' + edges.lower_edge.toLocaleString();
                }
            } else {
                try {
                    return '$' + edges.lower_edge.toLocaleString();
                } catch (err) {
                    // Occurs when Highcharts wants to add an extra label
                    return '';
                }
            }
        };

        var end_on_tick;

        if ( data[data.length - 1].upper_edge !== 250000 ) {
            end_on_tick = false;
        } else {
            end_on_tick = true;
        }

        Highcharts.chart('benefit-distribution-chart', {
            title: {
              text: '', // Done in template
            },
            plotOptions: {
              column: {
                maxPointWidth: 80,
                minPointLength: 2,
                dataLabels: {
                  enabled: true,
                  color: '#333',
                },
                pointPlacement: 'between',
                pointPadding: 0,
                groupPadding: 0
              }
            },
            xAxis: {
                labels: {
                    enabled: true,
                    formatter: axis_format,
                },
                tickInterval: 0,
                endOnTick: end_on_tick,
                title: {
                    text: 'Benefit range',
                },
                allowDecimals: false
            },
            yAxis: {
                title: {
                    text: 'Number of benefits',
                },
            },
            series: [{
                type: 'column',
                data: data,
                id: 'amounts',
                tooltip: {
                  headerFormat: '', // Remove header
                  pointFormatter: tooltip_format
                },
                color: '#294d71',
            }],
            legend: {
                enabled: false,
            }
        });
    }
}

export { PensionsController, ChartHelper };
