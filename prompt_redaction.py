import argparse
import os

def main():

    # Read log file test.log as lines
    lines = open(args.file).readlines()
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
    with open(f"processed_{args.file}", 'w') as f:
        f.write(processed_log)

    if args.destroy_original:
        os.remove(args.file)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Redact prompts from a log file based on requests.")
    parser.add_argument('-f','--file',help="File to process.",required=True)
    parser.add_argument('-d','--destroy_original',action='store_true',help="Delete the original file when done.",required=False, default=False)
    args = parser.parse_args()
    main()
