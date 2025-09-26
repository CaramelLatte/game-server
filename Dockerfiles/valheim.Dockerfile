FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    lib32gcc-s1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -d /home/gameserver gameserver

USER gameserver
WORKDIR /home/gameserver/valheim

USER root
RUN mkdir -p /opt/steamcmd && chown gameserver:gameserver /opt/steamcmd
USER gameserver

WORKDIR /opt/steamcmd

RUN wget https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz \
    && tar -xvzf steamcmd_linux.tar.gz \
    && rm steamcmd_linux.tar.gz

RUN ./steamcmd.sh +login anonymous \
    +force_install_dir /home/gameserver/valheim \
    +app_update 896660 validate \
    +quit
    
EXPOSE 2456/udp 2457/udp 2458/udp

WORKDIR /home/gameserver/valheim

RUN wget https://github.com/BepInEx/BepInEx/releases/download/v5.4.21/BepInEx_x64_5.4.21.0.zip \
    && unzip BepInEx_x64_5.4.21.0.zip -d /home/gameserver/valheim \
    && rm BepInEx_x64_5.4.21.0.zip

RUN echo '#!/bin/bash' > /home/gameserver/valheim/start-server.sh && \
    echo 'cd /home/gameserver/valheim' >> /home/gameserver/valheim/start-server.sh && \
    echo './valheim_server.x86_64 -name "Nerds" -port 2456 -world "Nerdaria" -password "onlynerdsplayvalheim" -public 1' >> /home/gameserver/valheim/start-server.sh

RUN chmod +x /home/gameserver/valheim/start-server.sh
ENTRYPOINT ["/home/gameserver/valheim/start-server.sh"]

LABEL maintainer="jared.ekenstam@gmail.com"
LABEL game="valheim"
LABEL version="1.0"
