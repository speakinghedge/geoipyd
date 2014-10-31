# geoipyd


is a simple geo IP daemon that offers a HTTP based interface to query
geo information related to public IPv4/6 addresses.

This tool utilizes the GeoData made available by MaxMind (www.maxmind.com).

## motivation

Currently I'm playing with Python wrappers for nDPI and libprotoident and
I needed a way to visualize flows on the surface of our planet. But its also
handy for a plethora of other things...

## configuration

The daemon expects its configuration in __/etc/geoipd.cfg__:

```
[GEOIPD]
data_dir : /var/geoipd/data
server_ip : 127.0.0.1
server_port : 4242
```

The __data_dir__ contains the downloaded and deflated geo databases from MaxMind.
Therefore the daemon needs at least read permissions on that folder. 

Since the tool is able to download/deflate the database on its own, it may also
require write permissions. Be careful with that.

The __server_ip__ defines the local IP address the daemon should listen on,
__server_port__ defines the service endpoint.

The configuration given in the file could be overridden by command line arguments.

If the configuration is not present and no command line argument is given, the daemon 
uses a default configuration that equals the example configuration file given above.

## first startup

If you start the daemon for the first time, you can use the command line switch __--force-download__
to advice the tool to download and deflate the database files from MaxMind. 

In addition you can use the argument __--data-dir__ to specify to witch directory the deflated 
files should be saved.

If you would like to download and deflate the files on your own, have a look at the head of
the file geoipyd - there you can find all required download locations and the expected file names. 
Make sure that all files are dropped within one folder (some of them are shipped in a folder).

To save bandwith avoid unneeded downloads (don't download the database files on each start - check
first if there are any updates).

## usage

To start/stop/restart the daemon just run:

```
./geoipyd start
./geoipyd restart
./geoipyd stop
```

Startup may take some time - have a look at the syslog.

A typical request (HTTP-GET) looks like this:

```
http://192.168.1.101:4242/?23.23.23.42
```

The response is alway a JSON-string:

```
{
 "ip": {"version": 4, "uint": 387389226, "address": "23.23.23.42"}, 
 "as": {"owner": "Amazon.com  Inc.", "num": 14618}, 
 "location": {"latitude": 39.0437, "country": {"code": "US", "name": "United States"}, "longitude": -77.4875, "city": "Ashburn"}
}
```

Even if the daemon is not able to find any information the response is JSON-formated:

```
{"ip": {"version": 4, "uint": 3232235777, "address": "192.168.1.1"}, "location": {}}
```

## help

To get the (subcommands specific) help, run:

```
./geoipyd -h
./geoipyd start -h
./geoipyd restart -h
```

The subcommand stop offers no additional arguments.

## TODO

- unittest (there are none currently)
- per function documentation
- local database to avoid re-reading at startup
