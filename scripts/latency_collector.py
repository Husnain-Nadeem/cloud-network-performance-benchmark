# latency_collector.py

import subprocess
import csv
import re
from datetime import datetime

TARGET_IP = "35.93.195.101"

result = subprocess.run(
    ["ping", "-c", "20", TARGET_IP],
    capture_output=True,
    text=True
)

output = result.stdout

loss_match = re.search(r'(\d+)% packet loss', output)
loss = loss_match.group(1) if loss_match else "0"

rtt_match = re.search(
    r'=\s([\d\.]+)/([\d\.]+)/([\d\.]+)/',
    output
)

avg_latency = rtt_match.group(2) if rtt_match else "0"

with open("latency.csv", "a", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        datetime.now(),
        TARGET_IP,
        avg_latency,
        loss
    ])

print("Measurement saved")