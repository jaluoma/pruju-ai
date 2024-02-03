# Script to process prompt redaction requests in a given folder.

import argparse
import os
import datetime

from prompt_redaction import prompt_redaction_from_file

def main():
    # Get the date in format YYYY-MM-DD
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    print(f"Processing prompt redaction requests in {args.path}...")
    print(f"Delete original files {args.destroy_original}")
    print(f"Exclude files from: {today}")
    
    for root, dirs, files in os.walk(args.path):
        for file in files:
            # Exclude files from today
            if today in file:
                print(f"Excluding a file from today: {file}")
                continue
            if "processed" in file:
                print(f"Excluding an already processed file: {file}")
                continue
            if ".log" in file:
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}...")
                prompt_redaction_from_file(file_path, args.destroy_original)    

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Process prompt redaction requests in a given folder.")
    parser.add_argument('-p','--path',help="Path to process.",required=True)
    parser.add_argument('-d','--destroy_original',action='store_true',help="Delete the original files when done.",required=False, default=False)
    args = parser.parse_args()
    main()