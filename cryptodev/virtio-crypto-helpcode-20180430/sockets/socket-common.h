/*
 * socket-common.h
 *
 * Simple TCP/IP communication using sockets
 *
 * Vangelis Koukis <vkoukis@cslab.ece.ntua.gr>
 */

#ifndef _SOCKET_COMMON_H
#define _SOCKET_COMMON_H

/* Compile-time options */
#define TCP_PORT    35001
#define TCP_BACKLOG 5

#define BUF_LEN 100
#define HELLO_THERE "Hello There"

/* General purpose functions */
#include <arpa/inet.h>
#include <errno.h>
#include <stdio.h>

int isIP (char *str)
{
    int res = 0;
    unsigned long ip;
    errno = 0;
    res = inet_pton (AF_INET, str, &ip);
    if (errno != 0) {   // error occured
        fprintf (stderr, "[ERROR] Argument is not a valid IP address.\n" \
                         "%s\n", strerror(errno));
    }
    return res;
}

int isPort (char *str, int *port)
{
    char *curr = str;
    while ( *curr != '\0' && curr != NULL ){
        if ((*curr < '0') || (*curr > '9')) {
            return -1;
        }
        curr++;
    }
    *port = atoi(str);
    return ((*port >= 0) && (*port < 65536));
}
/*****************************/

#endif /* _SOCKET_COMMON_H */

