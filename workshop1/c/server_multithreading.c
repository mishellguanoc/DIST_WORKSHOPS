/* Equivalent of server_multithreading.py: handles "TaskName seconds" requests,
   one pthread per client, so multiple clients are served concurrently.
   Portable: compiles with POSIX sockets (Linux/WSL) or Winsock2 (native Windows/MinGW). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <pthread.h>

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

typedef struct {
    sock_t connectionSocket;
    struct sockaddr_in addr;
} ClientArgs;

void *handleClient(void *arg) {
    ClientArgs *clientArgs = (ClientArgs *)arg;
    sock_t connectionSocket = clientArgs->connectionSocket;

    char clientIp[INET_ADDRSTRLEN];
    inet_ntop(AF_INET, &clientArgs->addr.sin_addr, clientIp, sizeof(clientIp));
    int clientPort = ntohs(clientArgs->addr.sin_port);

    printf("[START] Client %s:%d connected\n", clientIp, clientPort);

    char buffer[BUFFER_SIZE];
    int n = recv(connectionSocket, buffer, BUFFER_SIZE - 1, 0);
    if (n <= 0) {
        printf("[ERROR] Client %s:%d: recv failed\n", clientIp, clientPort);
        CLOSESOCK(connectionSocket);
        free(clientArgs);
        return NULL;
    }
    buffer[n] = '\0';

    char task[BUFFER_SIZE];
    int seconds = 0;
    if (sscanf(buffer, "%s %d", task, &seconds) != 2) {
        printf("[ERROR] Client %s:%d: malformed message '%s'\n", clientIp, clientPort, buffer);
        CLOSESOCK(connectionSocket);
        free(clientArgs);
        return NULL;
    }

    printf("[TASK] Client %s:%d: %s - %d seconds\n", clientIp, clientPort, task, seconds);

    for (int i = 0; i < seconds; i++) {
        printf("[WORK] Client %s:%d: %s - %d/%d\n", clientIp, clientPort, task, i + 1, seconds);
        SLEEP_SEC(1);
    }

    char response[BUFFER_SIZE];
    snprintf(response, sizeof(response), "%s completed by server", task);
    send(connectionSocket, response, (int)strlen(response), 0);

    printf("[END] Client %s:%d: %s completed\n", clientIp, clientPort, task);

    CLOSESOCK(connectionSocket);
    free(clientArgs);
    return NULL;
}

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

    if (listen(serverSocket, 5) < 0) {
        perror("listen");
        exit(1);
    }

    printf("Server is ready on port %d\n", serverPort);

    while (1) {
        ClientArgs *clientArgs = malloc(sizeof(ClientArgs));
        socklen_t addrLen = sizeof(clientArgs->addr);
        clientArgs->connectionSocket = accept(serverSocket, (struct sockaddr *)&clientArgs->addr, &addrLen);
        if (clientArgs->connectionSocket == SOCK_INVALID) {
            perror("accept");
            free(clientArgs);
            continue;
        }

        pthread_t tid;
        pthread_create(&tid, NULL, handleClient, clientArgs);
        pthread_detach(tid);
    }

    return 0;
}
