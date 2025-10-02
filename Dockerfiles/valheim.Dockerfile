FROM debian:bookworm-slim

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget lib32gcc-s1 lib32stdc++6 unzip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m steam
USER steam
WORKDIR /home/steam

# Install SteamCMD
RUN mkdir -p /home/steam/steamcmd && \
    cd /home/steam/steamcmd && \
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf - && \
    ./steamcmd.sh +quit

# Install Valheim Dedicated Server
RUN /home/steam/steamcmd/steamcmd.sh \
    +login anonymous \
    +force_install_dir /home/steam/valheim \
    +app_update 896660 validate \
    +quit

# Install BepInEx (latest stable release)
RUN cd /home/steam && \
    wget -q https://github.com/BepInEx/BepInEx/releases/download/v5.4.23.2/BepInEx_UnityMono_x64_5.4.23.2.zip -O bepinex.zip && \
    unzip bepinex.zip -d /home/steam/valheim && \
    rm bepinex.zip

# Expose default ports
EXPOSE 2456/udp 2457/udp 2458/udp

# Set entrypoint to Valheim server with BepInEx
WORKDIR /home/steam/valheim
ENTRYPOINT ["./start_server_bepinex.sh"]
```
