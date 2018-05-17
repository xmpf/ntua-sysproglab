CC = gcc

CFLAGS = -Wall
CFLAGS += -g
# CFLAGS += -O2 -fomit-frame-pointer -finline-functions

LIBS =

BINS = server client

all: $(BINS)

server: server.c common.h
	$(CC) $(CFLAGS) -o $@ $< $(LIBS)

client: client.c common.h
	$(CC) $(CFLAGS) -o $@ $< $(LIBS)

clean:
	rm -f *.o *~ $(BINS)
