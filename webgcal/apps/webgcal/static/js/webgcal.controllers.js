var WebGCalControllers = angular.module('WebGCalControllers', []);

WebGCalControllers.controller('WebGCalCalendarController', ['$scope', '$dragon', function ($scope, $dragon) {
    $scope.calendar_id = 0;
    $scope.calendar = {};
    $scope.channel = 'calendar';
    $scope.router = 'calendar';

    $scope.init = function(calendar_id, calendar) {
        $scope.calendar_id = calendar_id;
        $scope.calendar = calendar;
        $scope.channel = 'calendar-' + calendar_id;
    };

    $scope.parseDate = function(string) {
        return DateISO8601(string.replace(' ', 'T'));
    };

    $dragon.onReady(function() {
        $dragon.subscribe($scope.router, $scope.channel, {id: $scope.calendar_id}).then(function(response) {
            $scope.dataMapper = new DataMapper(response.data);
        });

        $dragon.getSingle($scope.router, {id: $scope.calendar_id}).then(function(response) {
            $scope.calendar = response.data;
        });
    });

    $dragon.onChannelMessage(function(channels, message) {
        if (indexOf.call(channels, $scope.channel) > -1) {
            $scope.$apply(function() {
                $scope.dataMapper.mapData($scope.calendar, message);
            });
        }
    });
}]);

WebGCalControllers.controller('WebGCalWebsiteController', ['$scope', '$dragon', function ($scope, $dragon) {
    $scope.website_id = 0;
    $scope.website = {};
    $scope.channel = 'website';
    $scope.router = 'website';

    $scope.init = function(website_id, website) {
        $scope.website_id = website_id;
        $scope.website = website;
        $scope.channel = 'website-' + website_id;
    };

    $scope.parseDate = function(string) {
        return DateISO8601(string.replace(' ', 'T'));
    };

    $dragon.onReady(function() {
        $dragon.subscribe($scope.router, $scope.channel, {id: $scope.website_id}).then(function(response) {
            $scope.dataMapper = new DataMapper(response.data);
        });

        $dragon.getSingle($scope.router, {id: $scope.website_id}).then(function(response) {
            $scope.website = response.data;
        });
    });

    $dragon.onChannelMessage(function(channels, message) {
        if (indexOf.call(channels, $scope.channel) > -1) {
            $scope.$apply(function() {
                $scope.dataMapper.mapData($scope.website, message);
            });
        }
    });
}]);
