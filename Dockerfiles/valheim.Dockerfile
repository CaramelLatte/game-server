FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    libpulse0 \
    libsdl2-2.0-0 \
    libx11-6 \
    libxcursor1 \
    libxrandr2 \
    libxi6 \
    libgl1-mesa-glx \
    wget \
    unzip \
    curl \
    tar \
    ca-certificates \
    lib32gcc1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -d /home/gameserver gameserver

# USER gameserver
# WORKDIR /home/gameserver/

USER root
RUN mkdir -p /home/gameserver/container-test/steamcmd && chown gameserver:gameserver /home/gameserver/container-test/steamcmd

WORKDIR /home/gameserver/container-test/steamcmd

RUN wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz \
    && tar -xvzf steamcmd_linux.tar.gz \
    && rm steamcmd_linux.tar.gz
RUN mkdir -p /home/gameserver/valheim && chown gameserver:gameserver /home/gameserver/valheim
RUN ./steamcmd.sh +force_install_dir /home/gameserver/container-test/valheim \
    +login anonymous \
    +app_update 896660 validate \
    +quit
    
EXPOSE 2456/udp 2457/udp 2458/udp

WORKDIR /home/gameserver/container-test/valheim/

RUN wget https://github.com/BepInEx/BepInEx/releases/download/v5.4.21/BepInEx_x64_5.4.21.0.zip \
    && unzip BepInEx_x64_5.4.21.0.zip -d /home/gameserver/container-test/valheim \
    && rm BepInEx_x64_5.4.21.0.zip

RUN echo '#!/bin/bash' > /home/gameserver/container-test/valheim/start-server.sh && \
 echo './valheim_server.x86_64 -nographics -batchmode -name "Nerds" -port 2456 -world "Nerdaria" -password "onlynerdsplayvalheim" -public 1' >> /home/gameserver/container-test/valheim/start-server.sh

RUN echo "892970" > /home/gameserver/container-test/valheim/steam_appid.txt

USER root
RUN chown gameserver:gameserver /home/gameserver/container-test/valheim/start-server.sh
RUN chmod +x /home/gameserver/container-test/valheim/start-server.sh
ENTRYPOINT ["/home/gameserver/container-test/valheim/start-server.sh"]

ENV SteamAppId=892970
ENV SteamGameId=892970
ENV LD_LIBRARY_PATH=/home/gameserver/container-test/valheim:$LD_LIBRARY_PATH
LABEL maintainer="jared.ekenstam@gmail.com"
LABEL game="valheim"
LABEL version="1.0"
