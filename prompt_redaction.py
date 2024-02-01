# Read log file test.log as lines
lines = open('test.log').readlines()

redacted_lines = []

# Identify UUIDs with prompt removal requests
uuids_for_removal = []
for line in lines:
    parts = line.split(',')
    if "PROMPT REMOVAL REQUEST" in line:
        uuids_for_removal.append(parts[1])

# Replace the text for those UUIDs with "REDACTED"
for line in lines:
    parts = line.split(',')
    uuid = parts[1]
    if uuid in uuids_for_removal:
        redacted_line = ','.join([parts[0], uuid, "REDACTED"] + parts[-4:])
        redacted_lines.append(redacted_line)
    else:
        redacted_lines.append(line)

# Join the lines back together
processed_log = ''.join(redacted_lines)
processed_log

# Write the processed log to a new file
with open('processed_test.log', 'w') as f:
    f.write(processed_log)
