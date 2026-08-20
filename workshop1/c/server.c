/* Equivalent of server-socket.py: receives a sentence, replies with it in uppercase.
   Portable: compiles with POSIX sockets (Linux/WSL) or Winsock2 (native Windows/MinGW). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <signal.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef SOCKET sock_t;
    #define SOCK_INVALID INVALID_SOCKET
    #define CLOSESOCK closesocket
    #define SLEEP_SEC(x) Sleep((x) * 1000)
#else
    #include <unistd.h>
    #include <arpa/inet.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    typedef int sock_t;
    #define SOCK_INVALID (-1)
    #define CLOSESOCK close
    #define SLEEP_SEC(x) sleep(x)
#endif

#define BUFFER_SIZE 1024

static sock_t serverSocketGlobal = SOCK_INVALID;

void handleSigint(int sig) {
    (void)sig;
    printf("\nServer is shutting down.\n");
    if (serverSocketGlobal != SOCK_INVALID) {
        CLOSESOCK(serverSocketGlobal);
    }
#ifdef _WIN32
    WSACleanup();
#endif
    exit(0);
}

int main(void) {
    char portInput[16];
    int serverPort;

    setvbuf(stdout, NULL, _IONBF, 0);

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        exit(1);
    }
#endif

    printf("Enter server port number: ");
    if (fgets(portInput, sizeof(portInput), stdin) == NULL ||
        sscanf(portInput, "%d", &serverPort) != 1) {
        printf("Invalid input. Using default port 12000.\n");
        serverPort = 12000;
    }
    if (serverPort <= 0 || serverPort > 65535) {
        serverPort = 12000;
    }

    sock_t serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocket == SOCK_INVALID) {
        perror("socket");
        exit(1);
    }
    serverSocketGlobal = serverSocket;
    signal(SIGINT, handleSigint);

    int opt = 1;
    setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, (const char *)&opt, sizeof(opt));

    struct sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons((unsigned short)serverPort);

    if (bind(serverSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) < 0) {
        perror("bind");
        exit(1);
    }

    if (listen(serverSocket, 1) < 0) {
        perror("listen");
        exit(1);
    }

    printf("The server is ready to receive\n");

    while (1) {
        struct sockaddr_in clientAddr;
        socklen_t clientLen = sizeof(clientAddr);
        sock_t connectionSocket = accept(serverSocket, (struct sockaddr *)&clientAddr, &clientLen);
        if (connectionSocket == SOCK_INVALID) {
            perror("accept");
            continue;
        }

        char clientIp[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &clientAddr.sin_addr, clientIp, sizeof(clientIp));
        printf("From Client: %s:%d\n", clientIp, ntohs(clientAddr.sin_port));

        char buffer[BUFFER_SIZE];
        int n = recv(connectionSocket, buffer, BUFFER_SIZE - 1, 0);
        if (n < 0) {
            perror("Error receiving data");
            CLOSESOCK(connectionSocket);
            continue;
        }
        buffer[n] = '\0';
        printf("I received: %s\n", buffer);

        for (int i = 0; i < n; i++) {
            buffer[i] = (char)toupper((unsigned char)buffer[i]);
        }

        SLEEP_SEC(3);

        if (send(connectionSocket, buffer, n, 0) < 0) {
            perror("Error sending data");
        }

        CLOSESOCK(connectionSocket);
    }

    return 0;
}
