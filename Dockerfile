FROM alpine:3.16

WORKDIR /root

# switch repo to edge
RUN echo -e "http://dl-3.alpinelinux.org/alpine/edge/main\nhttp://dl-3.alpinelinux.org/alpine/edge/community" > /etc/apk/repositories

RUN apk update && apk upgrade && \
    apk add --no-cache python3 py-pip kubo && \
	wget https://yt-dl.org/downloads/latest/youtube-dl -O /usr/local/bin/youtube-dl && \
	chmod a+rx /usr/local/bin/youtube-dl && \
	ipfs config --json Experimental.FilestoreEnabled true && \

# Swarm TCP; should be exposed to the public
EXPOSE 4001
# Swarm UDP; should be exposed to the public
EXPOSE 4001/udp

# run overlays
COPY * ./
RUN chmod 755 run.sh
CMD ["run.sh"]

