#!/usr/bin/env python3
"""
Python3 script to upload the daily backup file using backblaze.
REQUIRES `b2sdk` python lib to be installed and importable.
Reads env vars DAILY_BACKUP_B2_API_KEY and DAILY_BACKUP_B2_API_KEY_ID.
"""

import b2sdk.api
import b2sdk.progress
import argparse
import os
import sys
import datetime
import re

# Globals
DAILY_BACKUP_B2_API_KEY = os.environ['DAILY_BACKUP_B2_API_KEY']
DAILY_BACKUP_B2_API_KEY_ID = os.environ['DAILY_BACKUP_B2_API_KEY_ID']
DATE_FORMAT="%Y-%m-%dT%H:%M:%S"

# CLI Parsing
parser = argparse.ArgumentParser('Uploads daily backup file using b2')
parser.add_argument('-f', '--file-name', help='The path to the file to be uploaded', required=True)
parser.add_argument('-b', '--bucket-name', help='The name of the bucket to use', required=True)
parser.add_argument('-w', '--wait-between', help='Seconds to wait between two upload failures', default=60)
parser.add_argument('-r', '--max-retries', help='Maximum of retries attempts of failured uploads before giving up', default=60)

# Helpers
def destination_file_name(original_file_name):
    """
    Returns a name to be used as the file name on the destination bucket,
    given the original file name.
    """
    reg = re.compile("[^\/]*$")
    return reg.search(original_file_name).group(0)

def upload(args):
    dest_file = destination_file_name(args.file_name)

    print("Starting B2 client...", flush=True)
    b2 = b2sdk.api.B2Api()

    print("Authorizing account...", flush=True)
    b2.authorize_account('production', DAILY_BACKUP_B2_API_KEY_ID, DAILY_BACKUP_B2_API_KEY)

    print("Uploading file...", flush=True)
    progress = b2sdk.progress.SimpleProgressListener("Upload")
    bucket = b2.get_bucket_by_name(args.bucket_name)
    bucket.upload_local_file(args.file_name, dest_file, progress_listener=progress)


# Script
if __name__ == "__main__":
    args = parser.parse_args()
    counter = 0
    success = False
    while counter < args.max_retries and not success:
        counter += 1
        try:
            print(f"ATTEMPT {counter}", flush=True)
            upload(args)
            success=True
        except Exception as e:
            print("FAILED WITH EXCEPTION:", flush=True)
            print(e, flush=True)
            print(f"TRYING AGAIN IN {args.wait_between} SECOND", flush=True)
            sleep(args.wait_between)
