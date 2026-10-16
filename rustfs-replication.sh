#!/usr/bin/env bash
# Configure two-way (active-active style) bucket replication between the
# rustfs and rustfs2 containers using the MinIO client (mc).
# Usage: ./rustfs-replication.sh [bucket]
# Requires: docker, containers running from docker-compose.rustfs.yml, rustfs.env.
# Note: RustFS replication support depends on the image version; pin a tag.
set -euo pipefail
cd "$(dirname "$0")"
set -a; . ./rustfs.env; set +a

BUCKET="${1:-repl-test}"
NET=rustfs-net
A=http://rustfs:9000
B=http://rustfs2:9000

mc() {
  docker run --rm --network "$NET" \
    -e MC_HOST_a="http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@rustfs:9000" \
    -e MC_HOST_b="http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@rustfs2:9000" \
    minio/mc "$@"
}

for s in a b; do
  mc mb --ignore-existing "$s/$BUCKET"
  mc version enable "$s/$BUCKET"
done

# a -> b and b -> a (both with delete + existing-object replication)
mc replicate add "a/$BUCKET" --remote-bucket "http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@rustfs2:9000/$BUCKET" \
  --replicate "delete,delete-marker,existing-objects"
mc replicate add "b/$BUCKET" --remote-bucket "http://${RUSTFS_ACCESS_KEY}:${RUSTFS_SECRET_KEY}@rustfs:9000/$BUCKET" \
  --replicate "delete,delete-marker,existing-objects"

mc replicate ls "a/$BUCKET"
mc replicate ls "b/$BUCKET"
echo "Verify: upload to localhost:9002 / 9007 (s3_ops.py) and check the other side."
