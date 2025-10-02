
#!/bin/sh
set -eu

# Defaults (can be overridden by docker run -e ...)
: "${SERVER_NAME:=My Valheim Server}"
: "${WORLD_NAME:=Dedicated}"
: "${SERVER_PASS:=secret}"
: "${PORT:=2456}"
: "${PUBLIC:=1}"
: "${ADDITIONAL_ARGS:=}"

cd /home/steam/valheim

echo "Starting Valheim + BepInEx..."
echo "  Name:  $SERVER_NAME"
echo "  World: $WORLD_NAME"
echo "  Port:  $PORT"
echo "  Public:$PUBLIC"

# BepInEx expects to be run as a wrapper around the server binary
exec ./BepInEx/run_bepinex.sh ./valheim_server.x86_64 \
  -nographics -batchmode \
  -name "${SERVER_NAME}" \
  -port "${PORT}" \
  -world "${WORLD_NAME}" \
  -password "${SERVER_PASS}" \
  -public "${PUBLIC}" \
  ${ADDITIONAL_ARGS}
