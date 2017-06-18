angular.module('IoT', [])
    .controller('HomeCtrl', function ($scope, $http) {
        $scope.info = {};
        $scope.showAdd = true;
        $scope.showlist = function () {
            $http({
                method: 'POST',
                url: '/getDeviceList',
            }).then(function (response) {
                $scope.devices = response.data;
                console.log('mm', $scope.devices);
            }, function (error) {
                console.log(error);
            });
        };

        $scope.addDevice = function () {
            $http({
                method: 'POST',
                url: '/addDevice',
                data: {info: $scope.info}
            }).then(function (response) {
                $scope.showlist();
                $('#addPopUp').modal('hide')
                $scope.info = {}
            }, function (error) {
                console.log(error);
            });
        };

        $scope.editDevice = function (id) {
            $scope.info.id = id;
            $scope.showAdd = false;
            $http({
                method: 'POST',
                url: '/getDevice',
                data: {id: $scope.info.id}
            }).then(function (response) {
                console.log(response);
                $scope.info = response.data;
                $('#addPopUp').modal('show')
            }, function (error) {
                console.log(error);
            });
        };

        $scope.updateDevice = function (id) {

            $http({
                method: 'POST',
                url: '/updateDevice',
                data: {info: $scope.info}
            }).then(function (response) {
                console.log(response.data);
                $scope.showlist();
                $('#addPopUp').modal('hide')
            }, function (error) {
                console.log(error);
            });
        };


        $scope.showAddPopUp = function () {
            $scope.showAdd = true;
            $scope.info = {};
            $('#addPopUp').modal('show')
        };

        $scope.showRunPopUp = function (id) {
            $scope.info.id = id;
            $scope.run = {};
            $http({
                method: 'POST',
                url: '/getDevice',
                data: {id: $scope.info.id}
            }).then(function (response) {
                console.log(response);
                $scope.run = response.data;
                $scope.run.isRoot = false;
                $('#runPopUp').modal('show');
            }, function (error) {
                console.log(error);
            });
        };

        $scope.confirmDelete = function (id) {
            $scope.deleteDeviceId = id;
            $('#deleteConfirm').modal('show');
        };

        $scope.deleteDevice = function () {

            $http({
                method: 'POST',
                url: '/deleteDevice',
                data: {id: $scope.deleteDeviceId, info: $scope.info}
            }).then(function (response) {
                console.log(response.data);
                $scope.deleteDeviceId = '';
                $scope.showlist();
                $('#deleteConfirm').modal('hide')
            }, function (error) {
                console.log(error);
            });
        };

        $scope.executeCommand = function () {
            console.log($scope.run);
            $http({
                method: 'POST',
                url: '/execute',
                data: {info: $scope.run}
            }).then(function (response) {
                console.log(response);
                $scope.run.response = response.data.message;
            }, function (error) {
                console.log(error);
            });
        };

        $scope.showlist();
    })