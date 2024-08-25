"""
This example file demonstrates a real-world problem that Derived Triggers
can help solve.

PROBLEM

Imagine you are an IT department that needs to monitor its infrastructure
for problems and initiate alerts to various on-call teams who can respond
them fix them.  Once a minute, you examine metrics for the previous 10-minute
period.

SOLUTION

With Derived Triggers, you can define your monitoring triggers in a simple
Subject-Verb-Object format.  The triggers can then be evaluated against your
system metrics data.  Any trigger that evaluates to True will invoke the
event defined for that trigger.
"""

import csv
import io

from src.derived_attributes.derive import DeriveTriggers, InputBuilder, Trigger


def event_handler(event_name, **params):
    print(f"Event {event_name} fired with the following parameters:")
    for key, value in params.items():
        print(f"{key}: {value}")


def derive_triggers_system_monitoring():
    # Create a CSV.  Normally this would be done in a spreadsheet tool like Excel,
    # but for the purpose of this demo, we'll put together the data in a plaintext
    # format, then generate a CSV.
    trigger_rows = [
        {
            "attr": "_uptime",
            "subject": "source",
            "verb": "parse",
            "object": "$.uptime",
            "action": None,
            "params": None,
            "notes": "System uptime percentage",
        },
        {
            "attr": "uptime_alert",
            "subject": "_uptime",
            "verb": "<",
            "object": 99.5,
            "action": "page_devops_team",
            "params": ["uptime_alert", "_uptime"],
            "notes": "Alert the DevOps team if uptime dips below 99.5",
        },
        {
            "attr": "_5xx_errors",
            "subject": "source",
            "verb": "parse",
            "object": "$.error_counts['5xx']",
            "action": None,
            "params": None,
            "notes": "Count of 500-level errors",
        },
        {
            "attr": "server_error_alert",
            "subject": "_5xx_errors",
            "verb": ">",
            "object": 5,
            "action": "page_feature_team",
            "params": ["server_error_alert", "_5xx_errors"],
            "notes": "Alert the Feature team if more than 5 server errors",
        },
        {
            "attr": "_max_cpu_usage_by_core",
            "subject": "source",
            "verb": "parse_jsonata",
            "object": "$max(cpu_usage.core_usage[*].usage)",
            "action": None,
            "params": None,
            "notes": "Maximum amount of CPU used by any core",
        },
        {
            "attr": "max_cpu_usage_by_core_alert",
            "subject": "_max_cpu_usage_by_core",
            "verb": ">",
            "object": 90,
            "action": "page_devops_team",
            "params": ["max_cpu_usage_by_core_alert", "_max_cpu_usage_by_core"],
            "notes": "Alert the DevOps team if max CPU used by any core exceeds 90",
        },
        {
            "attr": "_free_disk_space_percentage",
            "subject": "source",
            "verb": "parse",
            "object": "($.disk_usage.total - $.disk_usage.used) / $.disk_usage.total",
            "action": None,
            "params": None,
            "notes": "The amount of free disk space left",
        },
        {
            "attr": "low_disk_space_alert",
            "subject": "_free_disk_space_percentage",
            "verb": "<",
            "object": 0.10,
            "action": "page_devops_team",
            "params": ["low_disk_space_alert", "_free_disk_space_percentage"],
            "notes": "Alert the DevOps team if disk space is below 10Q%",
        },
    ]

    # Create a StringIO object to hold the CSV data
    output = io.StringIO()

    # Write the dictionary to the StringIO object as CSV
    writer = csv.writer(output)

    # Write the header, minus the Notes field
    writer.writerow(["attr", "subject", "verb", "obj", "action", "params"])

    # Write the data
    for row in trigger_rows:
        writer.writerow(
            [
                row["attr"],
                row["subject"],
                row["verb"],
                row["object"],
                row["action"],
                ",".join(row["params"]) if row["params"] else None,
            ]
        )

    # Get the string value of the CSV
    triggers_csv = output.getvalue()

    # Close the StringIO object
    output.close()

    # Get the customer purchase history.  Normally this would be fetched from
    # the database, but for the purpose of this demo, we'll construct it.
    system_metrics = {
        "uptime": 99.4,
        "error_counts": {
            "4xx": 23,
            "5xx": 13,
        },
        "cpu_usage": {
            "average": 81.1,
            "core_usage": [
                {"core": 0, "usage": 70.1},
                {"core": 1, "usage": 92.1},
            ],
        },
        "memory_usage": {
            "total": 16,
            "used": 12.5,
            "free": 3.5,
            "swap_used": 1.2,
        },
        "disk_usage": {
            "total": 500,
            "used": 480,
        },
    }

    # Construct Sentences from the CSV
    triggers = InputBuilder.from_csv(triggers_csv, data_type=Trigger)

    # Generate the Derived Attributes
    da = DeriveTriggers(triggers, system_metrics, event_handler)
    da.derive()


if __name__ == "__main__":
    derive_triggers_system_monitoring()
