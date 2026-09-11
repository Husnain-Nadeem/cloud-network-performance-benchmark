import os
import subprocess
import csv
import re
from datetime import datetime

TARGET_IP = "35.93.195.101"

# --------------------
# LATENCY SECTION
# --------------------

ping_result = subprocess.run(
    ["ping", "-c", "20", TARGET_IP],
    capture_output=True,
    text=True
)

ping_output = ping_result.stdout

loss_match = re.search(r'(\d+(?:\.\d+)?)% packet loss', ping_output)

packet_loss = float(loss_match.group(1)) if loss_match else 0

rtt_match = re.search(
    r'=\s*([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)',
    ping_output
)

if rtt_match:
    min_latency = float(rtt_match.group(1))
    avg_latency = float(rtt_match.group(2))
    max_latency = float(rtt_match.group(3))
    jitter = float(rtt_match.group(4))
else:
    min_latency = avg_latency = max_latency = jitter = 0

# --------------------
# THROUGHPUT SECTION
# --------------------

iperf_result = subprocess.run(
    ["iperf3", "-c", TARGET_IP],
    capture_output=True,
    text=True
)

iperf_output = iperf_result.stdout

# Match the sender line, for example:
# [SUM]   0.00-10.00  sec  212 MBytes   178 Mbits/sec  1479             sender
#
# Also works with lines without [SUM].

sender_match = re.search(
    r'([\d.]+)\s+Mbits/sec\s+(\d+)\s+sender',
    iperf_output,
    re.IGNORECASE
)

if sender_match:
    throughput = float(sender_match.group(1))
    retransmissions = int(sender_match.group(2))
else:
    throughput = 0
    retransmissions = 0

# --------------------
# DEBUG OUTPUT
# --------------------

print("iperf3 output:")
print(iperf_output)

print("Throughput:", throughput, "Mbps")
print("Retransmissions:", retransmissions)

# --------------------
# WRITE CSV
# --------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(BASE_DIR, "data", "network_metrics.csv")

with open(
    CSV_FILE,
    "a",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        datetime.now().isoformat(),
        "us-east-1",
        "us-west-2",
        avg_latency,
        min_latency,
        max_latency,
        packet_loss,
        jitter,
        throughput,
        retransmissions
    ])

print("Measurement saved")
