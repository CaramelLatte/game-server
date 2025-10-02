# ====== Base image ======
FROM debian:bookworm-slim

# ====== Environment setup ======
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/steam
ENV STEAMCMD_HOME=/home/steam/steamcmd
ENV VALHEIM_HOME=/home/steam/valheim
WORKDIR $VALHEIM_HOME

# ====== Dependencies ======
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    file \
    nano \
    unzip \
    libc6:i386 \
    lib32gcc-s1 \
    lib32stdc++6 \
    libcurl4 \
    libssl3 \
    libgcc1 \
    libstdc++6 \
    xvfb \
    xauth \
    x11-utils \
    libx11-6 \
    libxrandr2 \
    libglu1-mesa \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

# ====== Create steam user ======
RUN useradd -m steam
WORKDIR /home/steam

# ====== Install SteamCMD ======
RUN mkdir -p $STEAMCMD_HOME && \
    cd $STEAMCMD_HOME && \
    wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz -O steamcmd_linux.tar.gz && \
    tar -xvzf steamcmd_linux.tar.gz && \
    rm steamcmd_linux.tar.gz

    
    # ====== Install Valheim dedicated server ======
    RUN $STEAMCMD_HOME/steamcmd.sh +login anonymous +force_install_dir $VALHEIM_HOME +app_update 896660 validate +quit
    
    # ====== Install BepInEx (Linux x64 stable) ======
    RUN cd $VALHEIM_HOME && \
    wget -q https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.2/BepInEx_x64_5.4.23.2.zip -O bepinex.zip && \
    unzip bepinex.zip -d $VALHEIM_HOME && \
    rm bepinex.zip
    
    # ====== Create run_bepinex.sh wrapper ======
    RUN cat > $VALHEIM_HOME/run_bepinex.sh <<'EOF' && chmod +x $VALHEIM_HOME/run_bepinex.sh
    #!/bin/sh
    set -eu
    
    : "${SERVER_NAME:=My Valheim Server}"
    : "${WORLD_NAME:=Dedicated}"
    : "${SERVER_PASS:=secret}"
    : "${PORT:=2456}"
    : "${PUBLIC:=1}"
    : "${ADDITIONAL_ARGS:=}"
    
    cd /home/steam/valheim
    

    # Run Valheim server with BepInEx under xvfb (headless X)
    exec xvfb-run -a ./BepInEx/run_bepinex.sh ./valheim_server.x86_64 \
    -nographics -batchmode \
    -name "${SERVER_NAME}" \
    -port "${PORT}" \
    -world "${WORLD_NAME}" \
    -password "${SERVER_PASS}" \
    -public "${PUBLIC}" \
    ${ADDITIONAL_ARGS} "$@"
    EOF


# ====== Expose UDP ports ======
EXPOSE 2456/udp 2457/udp 2458/udp
# ====== Set workdir and entrypoint ======
WORKDIR $VALHEIM_HOME
ENTRYPOINT ["./run_bepinex.sh"]
