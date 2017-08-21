'use strict';
/**
 * @ngdoc function
 * @name sbAdminApp.controller:MainCtrl
 * @description
 * # MainCtrl
 * Controller of the sbAdminApp
 */
angular.module('sbAdminApp')
    .controller('MainCtrl', function ($scope, $position, $http) {

        var loaddata = function () {

            // EDIT THIS TO CORRESPOND TO THE URL OF YOUR "ds_app_15"
            $http.get('http://ds_app_15.apps.YOUR_PCF_INSTALL.DOMAIN/lastMessage')
                .then(function (data) {

                    console.log(data);
                    $scope.sentimentdata = data.data;

                    // check for vision_labels

                    var media = $scope.sentimentdata.entities.media;

                    $scope.media_url = media[0].media_url;

                    $scope.vision_labels = media[0].vision_labels;
                    console.log($scope.vision_labels);

                    //$scope.sentiment.score = 0.0;

                    $scope.sentiment = $scope.sentimentdata.sentiment;

                    // Add an icon to represent the sentiment
                    if ($scope.sentiment.score > 0.0) {
                        $scope.sentiment_icon_url = "/Thumbs_Up.png";
                    } else {
                        $scope.sentiment_icon_url = "/Thumbs_Down.png";
                    }

                    console.log($scope.sentiment);

                    $scope.offer_items = $scope.sentimentdata.offer_items;

                    $scope.offer_text = $scope.sentimentdata.offer_text;

                    console.log($scope.offer_items);


                }, function (errorPayload) {

                    console.log(errorPayload);


                });
        }

        loaddata();


    });
