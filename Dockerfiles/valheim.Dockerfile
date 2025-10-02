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
# USER steam
WORKDIR /home/steam

# ====== Install SteamCMD ======
RUN mkdir -p $STEAMCMD_HOME && \
    cd $STEAMCMD_HOME && \
    wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz -O steamcmd_linux.tar.gz && \
    tar -xvzf steamcmd_linux.tar.gz && \
    rm steamcmd_linux.tar.gz
RUN mkdir -p /home/steam/valheim && chown -R steam:steam /home/steam/valheim

# ====== Install Valheim dedicated server ======
RUN $STEAMCMD_HOME/steamcmd.sh +login anonymous +force_install_dir $VALHEIM_HOME +app_update 896660 validate +quit

# ====== Install BepInEx (Linux x64 stable) ======
RUN cd $VALHEIM_HOME && \
    wget -q https://sourceforge.net/projects/bepinex.mirror/files/v5.4.22/BepInEx_unix_5.4.22.0.zip/download -O bepinex.zip && \
    unzip bepinex.zip -d $VALHEIM_HOME && \
    rm bepinex.zip

# ====== Add run_bepinex.sh script ======
COPY valheim_run_bepinex.sh $VALHEIM_HOME/run_bepinex.sh
RUN chmod +x $VALHEIM_HOME/run_bepinex.sh
# ====== Add run_valheim.sh script ======
RUN cat > $VALHEIM_HOME/run_valheim.sh <<'EOF' && chmod +x $VALHEIM_HOME/run_valheim.sh
    #!/bin/sh
    # Wrapper to launch Valheim + BepInEx in headless X
    cd /home/steam/valheim

    # Pass all arguments through
    exec xvfb-run -a ./run_bepinex.sh "$@"
    EOF


# ====== Expose UDP ports ======
EXPOSE 2456/udp 2457/udp 2458/udp

# ====== Set workdir and entrypoint ======
WORKDIR $VALHEIM_HOME
ENTRYPOINT ["./run_valheim.sh"]
