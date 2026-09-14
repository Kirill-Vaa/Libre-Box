#!/bin/sh
set -eu

DATABASE=/database/filebrowser.db

if [ ! -f "$DATABASE" ]; then
    filebrowser -d "$DATABASE" config init
    filebrowser -d "$DATABASE" config set --auth.method=proxy --auth.header=X-Auth-User --baseurl /files --root /srv --address 0.0.0.0 --port 80
    filebrowser -d "$DATABASE" users add root "$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n')" --perm.admin
fi

exec filebrowser -d "$DATABASE" --baseurl /files --root /srv --address 0.0.0.0 --port 80