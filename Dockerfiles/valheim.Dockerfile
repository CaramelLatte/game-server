FROM debian:bookworm-slim

# Install dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    curl \
    file \
    nano \
    unzip \
    lib32gcc-s1 \
    lib32stdc++6 \
    libcurl4 \
    libssl3 \
    libgcc1 \
    libstdc++6 \
    libc6:i386 \
    libx11-6 \
    libxrandr2 \
    libglu1-mesa \
    libxinerama1 \
    libxcursor1 \
    libxi6 \
    xvfb \
    xauth \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m steam
USER steam
WORKDIR /home/steam

# Install SteamCMD
RUN mkdir steamcmd && \
    cd steamcmd && \
    curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf - && \
    ./steamcmd.sh +quit

# Install Valheim Dedicated Server
RUN ./steamcmd/steamcmd.sh \
    +login anonymous \
    +force_install_dir /home/steam/valheim \
    +app_update 896660 validate \
    +quit

# Install BepInEx (Linux / Unix build)
RUN cd /home/steam && \
    wget -q https://sourceforge.net/projects/bepinex.mirror/files/v5.4.22/BepInEx_unix_5.4.22.0.zip/download -O bepinex.zip && \
    unzip bepinex.zip -d valheim && \
    rm bepinex.zip


    
COPY ./Dockerfiles/valheim_run_bepinex.sh /home/steam/valheim/run_bepinex.sh
RUN sed -i 's/\r$//' /home/steam/valheim/run_bepinex.sh && chmod +x /home/steam/valheim/run_bepinex.sh


# Make sure the BepInEx run script is executable
RUN chmod u+x /home/steam/valheim/run_bepinex.sh
# Expose default ports
EXPOSE 2456/udp 2457/udp 2458/udp
ENV HOME=/home/steam
WORKDIR /home/steam/valheim

# Note: Use the BepInEx startup script that comes with the linux build (if present),
# or fallback to the original server start with modifications.
ENTRYPOINT ["./run_bepinex.sh"]
