/* Equivalent of client-random-msgs.py: sends a random number (1-10) of randomly
   generated lowercase messages (5-15 chars each) over one connection, then closes it.
   Portable: compiles with POSIX sockets (Linux/WSL) or Winsock2 (native Windows/MinGW). */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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

void generateRandomMessage(char *out) {
    int length = 5 + rand() % 11; /* 5..15 */
    for (int i = 0; i < length; i++) {
        out[i] = (char)('a' + rand() % 26);
    }
    out[length] = '\0';
}

int main(void) {
    char serverName[256];
    char portInput[16];
    int serverPort;

    setvbuf(stdout, NULL, _IONBF, 0);
    srand((unsigned int)time(NULL));

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

    int numMessages = 1 + rand() % 10; /* 1..10 */
    printf("%d messages would be sent to the server\n", numMessages);

    sock_t clientSocket = socket(AF_INET, SOCK_STREAM, 0);
    if (clientSocket == SOCK_INVALID) {
        perror("socket");
        exit(1);
    }

    struct sockaddr_in serverAddr;
    memset(&serverAddr, 0, sizeof(serverAddr));
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons((unsigned short)serverPort);

    struct hostent *host = gethostbyname(serverName);
    if (host == NULL) {
        fprintf(stderr, "Connection error: could not resolve host %s\n", serverName);
        CLOSESOCK(clientSocket);
        exit(1);
    }
    memcpy(&serverAddr.sin_addr.s_addr, host->h_addr_list[0], (size_t)host->h_length);

    if (connect(clientSocket, (struct sockaddr *)&serverAddr, sizeof(serverAddr)) < 0) {
        perror("Connection error");
        CLOSESOCK(clientSocket);
        exit(1);
    }

    for (int i = 0; i < numMessages; i++) {
        char sentence[32];
        generateRandomMessage(sentence);
        printf("Mensaje %d: %s\n", i + 1, sentence);

        send(clientSocket, sentence, (int)strlen(sentence), 0);

        char buffer[BUFFER_SIZE];
        int n = recv(clientSocket, buffer, BUFFER_SIZE - 1, 0);
        if (n < 0) {
            perror("recv");
            break;
        }
        buffer[n] = '\0';
        printf("From Server: %s\n", buffer);
    }

    CLOSESOCK(clientSocket);
    printf("Comunicacion terminada.\n");

#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
