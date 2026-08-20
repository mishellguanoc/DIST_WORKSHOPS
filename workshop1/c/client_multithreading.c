/* Equivalent of client_multithreading.py: launches several client threads that
   each connect independently, so the server is exercised by concurrent clients.
   Portable: compiles with POSIX sockets (Linux/WSL) or Winsock2 (native Windows/MinGW). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef SOCKET sock_t;
    #define SOCK_INVALID INVALID_SOCKET
    #define CLOSESOCK closesocket
#else
    #include <unistd.h>
    #include <arpa/inet.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <netdb.h>
    typedef int sock_t;
    #define SOCK_INVALID (-1)
    #define CLOSESOCK close
#endif

#define BUFFER_SIZE 1024
#define NUMBER_OF_CLIENTS 3

static char serverName[256];
static int serverPort;

typedef struct {
    int clientId;
    char taskName[64];
    int duration;
} ClientTask;

void *clientTask(void *arg) {
    ClientTask *ct = (ClientTask *)arg;

    sock_t clientSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (clientSocket == SOCK_INVALID) {
        printf("[CLIENT %d] socket() failed\n", ct->clientId);
        free(ct);
        return NULL;
    }

    struct sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons((unsigned short)serverPort);

    struct hostent *host = gethostbyname(serverName);
    if (host == NULL) {
        printf("[CLIENT %d] Connection error: could not resolve host %s\n", ct->clientId, serverName);
        CLOSESOCK(clientSocket);
        free(ct);
        return NULL;
    }
    memcpy(&serverAddr.sin_addr.s_addr, host->h_addr_list[0], (size_t)host->h_length);

    if (connect(clientSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) < 0) {
        printf("[CLIENT %d] Connection error\n", ct->clientId);
        CLOSESOCK(clientSocket);
        free(ct);
        return NULL;
    }

    printf("[CLIENT %d] Connected to server\n", ct->clientId);

    char message[BUFFER_SIZE];
    snprintf(message, sizeof(message), "%s %d", ct->taskName, ct->duration);
    printf("[CLIENT %d] Sending: %s\n", ct->clientId, message);
    send(clientSocket, message, (int)strlen(message), 0);

    char buffer[BUFFER_SIZE];
    int n = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);
    if (n > 0) {
        buffer[n] = '\0';
        printf("[CLIENT %d] Server response: %s\n", ct->clientId, buffer);
    }

    CLOSESOCK(clientSocket);
    printf("[CLIENT %d] Connection closed\n", ct->clientId);

    free(ct);
    return NULL;
}

int main(void) {
    char portInput[16];

    setvbuf(stdout, NULL, _IONBF, 0);

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        exit(1);
    }
#endif

    printf("Enter server hostname or IP address: ");
    fgets(serverName, sizeof(serverName), stdin);
    serverName[strcspn(serverName, "\n")] = '\0';
    if (strlen(serverName) == 0) {
        strcpy(serverName, "localhost");
    }

    printf("Enter server port number: ");
    if (fgets(portInput, sizeof(portInput), stdin) == NULL ||
        sscanf(portInput, "%d", &serverPort) != 1) {
        printf("Invalid input. Using default port 12000.\n");
        serverPort = 12000;
    }
    if (serverPort <= 0 || serverPort > 65535) {
        serverPort = 12000;
    }

    pthread_t threads[NUMBER_OF_CLIENTS];

    for (int i = 0; i < NUMBER_OF_CLIENTS; i++) {
        int clientId = i + 1;
        ClientTask *ct = malloc(sizeof(ClientTask));
        ct->clientId = clientId;
        snprintf(ct->taskName, sizeof(ct->taskName), "Task%d", clientId);
        ct->duration = (clientId * 2) + 1;

        pthread_create(&threads[i], NULL, clientTask, ct);
    }

    for (int i = 0; i < NUMBER_OF_CLIENTS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("\nAll clients have finished.\n");

#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
