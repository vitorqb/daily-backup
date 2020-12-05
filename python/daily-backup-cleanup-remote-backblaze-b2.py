#!/usr/bin/env python3
"""
Python3 script to cleanup the b2 uploaded files.
REQUIRES `b2sdk` python lib to be installed and importable.
Reads env vars DAILY_BACKUP_B2_API_KEY and DAILY_BACKUP_B2_API_KEY_ID.
"""

import b2sdk.api
import argparse
import os
import sys
import datetime
import re
import time


# Globals
DAILY_BACKUP_B2_API_KEY = os.environ['DAILY_BACKUP_B2_API_KEY']
DAILY_BACKUP_B2_API_KEY_ID = os.environ['DAILY_BACKUP_B2_API_KEY_ID']


# CLI Parsing
parser = argparse.ArgumentParser('Cleanup old files uploaded to b2')
parser.add_argument('-r', '--max-retries', help='Maximum of retries attempts of cleanup', default=60)
parser.add_argument('-w', '--wait-between', help='Seconds to wait between two upload failures', default=60)
parser.add_argument('-b', '--bucket-name', help='The name of the bucket to use', required=True)
parser.add_argument('-n', '--files-to-keep', help='The number of files to keep', default=30, type=int)
parser.add_argument('-p', '--backup-prefix', help='A common prefix for the files to delete', default="DAILY_BACKUP__")


# Helpers
def cleanup(args):
    print("Starting B2 client...", flush=True)
    b2 = b2sdk.api.B2Api()

    print("Authorizing account...", flush=True)
    b2.authorize_account('production', DAILY_BACKUP_B2_API_KEY_ID, DAILY_BACKUP_B2_API_KEY)

    print("Getting all files in bucket...", flush=True)
    bucket = b2.get_bucket_by_name(args.bucket_name)
    files = bucket.ls()
    files = (x for (x, _) in files)
    files = (x for x in files if x.file_name.startswith(args.backup_prefix))
    files = sorted(files, key=lambda x: x.file_name)
    print(f"FOUND {len(files)} FILES")
    files = files[args.files_to_keep:]
    print(f"CLEANING {len(files)} FILES")
    for file_ in files:
        print(f"Deleting file {file_.file_name}")
        b2.delete_file_version(file_.id_, file_.file_name)


# Script
if __name__ == "__main__":
    args = parser.parse_args()
    counter = 0
    success = False
    while counter < args.max_retries and not success:
        try:
            print(f"ATTEMPT {counter}", flush=True)
            cleanup(args)
            success = True
        except Exception as e:
            print("FAILED WITH EXCEPTION:", flush=True)
            print(e, flush=True)
            print(f"TRYING AGAIN IN {args.wait_between} SECOND", flush=True)
            time.sleep(args.wait_between)
