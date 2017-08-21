'use strict';
/**
 * @ngdoc function
 * @name sbAdminApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the sbAdminApp
 */
angular.module('sbAdminApp')
  .controller('SearchTicketsCtrl', ['$scope', '$timeout','$http', function ($scope, $timeout,$http) {

    console.log('SearchTicketsCtrl');
    $scope.showdetails =false;


              /*  $http({
        			method: 'GET',
        			url: 'data/pass_users.json'
        		}).then(function successCallback(response) {
                    $scope.users = response.data.users;

                        console.log($scope.users);
        		}, function errorCallback(response) {
        			console.error(response)
        		});
        		*/

                $http({
                    method: 'GET',
                    url: 'rest/getpaasusers'
                }).then(function successCallback(response) {

                   // $scope.users = response.data.users;
                    $scope.showdetails =false;
                    $scope.users = response.data;
                        console.log(response);
                }, function errorCallback(response) {
                    console.error(response)
                });


                 $http({
                    method: 'GET',
                    url: 'data/example_data.tsv'
                }).then(function successCallback(response) {

                        //console.log(response.data);

                      //  d3simplejson(response.data);

                   // drawzendeskReportForUser(response.data);
                }, function errorCallback(response) {
                    console.error(response)
                });

               /* $http({
                    method: 'GET',
                    url: 'data/sridhars_ticket.json'
                }).then(function successCallback(response) {
                        //console.log(response.data);

                    //drawzendeskReportForUser(response.data);

                }, function errorCallback(response) {
                    console.error(response)
                });
                */

                 $scope.loaddata = function(){
                     $scope.showdetails =false;
                     d3.select("#chartContainer").selectAll("svg").remove();
                    console.log($scope.selectedUser);
                    // get ticket information...

                    $http({
                        method: 'GET',
                        url: 'rest/getuserticketinfo?userId='+$scope.selectedUser.id
                    }).then(function successCallback(response) {
                        console.log(response);
                        $scope.tickets = response.data;
                        drawzendeskReportForUser(response.data);
                         $scope.showdetails =true;
                    }, function errorCallback(response) {
                        console.error(response)
                    });


                 }

                 $scope.formatuidate = function(uidate){
                    var createdate = new Date(uidate);
                    return createdate;
                 }

                 $scope.getcustomfields = function(customfields){
                    var fields=[];
                       customfields.forEach(function(d) {
                           // console.log(d);
                           /*if(d.id== "23872527"){
                           fields.push(d.value);
                           }*/
                           if( (d.value != "" ) && (d.value != null) && (d.value != null) && (d.value != 'n/a')) {
                             fields.push(d.value);
                           }
                        })
                    return fields;
                  }

                 // "2016-04-25T15:34:54Z"
                 var parseDate = d3.time.format("%Y-%m-%dT%H:%M:%SZ").parse;
                 var formatTime =  d3.time.format("%Y-%m-%dT00:00:00");

                 var drawzendeskReportForUser = function(tickets){

                       // console.log(data.tickets);
                          var ticketOjb=[];
                          var ticketOjbData =[];
                          var count=0;
                            tickets.forEach(function(d) {

                               // console.log(d);

                                //  d.frequency = parseDate(d.frequency);
                                //   console.log(d.created_at);
                                //d.frequency = parseDate(d.created_at);
                                //   var parseDate = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;
                                //   parseDate("2015-07-16T00:00:00.000Z");
                                //console.log( parseDate("2015-07-16T00:00:00.000Z"));

                                //console.log(parseDate(d.created_at));
                               // var createdate = parseDate(d.created_at);
                                var createdate = new Date(d.created_at);
                                var mycreate = formatTime(createdate);

                              //  console.log(mycreate);


                                var ticketOjb=[];
                                    ticketOjb.createdate= Date.parse(mycreate);
                                    ticketOjb.id= d.id;
                                    ticketOjb.subject = d.subject;
                                    ticketOjb.description= d.description;
                                    // ticketOjb.priority= d.priority;
                                    ticketOjb.status= d.status;
                                    ticketOjb.tags= d.tags;
                                    ticketOjb.fields =d.custom_fields;
                                    // set the serverity of the
                                    //console.log(ticketOjb.fields.length);
                                    for(var i =0;i < ticketOjb.fields.length ; i++){
                                       if(ticketOjb.fields[i].id == "23872527"){
                                            ticketOjb.priority = ticketOjb.fields[i].value;
                                            //console.log(ticketOjb.priority);
                                       }
                                        //console.log();
                                    }
                                count= count+1;
                               // console.log(createdate);

                                //console.log(ticketOjb);

                                if(count < 15){

                                     ticketOjbData.push(ticketOjb);
                                }


                           });


                                                    //       d3chart(ticketOjbData);

                                                           d3simplechart(ticketOjbData);



                 }

                var d3chart = function(ticketOjbData){

                         console.log(ticketOjbData);
                    $('.svg-container svg').remove();

                  // Set the dimensions of the canvas / graph
                                         var margin = {top: 30, right: 20, bottom: 30, left: 50},
                                           width = 900 - margin.left - margin.right,
                                           height = 270 - margin.top - margin.bottom;

                                         // Set the ranges
                                         var x = d3.time.scale().range([0, width]);


                                       var y = d3.scale.ordinal()
                                             .domain(["high","urgent","normal"])
                                             .rangePoints([0,height]);

                                         // Define the axes
                                         var xAxis = d3.svg.axis().scale(x)
                                             .orient("bottom")
                                             //.ticks(10)
                                            // .ticks(d3.time.days, 1)
                                             // .tickSubdivide(true)
                                              .tickFormat(d3.time.format('%m/%d'))
                                           //   .tickSize(5)
                                              //.outerTickSize(10)
                                           //   .tickPadding(8);

                                         var yAxis = d3.svg.axis().scale(y)
                                             .orient("left").ticks(5);


                                         // Adds the svg canvas
                                         var svg = d3.select(".svg-container")
                                             .append("svg")
                                                 .attr("width", width + margin.left + margin.right)
                                                 .attr("height", height + margin.top + margin.bottom)
                                             .append("g")
                                                 .attr("transform",
                                                       "translate(" + margin.left + "," + margin.top + ")");
                                             // Scale the range of the data
                                             x.domain(d3.extent(ticketOjbData, function(d) { return d.createdate; }));
                                            // y.domain([0, d3.max(ticketOjbData, function(d) { return 5; })]);




                                             // Add the X Axis
                                             svg.append("g")
                                                 .attr("class", "x axis")
                                                 .attr("transform", "translate(0," + height + ")")
                                                 .call(xAxis);

                                             // Add the Y Axis
                                             svg.append("g")
                                                 .attr("class", "y axis")
                                                 .call(yAxis);


                                               // Add the scatterplot
                                               svg.selectAll("dot")
                                                   .data(ticketOjbData)
                                                 .enter().append("circle")
                                                   .attr("r", 3.5)
                                                   .attr("cx", function(d) { return x(d.createdate); })
                                                   .attr("cy", function(d) { return y(d.priority); });
                }

                       var d3simplechart = function(data){


                            // var svg = dimple.newSvg("#chartContainer", 590, 500);

                           /* var margin = {top: 30, right: 20, bottom: 30, left: 50},
                            width = 900 - margin.left - margin.right,
                            height = 270 - margin.top - margin.bottom;


                            var svg = d3.select(".svg-container")
                            .append("svg")
                            .attr("width", width + margin.left + margin.right)
                            .attr("height", height + margin.top + margin.bottom)

                            */
                            //$('.chartContainer').remove();
                            d3.select("#chartContainer").selectAll("svg").remove();
                            var svg = dimple.newSvg("#chartContainer", 590, 500);
                           // data = dimple.filterData(data, "status", ["open", "pending","closed"])
                             var myChart = new dimple.chart(svg, data);
                            // myChart.setBounds(50, 30, 450, 330)


                             var x = myChart.addTimeAxis("x", "createdate");
                             x.tickFormat ='%m/%d';
                             x.timeInterval = 2;
                            // x.addOrderRule("Date");
                             x.title = 'Ticket Pickup date';
                             var y = myChart.addCategoryAxis("y", ["priority", "status","id"]);
                             y.title = 'Ticket Type';

                            // myChart.addSeries("Channel", dimple.plot.bubble);
                            // myChart.addLegend(180, 10, 360, 20, "right");
                              // set series and legend
                              var s = myChart.addSeries('status', dimple.plot.scatter);

                                    // Define a custom color palette.  These colours are based on the excellent
                                    // set at http://flatuicolors.com/
                                    //   new dimple.color("#9b59b6", "#8e44ad", 1), // purple
                                    //  new dimple.color("#1abc9c", "#16a085", 1), // turquoise
                                    myChart.defaultColors = [
                                        new dimple.color("#3498db", "#2980b9", 1), // blue
                                        new dimple.color("#e74c3c", "#c0392b", 1), // red
                                        new dimple.color("#2ecc71", "#27ae60", 1), // green
                                        new dimple.color("#e67e22", "#d35400", 1), // orange
                                        new dimple.color("#f1c40f", "#f39c12", 1), // yellow
                                        new dimple.color("#95a5a6", "#7f8c8d", 1)  // gray
                                    ];

                                //  myChart.addColorAxis("status", ["green", "orange", "red","blue","black"]);
                                // var p = myChart.addSeries('Ticket Details', dimple.plot.line);
                                // myChart.addSeries("status", dimple.plot.line);
                                // var legend = myChart.addLegend(width*0.65, 60, width*0.25, 60, 'right');
                                 myChart.addLegend(60, 10, 500, 20, "right");
                             myChart.draw();

                       }


                   var d3simplejson = function(data){
                         var svg = dimple.newSvg("#chartContainer", 590, 400);
                           d3.tsv("data/example_data.tsv", function (data) {
                             var myChart = new dimple.chart(svg, data);
                             myChart.setBounds(75, 30, 490, 330)
                             myChart.addMeasureAxis("x", "Unit Sales");
                             var y = myChart.addCategoryAxis("y", "Month");
                             y.addOrderRule("Date");
                             myChart.addSeries("Channel", dimple.plot.bubble);
                             myChart.addLegend(180, 10, 360, 20, "right");
                             myChart.draw();
                           });
                       }

}]);