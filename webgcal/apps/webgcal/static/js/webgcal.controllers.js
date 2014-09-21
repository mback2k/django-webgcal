var WebGCalControllers = angular.module('WebGCalControllers', []);

WebGCalControllers.controller('WebGCalCalendarController', ['$scope', '$dragon', function ($scope, $dragon) {
    $scope.calendars = {};
    $scope.channel = 'calendars';
    $scope.router = 'calendar';

    $dragon.onReady(function() {
        $dragon.subscribe($scope.router, $scope.channel, {}).then(function(response) {
            $scope.dataMapper = new DataMapper(response.data);
        });

        $dragon.getList($scope.router, {}).then(function(response) {
            $scope.calendars = response.data;
        });
    });

    $dragon.onChannelMessage(function(channels, message) {
        if (indexOf.call(channels, $scope.channel) > -1) {
            $scope.$apply(function() {
                $scope.dataMapper.mapData($scope.calendars, message);
            });
        }
    });
}]);

WebGCalControllers.controller('WebGCalWebsiteController', ['$scope', '$dragon', function ($scope, $dragon) {
    $scope.websites = {};
    $scope.channel = 'websites';
    $scope.router = 'website';

    $scope.init = function(calendar_id) {
        $scope.calendar_id = calendar_id;
    };

    $dragon.onReady(function() {
        $dragon.subscribe($scope.router, $scope.channel, {calendar_id: $scope.calendar_id}).then(function(response) {
            $scope.dataMapper = new DataMapper(response.data);
        });

        $dragon.getList($scope.router, {calendar_id: $scope.calendar_id}).then(function(response) {
            $scope.websites = response.data;
        });
    });

    $dragon.onChannelMessage(function(channels, message) {
        if (indexOf.call(channels, $scope.channel) > -1) {
            $scope.$apply(function() {
                $scope.dataMapper.mapData($scope.websites, message);
            });
        }
    });
}]);