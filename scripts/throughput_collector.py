import subprocess
import re

TARGET_IP = "35.93.195.101"

result = subprocess.run(
    ["iperf3", "-c", TARGET_IP],
    capture_output=True,
    text=True
)

output = result.stdout

bitrate_match = re.search(
    r'([\d\.]+)\sMbits/sec',
    output
)

retrans_match = re.search(
    r'\s(\d+)\s*$',
    output,
    re.MULTILINE
)

throughput = bitrate_match.group(1) if bitrate_match else "0"
retrans = retrans_match.group(1) if retrans_match else "0"

print("Throughput:", throughput)
print("Retransmissions:", retrans)