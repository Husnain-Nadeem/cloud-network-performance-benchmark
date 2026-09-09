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
packet_loss = float(loss_match.group(1)) if loss_match else 0

rtt_match = re.search(
    r'=\s([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)',
    output
)

if rtt_match:
    min_latency = float(rtt_match.group(1))
    avg_latency = float(rtt_match.group(2))
    max_latency = float(rtt_match.group(3))
    jitter = float(rtt_match.group(4))
else:
    min_latency = avg_latency = max_latency = jitter = 0

print(avg_latency)
print(packet_loss)
print(jitter)