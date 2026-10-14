#!/usr/bin/env python3
"""Common S3 operations against the endpoint configured in .env.

Run without arguments for interactive mode.
"""
import argparse
import os
import shlex
import sys

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()


def client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("S3_ACCESS_KEY", "admin"),
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
    )


def list_buckets(s3, a):
    for b in s3.list_buckets()["Buckets"]:
        print(b["Name"])


def create_bucket(s3, a):
    s3.create_bucket(Bucket=a.bucket)
    print(f"Created bucket {a.bucket}")


def delete_bucket(s3, a):
    s3.delete_bucket(Bucket=a.bucket)
    print(f"Deleted bucket {a.bucket}")


def list_objects(s3, a):
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=a.bucket, Prefix=a.prefix):
        for o in page.get("Contents", []):
            print(f"{o['Size']:>12}  {o['LastModified']:%Y-%m-%d %H:%M}  {o['Key']}")


def upload(s3, a):
    key = a.key or os.path.basename(a.file)
    s3.upload_file(a.file, a.bucket, key)
    print(f"Uploaded {a.file} -> s3://{a.bucket}/{key}")


def download(s3, a):
    dest = a.file or os.path.basename(a.key)
    s3.download_file(a.bucket, a.key, dest)
    print(f"Downloaded s3://{a.bucket}/{a.key} -> {dest}")


def delete_object(s3, a):
    s3.delete_object(Bucket=a.bucket, Key=a.key)
    print(f"Deleted s3://{a.bucket}/{a.key}")


def copy_object(s3, a):
    s3.copy_object(
        Bucket=a.dest_bucket,
        Key=a.dest_key,
        CopySource={"Bucket": a.bucket, "Key": a.key},
    )
    print(f"Copied s3://{a.bucket}/{a.key} -> s3://{a.dest_bucket}/{a.dest_key}")


def info(s3, a):
    h = s3.head_object(Bucket=a.bucket, Key=a.key)
    print(f"Size:         {h['ContentLength']}")
    print(f"Content-Type: {h['ContentType']}")
    print(f"ETag:         {h['ETag']}")
    print(f"Modified:     {h['LastModified']}")


def presign(s3, a):
    print(
        s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": a.bucket, "Key": a.key},
            ExpiresIn=a.expires,
        )
    )


def build_parser():
    p = argparse.ArgumentParser(prog="s3", description=__doc__)
    sub = p.add_subparsers(dest="command")

    def cmd(name, func, help, *args):
        sp = sub.add_parser(name, help=help)
        for arg, kwargs in args:
            sp.add_argument(arg, **kwargs)
        sp.set_defaults(func=func)

    bucket = ("bucket", {})
    key = ("key", {})

    cmd("buckets", list_buckets, "list buckets")
    cmd("mb", create_bucket, "create a bucket", bucket)
    cmd("rb", delete_bucket, "delete an empty bucket", bucket)
    cmd("ls", list_objects, "list objects", bucket,
        ("prefix", {"nargs": "?", "default": ""}))
    cmd("put", upload, "upload a file", bucket, ("file", {}),
        ("key", {"nargs": "?", "help": "defaults to the file name"}))
    cmd("get", download, "download an object", bucket, key,
        ("file", {"nargs": "?", "help": "defaults to the key's base name"}))
    cmd("rm", delete_object, "delete an object", bucket, key)
    cmd("cp", copy_object, "copy an object", bucket, key,
        ("dest_bucket", {}), ("dest_key", {}))
    cmd("info", info, "show object metadata", bucket, key)
    cmd("presign", presign, "create a temporary download URL", bucket, key,
        ("--expires", {"type": int, "default": 3600, "help": "seconds"}))

    return p


def run(s3, p, argv):
    try:
        args = p.parse_args(argv)
    except SystemExit:
        return
    if not args.command:
        p.print_help()
        return
    try:
        args.func(s3, args)
    except (ClientError, BotoCoreError, OSError) as e:
        print(f"Error: {e}")


def interactive(s3, p):
    print("S3 interactive mode. Type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("s3> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line in ("exit", "quit"):
            break
        try:
            argv = shlex.split(line)
        except ValueError as e:
            print(f"Error: {e}")
            continue
        run(s3, p, ["-h"] if argv == ["help"] else argv)


def main():
    p = build_parser()
    if len(sys.argv) > 1:
        run(client(), p, sys.argv[1:])
    else:
        interactive(client(), p)


if __name__ == "__main__":
    main()
