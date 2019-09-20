

var request = new XMLHttpRequest();
request.open('GET', '/analytics', true);

request.onload = function() {
  if (request.status >= 200 && request.status < 400) {
    // Success!
    var data = JSON.parse(request.responseText);

    var trace1 = {
      x: data.times,
      y: data.cur_order_counts_by_clock,
      name:"今天",
      type: "scatter"
    };

    var trace2 = {
      x: data.times,
      y: data.last_order_counts_by_clock,
      name: "昨天",
      type: "scatter"
    };

    var plot_data = [trace1,trace2];

    var layout = {

                  title: "日销售曲线图 - 今日 vs 昨天",

                  xaxis: {
                    title: '时间点'},

                  yaxis: {
                    title: '订单总金额截止该点 €'}


                };

    Plotly.newPlot('lineChart', plot_data, layout);



    // weekly ploting
    var trace3 = {
      x: data.cur_weekdays,
      y: data.cur_week_revenue,
      name:"本周",
      type: "scatter"
    };



    var trace4 = {

      x: data.last_weekdays,
      y: data.last_week_revenue,
      name:"上周"

    };


    var weeklyLayout = {
      title: "周对比",
      xaxis: {
        title: '星期'},

      yaxis: {
        title: '当日营业额 €'}

    };

    var weeklyData = [trace3, trace4];


    Plotly.newPlot('weeklyChart', weeklyData, weeklyLayout);



    // Monthlyly ploting
    var trace5 = {
      x: data.cur_mon_dates,
      y: data.cur_mon_revenue_by_dates,
      name:"本月",
      type: "scatter"
    };


    var trace6 = {

      x: data.last_mon_dates,
      y: data.last_mon_revenue_by_dates,
      name:"上月",
      type: "scatter"

    };


    var monthlyLayout = {

      title: "月对比",

      xaxis: {
        title: '日期'
      },

      yaxis: {

        title: '当日营业额 €'

      }
    };

    var monthlyData = [trace5, trace6];

    Plotly.newPlot('monthlyChart', monthlyData, monthlyLayout);



  } else {
    // We reached our target server, but it returned an error

  }
};

request.onerror = function() {
  // There was a connection error of some sort
};

request.send();
