# IoT

Logging on using OTP - One-Time Password

http://sustentaculum.com.br


build
-----

    $ git clone https://github.com/caputomarcos/iot.git
    $ docker build --no-cache --rm -t caputomarcos/iot:1.0 -t caputomarcos/iot  .

pull
----
   
    $ docker pull caputomarcos/iot
   
run
---    

    $ echo 'MONGODB_URI=mongodb://<dbuser>:<dbpassword>@ds129442.mlab.com:29442/iot' > .env
    $ docker run --name iot --env-file .env -it -p 5000:5000 caputomarcos/iot
