# RTL 433 Prometheus Exporter

## Setup

* Install rtl_433 somewhere in the path
* Ensure python3 is installed
* Copy rtl_433_exporter.py to /usr/local/bin
* Create a config file in /usr/local/etc/rtl_433_exporter_config.toml
* Copy rtl_433_exporter.service to /etc/systemd/system
* Run systemctl daemon-reload
* Run systemctl enable rtl_433_exporter.service
* Run systemctl start rtl_433_exporter.service

## Config

```
[metric_descriptions]
foo = "Example metric description"
```

This section is for if your device returns a metric that isn't known by
rtl_433_exporter, and allows you to add a friendly description for the metric
that is included in the prometheus output. If you don't do this, the metric
name itself is used as the friendly description.

```
[locations]
# Model,ID,Channel = Location
"Acurite-Rain899,1234,0" = "Outside"
```

This section lets you map a device to a specific location (or other friendly
name for the device). You specify the model, ID and channel separated by
commas, and the value will be set as the 'location' prometheus label.
