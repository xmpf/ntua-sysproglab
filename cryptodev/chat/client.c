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

#ifndef DEBUG_ON
#define DEBUG_ON 1
#endif

int main (int argc, char *argv[])
{
    signal (SIGPIPE, SIG_IGN);  /* Make sure a broken connection doesn't kill us */

    if (argc != 3) {
        fprintf (stderr, "Usage: %s <hostname> <port>\n", argv[0]);
        exit (EXIT_FAILURE);
    }

    /* Variables */
    char *hostname = argv[1];
    int port = atoi(argv[2]); /* NEEDS BETTER ERROR CHECKING */
    if ( (port < 0) || (port > 65535) ) {
        fprintf (stderr, "[E] Port number \"%d\" does not exist\n", port);
        exit (EXIT_FAILURE);
    }

    /* KEEPS INFO ABOUT SERVICE HOST */
    struct hostent *host;

	if ((host = gethostbyname (hostname)) == NULL) { /* GETHOSTBYNAME */
		fprintf (stderr, "[E] DNS lookup failed for host %s\n", hostname);
		exit (EXIT_FAILURE);
	}

#if DEBUG_ON
    fprintf (stdout, "[I] Hostname: %s\n" \
                     "[I] IP Address: %s\n", host->h_name,
                     inet_ntoa (*((struct in_addr *)host->h_addr_list[0])));
#endif


	int sd; /* socket file descriptor */
	errno = 0;
	if ((sd = socket(AF_INET, SOCK_STREAM, 0)) < 0) { /* SOCKET */
		fprintf (stderr, "[E] Unable to create TCP socket - %s\n", strerror(errno));
		exit (EXIT_FAILURE);
	}
	fprintf(stdout, "[I] Created TCP socket\n");

    /* HANDLING INTERNET ADDRESSES */
    struct sockaddr_in sa;
    sa.sin_family = AF_INET;    /* INTERNET ADDRESS */
    sa.sin_port = htons(port);  /* host to network (short) order */
    memcpy (&sa.sin_addr.s_addr, host->h_addr_list[0], sizeof(struct in_addr));
    fprintf(stdout, "[I] Connecting to remote host...\n"); fflush(stderr);
    errno = 0;
	if (connect(sd, (struct sockaddr *) &sa, sizeof(sa)) < 0) { /* CONNECT */
		fprintf (stderr, "[E] Unable to establish connection - %s\n", strerror(errno));
		exit (EXIT_FAILURE);
	}
	fprintf(stdout, "[I] Connection established!\n" \
	                "[I] Server: %s\n", inet_ntoa (*((struct in_addr *)host->h_addr_list[0])));


    /*
            void FD_CLR(int fd, fd_set *set);       --      remove a fd from the fd_set
            int  FD_ISSET(int fd, fd_set *set);     --      test if a certain fd in the fd_set or not.
            void FD_SET(int fd, fd_set *set);       --      add a fd to the fd_set
            void FD_ZERO(fd_set *set);              --      clear the fd_set
    */
    fd_set  master;
    int maxfd = sd; /* for select() */
    int nbytes; /* number of bytes */

    FD_ZERO(&master);
    safe_fd_set(STDIN_FILENO, &master, &maxfd);
    safe_fd_set(sd, &master, &maxfd);

    char buf[BUF_LEN];

    /* TODO */

    for (;;) {
        fd_set dup = master;   /* backup master */

        errno = 0;
        if (select(maxfd + 1, &dup, NULL, NULL, NULL) < 0) {
            fprintf(stderr, "[E] select - %s\n", strerror(errno));
            exit (EXIT_FAILURE);
        }

        /*  Notes:
                ssize_t recv(int sockfd, void *buf, size_t len, int flags):
                    The only difference between recv() and read(2) is the presence of flags.
                    With a zero flags argument, recv() is generally equivalent to read(2)
        */
        for (int fd = 0; fd < maxfd + 1; fd++) {
            if (FD_ISSET(fd, &dup)) { /* fd is ready */
                if ( fd == sd ) {    /* server socket ready: get data */
                        if ( (nbytes = recv(fd, buf, sizeof(buf), 0)) <= 0 ) {
                            if (nbytes == 0) {
                                fprintf (stderr, "[I] Connection closed\n");
                                exit (EXIT_FAILURE);
                            }
                            else {
                                perror ("recv");
                                exit (EXIT_FAILURE);
                            }
                        }
                        else { /* received nbytes of data */
                            /* TODO */
                            for (int i = 0; i < nbytes; i++) {
                                fprintf (stdout, "%c", buf[i]);
                            }
                            // fflush(stdout);
                        }
                }
                else if ( fd == STDIN_FILENO ) { /* client sends message */
                        memset (buf, '\0', BUF_LEN);
                        if ( (nbytes = read(0, buf, BUF_LEN)) < 0 ) {
                            perror ("read: client");
                            exit (EXIT_FAILURE);
                        }
                        /* TODO */

                        if ( insist_send (sd, buf, BUF_LEN, 0) < 0 ) {
                            perror ("insist_send");
                        }
                }

            }       /* if(FD_ISSET) */
        }           /* for(maxfd) */
    }               /* for(;;) */

    return 0;
}