# RTL 433 Prometheus Exporter

This repository contains a prometheus exporter for [rtl_433](https://github.com/merbanan/rtl_433), a tool for receiving data from many different types of radio sensors.

## Prerequisites

The following need to be installed and working first:

* rtl_433
* python3

## Setup

The following will set up rtl_433_exporter to run via systemd:

* Clone this repo
* Run `pip install -r requirements.txt`
* Copy `rtl_433_exporter.py` to `/usr/local/bin`
* Create a config file in `/usr/local/etc/rtl_433_exporter_config.toml`
* Copy `rtl_433_exporter.service` to `/etc/systemd/system`
* Run `systemctl daemon-reload`
* Run `systemctl enable rtl_433_exporter.service`
* Run `systemctl start rtl_433_exporter.service`

## Config

The configuration file format is TOML, and the default path to the config file is `config.toml` in the same directory as `rtl_433_exporter.py` itself.

```
[metric_descriptions]
foo = "Example metric description"
```

This section is for if your device returns a metric that isn't known by rtl_433_exporter, and allows you to add a friendly description for the metric that is included in the prometheus output. If you don't do this, the metric name itself is used as the friendly description.

```
[locations]
# Model,ID,Channel = Location
"Acurite-Rain899,1234,0" = "Outside"
```

This section lets you map a device to a specific location (or other friendly name for the device). You specify the model, ID and channel separated by commas, and the value will be set as the 'location' prometheus label.

```
prometheus_port = 9550
```

You can change the port used for the exporter by specifying it in the configuration file similar to above.

## Metric names

Metrics names are identical to those returned by `rtl_433 -F json`, but with `rtl_433_` prepended to the name. You can run `rtl_433` manually to discover what they are. However, the following are some common metrics you might see:

* `rtl_433_battery_ok` - Battery status of a device
* `rtl_433_rain_mm` - The total amount of rainfall for a rain meter

There are also two additional metrics added by the exporter:

* `rtl_433_timestamp_seconds` - the unix timestamp of the time when we last received a packet for a given device.
* `rtl_433_packets_received` - A count of the total number of packets received for a given device.

All metrics have 4 labels attached to them:

* `model` - The model of the device as returned by rtl_433
* `id` - The id of the device as returned by rtl_433
* `channel` - The channel of the device as returned by rtl_433
* `location` - A 'friendly' name for a device that you can set in the configuration file based on model,id,channel. If you don't set a friendly name, this label is left blank.

## Example prometheus configuration

```
  - job_name: static_exporters
    static_configs:
      - targets:
        - meters.example.com:9550
```

## Similar tools

* [rtl_433_prometheus](https://github.com/mhansen/rtl_433_prometheus) - the original inspiration for this project. The main difference between the two is that rtl_433_exporter will provide metrics for anything rtl_433 gives you and so will work with more than humidity and temperature sensors. However, rtl_433_exporter isn't quite a drop in replacement, as some of the metrics names are changed to match what rtl_433 returns.
