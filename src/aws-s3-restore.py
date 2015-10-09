#!/usr/bin/env python
# Interactive script for restoring a directory tree
#
# Written by Jonathan Love
# Copyright (c) Doubledot Media Ltd (http://www.doubledotmedia.com)
# Refer to LICENSE for more details

import time
import json
import os
import ConfigParser
from datetime import date, datetime, timedelta

from boto.s3.connection import S3Connection
from boto.s3.deletemarker import DeleteMarker
from boto.utils import parse_ts


def main():
    config = ConfigParser.ConfigParser()
    config.read(filenames=["aws-s3-restore.conf"])

    aws_access_key = config.get(section="aws", option="key")
    aws_access_secret = config.get(section="aws", option="secret")

    conn = S3Connection(aws_access_key, aws_access_secret)

    buckets = conn.get_all_buckets()

    print "The following buckets are available"
    print "\n".join(["- {}".format(bucket.name) for bucket in buckets])

    bucket = None
    while not bucket:
        print "Enter the exact name of the bucket to restore from:",
        name = raw_input().strip()
        bucket = next(
            iter([bucket for bucket in buckets if bucket.name == name]), None)
        if not bucket:
            print "Not a valid bucket"

    print "Using bucket `{bucket_name}`".format(bucket_name=bucket.name)

    restore_before = datetime.today()
    date_set = "n"
    while not date_set == "y":
        print "From how many days ago do you wish to restore? ",
        days = raw_input().strip()
        try:
            day_offset = int(days)
        except exceptions.ValueError:
            print "Error, you must supply an integer"
            continue
        restore_before = datetime.today() - timedelta(days=day_offset)
        print "Use files modified on `{date}` (or nearest preceding version) (y/N)? ".format(date=restore_before),
        date_set = raw_input().strip().lower()

    print
    print "Add files/folders for restoration"
    all_folders = "n"
    objects_to_restore = []
    while not all_folders == "y":
        print "Full path of file/folder to restore: ",
        add_folder = raw_input().strip()
        if add_folder[0] is not "/":
            print "Error, supplied path does not begin with a `/`; discarding"
        else:
            objects_to_restore.append(add_folder)
        print "Folders currently in restore set: "
        print "\n".join(["- {}".format(f) for f in objects_to_restore])

        print "Done adding folders (y/N)? ",
        all_folders = raw_input().strip().lower()

    print "NOTICE: Files will be restored to *this* working directory (and subdirectories)"
    print "Do you want to run the restore (y/N)? ",
    if not raw_input().strip().lower() == "y":
        os.exit(-1)
    else:
        valid_prefixes = []
        print "Running restore from bucket `{bucket_name}`".format(bucket_name=bucket.name)

        for obj in objects_to_restore:
            prefix = obj[1:]    # Remove the leading slash
            keys = bucket.get_all_versions(prefix=prefix)
            if not keys:
                print "Invalid prefix: `{obj}`".format(obj=obj)
            else:
                valid_prefixes.append(prefix)

        print
        print "Restoring files modified *before* `{restore_date}` (or nearest preceding version)".format(restore_date=restore_before)
        print "Aggregating backupset details..."
        # Determine the available versions for this file list
        all_files = {}
        for prefix in valid_prefixes:
            for version in bucket.list_versions(prefix=prefix):
                last_modified = parse_ts(version.last_modified)
                if last_modified < restore_before:
                    # Only restore if older than specified date
                    if version.name not in all_files or version.last_modified > all_files[version.name].last_modified:
                        # Add to list, or update if newer version available
                        all_files[version.name] = version

        total_file_count = len(all_files.keys())
        print "{count} file(s) to be restored".format(count=total_file_count)
        print
        print "Beginning Restore: "
        i = 0
        for file_prefix, version in all_files.iteritems():
            i = i + 1
            print "- ({number}/{total}): `{name}`".format(number=i, total=total_file_count, name=file_prefix)

            dirs = os.path.dirname(file_prefix)
            if not os.path.exists(dirs):
                os.makedirs(dirs)

            if isinstance(version, DeleteMarker):
                print "      WARNING: File was previously DELETED on {date}; skipping".format(date=version.last_modified)
            else:
                if not os.path.exists(file_prefix):
                    # Open relative to our working path
                    fp = open(file_prefix, "w")
                    version.get_file(fp, version_id=version.version_id)
                    fp.close()
                else:
                    print "      WARNING: Already exists at restore location; skipping"

if __name__ == '__main__':
    main()
