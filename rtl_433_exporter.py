#!/usr/bin/env python3
import collections
import contextlib
import logging
import json
import os
import subprocess
import sys

import prometheus_client
import toml


config = {
    # This is the same port as the golang rtl_433_prometheus exporter. It
    # works for now, but we might want to change it later.
    "prometheus_port": 9550,

    # Friendly descriptions of metric names included in the output. If a
    # metric isn't included here, then its name is used instead
    "metric_descriptions": {
        "battery_ok": "Battery status (1 ok, 0 low)",
        "battery_V": "Battery voltage",
        "temperature_C": "Temperature in C",
        "humidity": "Relative Humidity (0.0-1.0)",
        "moisture": "Moisture Level (0.0-1.0)",
        "wind_dir_deg": "Wind direction in degrees",
        "wind_avg_m_s": "Average wind speed in m/s",
        "wind_max_m_s": "Gust wind speed in m/s",
        "rain_mm": "Total rainfall in mm since last reset",
        "rain_rate_mm_h": "Rainfall rate in mm per hour",
        "pressure_hPa": "Air or Tire pressure in hPa",
        "timestamp_seconds": "Timestamp when we last received a packet",
        "packets_received": "Number of packets received from a device",
    },

    # Mapping of device information to a location. This is populated from the
    # config file.
    "locations": {},
}

# List of keys that are used as labels for a metric
label_keys = ['model', 'id', 'channel', 'location']


class Metrics(collections.defaultdict):
    """Dict-like object that automatically creates prometheus metrics when
    accessed"""

    def __missing__(self, key):
        self[key] = prometheus_client.Gauge(
            "rtl_433_" + key,
            config['metric_descriptions'].get(key, key),
            label_keys)
        return self[key]


metrics = Metrics()


def remove_default_metrics():
    # This removes the default prometheus client metrics which we don't care
    # about here
    REGISTRY = prometheus_client.REGISTRY
    for name in list(REGISTRY._names_to_collectors.values()):
        with contextlib.suppress(KeyError):
            prometheus_client.REGISTRY.unregister(name)


def load_config(filename):
    if not os.path.exists(filename):
        logging.warn(f"Config file {filename} doesn't exist. Skipping...")
        return
    logging.info(f"Loading config from {filename}")

    loaded_config = toml.load(filename)

    # Merge loaded and default config
    # Dict values are merged, other values are replaced
    for key in config:
        if key in loaded_config:
            if isinstance(config[key], dict):
                config[key].update(loaded_config[key])
            else:
                config[key] = loaded_config[key]


def start_rtl433():
    command = "rtl_433 -F json"
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                         close_fds=True, bufsize=1, text=True)
    return p.stdout


def process_lines(fd):
    for line in fd:
        data = json.loads(line)
        # Split data into things we want to keep as metrics and metadata that
        # we will use as labels
        metadata_keys = {'time', 'model', 'id', 'channel', 'mic'}
        metadata = {i: data[i] for i in metadata_keys if i in data}
        data = {i: data[i] for i in data if i not in metadata_keys}

        # Set the location based on device mappings
        metadata['location'] = config['locations'].get(
            f"{metadata['model']},{metadata['id']},{metadata['channel']}",
            "")

        # Generate labels for each metric based on the device informaiton
        label_values = [metadata[i] for i in label_keys]

        # Update metrics for each value in data
        for i in data:
            # Make a new Gauge metric if this is the first time we saw it,
            # otherwise retrieve the stored one.
            metric = metrics[i]
            metric.labels(*label_values).set(data[i])

        # Next, update some metadata about the device
        metrics['packets_received'].labels(*label_values).inc()
        # This sets to the current time, which isn't exactly what rtl_433
        # itself gives us, but it's close enough.
        metrics["timestamp_seconds"].labels(
                *label_values).set_to_current_time()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    remove_default_metrics()
    if len(sys.argv) > 1:
        load_config(sys.argv[1])
    else:
        load_config("./config.toml")
    logging.info(f"Starting http server on {config['prometheus_port']}")
    prometheus_client.start_http_server(config['prometheus_port'])
    logging.info("Starting rtl_433 process")
    fd = start_rtl433()
    logging.info("Procesing metrics")
    process_lines(fd)
