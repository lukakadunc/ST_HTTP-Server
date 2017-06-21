"""An example of a simple HTTP server."""
from __future__ import print_function
import socket
import mimetypes
# Port number
PORT = 8080

# Header template for a successful HTTP request
# Return this header (+ content) when the request can be
# successfully fulfilled
HEADER_RESPONSE_200 = """HTTP/1.1 200 OK
Content-Type: %s
Content-Length: %d

"""

# Template for a 404 (Not found) error: return this when
# the requested resource is not found
RESPONSE_404 = """HTTP/1.1 404 Not found
Content-Type: text/html;charset=utf-8

<!doctype html>
<h1>404 Page not found</h1>
<p>Page cannot be found.</p>
"""

RESPONSE_400 = """HTTP/1.1 400 Not found
content-type: text/html
connection: Close

<!doctype html>
<h1>400 Bad request</h1>
<p>Page cannot be found.</p>
"""

def extract_headers(file_input):
    headers = dict()

    while True:
        line = file_input.readline().strip()
        if(line == ""):
            break
        key, value = line.split(":",1)
        headers[key.strip()] = value.strip()


    return headers

def process_request(connection, address):
    """
    Process an incoming socket request.
    :param connection is a new socket object usable to send and receive data on the connection
    :param address is the address bound to the socket on the other end of the connection
    """
    # Make reading from a socket like reading from a file
    file_input = connection.makefile()

    # Read request line
    try:
        request_line = file_input.readline().strip()
        method, uri, version = request_line.split()
        print("[%s:%d] %s %s %s" %(address[0], address[1], method, uri, version))
    except ValueError as error:
        print("[%s:%d] ERROR cannot parse request line '%s' (%s)" % (address[0], address[1], request_line, error))
        return

    headers = extract_headers(file_input)

    uri = uri[1:]
    try:
        with open(uri, "rb") as handle:
            response_body = handle.read()
        minetype, _ = mimetypes.guess_type(uri)
        response_header = HEADER_RESPONSE_200 % (minetype, len(response_body))
        connection.sendall(response_header.encode("utf-8"))
        connection.sendall(response_body)

    except FileNotFoundError:
        connection.sendall(RESPONSE_404.encode("utf-8"))


    # Create a response: the same text, but in upper case
    #response = line.upper()

    # Write the response to the socket
    #connection.sendall(response.encode("utf-8"))

    # Close the file-like object (reading part)
    file_input.close()

def main():
    """Starts the server and waits for connections."""

    # Create a TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # To prevent "Address already in use" error,
    # set the reuse address socket option
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind on all network addresses (interfaces)
    server.bind(("", PORT))

    # Start listening and allow at most 1 queued connection
    server.listen(1)

    print("Listening on %d" % PORT)

    while True:
        # Accept the connection
        connection, address = server.accept()
        print("[%s:%d] CONNECTED" % address)

        # Process request
        process_request(connection, address)

        # Close the socket
        connection.close()
        print("[%s:%d] DISCONNECTED" % address)

if __name__ == "__main__":
    main()
