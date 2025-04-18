#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define SERVER_IP "127.0.0.1" // Replace with your server's IP
#define SERVER_PORT 5000      // Replace with your Flask server's port

void send_http_post_request(const char *api_key) {
    int sock;
    struct sockaddr_in server_addr;
    char request[1024];
    char response[1024];
    const char *json_data = "{\"service_name\": \"example_function\", \"sub_json\": {\"param1\": \"value1\", \"param2\": \"value2\"}, \"request_type\": \"INLINE\"}";

    // Create a socket
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("Socket creation failed");
        exit(1);
    }

    // Configure server address
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(SERVER_PORT);
    server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);

    // Connect to the server
    if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Connection to server failed");
        close(sock);
        exit(1);
    }

    // Construct HTTP POST request
    snprintf(request, sizeof(request),
             "POST /web_server HTTP/1.1\r\n"
             "Host: %s:%d\r\n"
             "Authorization: %s\r\n"
             "Content-Type: application/json\r\n"
             "Content-Length: %lu\r\n\r\n"
             "%s",
             SERVER_IP, SERVER_PORT, api_key, strlen(json_data), json_data);

    // Send the request
    if (send(sock, request, strlen(request), 0) < 0) {
        perror("Failed to send request");
        close(sock);
        exit(1);
    }

    // Receive the response
    ssize_t bytes_received = recv(sock, response, sizeof(response) - 1, 0);
    if (bytes_received < 0) {
        perror("Failed to receive response");
    } else {
        response[bytes_received] = '\0'; // Null-terminate the response
        printf("Server Response:\n%s\n", response);
    }

    // Close the socket
    close(sock);
}

int main() {
    const char *api_key = "your_api_key"; // Replace with your API key
    send_http_post_request(api_key);
    return 0;
}
