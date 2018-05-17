#include <stdio.h>
#include <errno.h>
#include <ctype.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <netdb.h>

#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>

#include <arpa/inet.h>
#include <netinet/in.h>

#include "common.h"

#ifndef TCP_PORT
#define TCP_PORT 35001
#endif

#ifndef TCP_BACKLOG
#define TCP_BACKLOG 10
#endif

int main (int argc, char *argv[])
{
	signal(SIGPIPE, SIG_IGN);   /* Make sure a broken connection doesn't kill us */


    int sd;     /* socket descriptor */
    errno = 0;
    if ( (sd = socket(AF_INET, SOCK_STREAM, 0)) < 0 ) { /* Create TCP socket endpoint */
        fprintf (stderr, "[E] Unable to create socket - %s\n", strerror(errno));
        exit (EXIT_FAILURE);
    }
    fprintf(stdout, "[I] Created TCP socket\n");

    int yes = 1;
    /* int setsockopt(int sockfd, int level, int optname, const void *optval, socklen_t optlen); */
	if ( setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0 ) {
	/*
	    Linux will only allow port reuse with the SO_REUSEADDR option when this option was set both
	    in the previous program that performed a bind(2) to the port and in the program that wants to reuse the port.
	*/
		perror("setsockopt");
	 	exit (EXIT_FAILURE);
    }


    /* Bind to a well-known port */
    struct sockaddr_in sa;
	memset(&sa, 0, sizeof(sa));
	sa.sin_family = AF_INET;
	sa.sin_port = htons(TCP_PORT);
	sa.sin_addr.s_addr = htonl(INADDR_ANY);

	errno = 0;
	if (bind(sd, (struct sockaddr *)&sa, sizeof(sa)) < 0) { /* BIND */
		fprintf (stderr, "[E] Unable to assign address - %s\n", strerror(errno));
		exit (EXIT_FAILURE);
	}
	fprintf(stdout, "[I] Bound TCP socket to port %d\n", TCP_PORT);

	/* Listen for incoming connections */
	if (listen(sd, TCP_BACKLOG) < 0) {
		perror("listen");
		exit (EXIT_FAILURE);
	}

    fd_set master;
    FD_ZERO(&master);
    int maxfd = sd;
    safe_fd_set(sd, &master, &maxfd);

    /* TODO */

    int newsd;  /* client socket descriptor <<= accept() */
    struct sockaddr_storage remoteaddr; /* client address */
    socklen_t addrlen;
    char remoteIP[INET6_ADDRSTRLEN];
    char buf[BUF_LEN];  /* buffer to hold clients data */
    int nbytes; /* number of bytes */

    while (1) { /* Loop forever, accept()ing connections */
        fd_set dup = master;    /* backup master fd_set */
        if ( select(maxfd + 1, &dup, NULL, NULL, NULL) < 0 ) {
            perror ("select");
            exit (EXIT_FAILURE);
        }

        for (int fd = 0; fd < maxfd + 1; fd++) { /* cycle through file descriptors, checking for data */
            if ( FD_ISSET(fd, &dup) ) {
                /* TODO */
                if (fd == sd) {  /* handle new connections */
                    addrlen = sizeof(remoteaddr);
                    errno = 0;
                    if ( (newsd = accept(sd, (struct sockaddr *)&remoteaddr, &addrlen)) < 0 ) {
                        perror ("accept");
                        break;
                    }
                    safe_fd_set(newsd, &master, &maxfd);    /* add socket to master fd_set */
                    fprintf (stdout, "[I] New connection from %s on socket %d\n",
                                    inet_ntop(remoteaddr.ss_family,
                                              get_in_addr((struct sockaddr *)&remoteaddr),
                                              remoteIP, INET6_ADDRSTRLEN),
                                     newsd);
                }
                else { /* handle data from client */
                #if DEBUG
                    fprintf (stderr, "[I] We have some data\n");
                #endif
                    if ( (nbytes = recv(fd, buf, sizeof(buf), 0)) <= 0 ) {
                        (nbytes == 0) ? fprintf (stdout, "[I] Connection %d closed!\n", fd) : perror("recv");

                        shutdown(fd, SHUT_RDWR);
                        close(fd); /* GOODBYE */
                        safe_fd_clr(fd, &master, &maxfd); /* remove from master set, and update maxfd */
                    }
                    else { /* we have some data */
                        /* broadcast data to all clients */
                        fprintf (stdout, "[I] Broadcast from client %d...\n", fd);
                        for (int cfd = 0; cfd < maxfd + 1; cfd++) {
                            if ( FD_ISSET(cfd, &master) ) {
                                if ( (cfd != sd) && (cfd != fd) ) { /* don't send data to ourself (server) and OP (client) */
                                    errno = 0;
                                    insist_send(cfd, STRCAT_MACRO(Client, fd), 7, 0);
                                    if ( insist_send(cfd, buf, nbytes, 0) < 0 ) { perror("insist_send"); }
                                }   /* if(cfd) */
                            }       /* if(FD_ISSET()) */
                        }           /* for(cfd) */
                    }               /* nbytes > 0 */
                }                   /* fd != sd */
            }   /* if(FD_ISSET) */
        }       /* for(maxfd)*/
    }           /* while(1) */

    return 0;
}