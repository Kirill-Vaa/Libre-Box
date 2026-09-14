#!/usr/bin/env bash
set -euo pipefail

mkdir -p /root/data /root/.box/logs /opt/state
touch /root/.box/ready

exec sleep infinity