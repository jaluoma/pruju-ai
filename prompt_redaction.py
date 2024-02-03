# This script can be used to redact prompts from a log file based on requests.

import argparse
import os

def prompt_redaction_from_file(file:str, destroy_original:bool):
    # Read log file test.log as lines
    lines = open(file).readlines()
    redacted_lines = []

    # Identify UUIDs with prompt removal requests
    uuids_for_removal = []
    for line in lines:
        parts = line.split(',')
        if "PROMPT REMOVAL REQUEST" in line:
            if parts[3] == "0": # Ensure that that the prompt removal request was not injected
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

    # Parse directory and filename from the input file
    directory, filename = os.path.split(file)
    
    if directory != "":
        directory += "/"

    # Write the processed log to a new file
    with open(f"{directory}processed_{filename}", 'w') as f:
        f.write(processed_log)

    if destroy_original:
        os.remove(file)

def main():
    prompt_redaction_from_file(args.file, args.destroy_original)

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Redact prompts from a log file based on requests.")
    parser.add_argument('-f','--file',help="File to process.",required=True)
    parser.add_argument('-d','--destroy_original',action='store_true',help="Delete the original file when done.",required=False, default=False)
    args = parser.parse_args()
    main()
