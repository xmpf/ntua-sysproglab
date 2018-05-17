#ifndef _COMMON_H
#define _COMMON_H

#include <sys/select.h>
#include <assert.h>

#define TCP_PORT 35001
#define TCP_BACKLOG 10
#define BUF_LEN 20

#ifndef STDIN_FILENO
#define STDIN_FILENO 0
#endif

#ifndef INET6_ADDRSTRLEN
#define INET6_ADDRSTRLEN 46
#endif

#define STRCAT_MACRO(A,B) A ## B

/* Insist until all of the data has been written */
ssize_t insist_write(int fd, const void *buf, size_t cnt)
{
	ssize_t ret;
	size_t orig_cnt = cnt;

	while (cnt > 0) {
	        ret = write(fd, buf, cnt);
	        if (ret < 0)
	                return ret;
	        buf += ret;
	        cnt -= ret;
	}

	return orig_cnt;
}


ssize_t insist_read(int fd, const void *buf, size_t cnt)
{
    ssize_t ret;
    size_t orig_cnt = cnt;

    while (cnt > 0) {
        ret = read(fd, (void *)buf, cnt);
        if (ret < 0) { return ret; }
        buf += ret;
        cnt -= ret;
    }

    return orig_cnt;
}

ssize_t insist_send(int fd, const void *buf, size_t len, int how)
{
    ssize_t ret;
    size_t orig_len = len;
    while (len > 0) {
        ret = send(fd, buf, len, how);
        if (ret < 0) { return ret; }
        buf += ret;
        len -= ret;
    }

    return orig_len;
}

void *get_in_addr(struct sockaddr *sa)
/* https://beej.us/guide/bgnet/pdf/bgnet_A4_2.pdf */
{
    if ( sa->sa_family == AF_INET ) { /* handle IPv4 */
        return &(((struct sockaddr_in *)sa)->sin_addr);
    }
    return &(((struct sockaddr_in6 *)sa)->sin6_addr); /* IPv6 */
}

/* add a fd to fd_set, and update max_fd */
int safe_fd_set(int fd, fd_set* fds, int* max_fd)
/* http://jhshi.me/2013/11/02/use-select-to-monitor-multiple-file-descriptors/index.html */
{
    assert(max_fd != NULL);
    FD_SET(fd, fds);
    if (fd > *max_fd) {
        *max_fd = fd;
    }
    return 0;
}

/* clear fd from fds, update max fd if needed */
int safe_fd_clr(int fd, fd_set* fds, int* max_fd)
/* http://jhshi.me/2013/11/02/use-select-to-monitor-multiple-file-descriptors/index.html */
{
    assert(max_fd != NULL);
    FD_CLR(fd, fds);
    if (fd == *max_fd) {
        (*max_fd)--;
    }
    return 0;
}


#endif