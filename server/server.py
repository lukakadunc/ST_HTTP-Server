"""An example of a simple HTTP server."""
from __future__ import print_function
import mimetypes
import pickle
import socket
from os.path import isdir

try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

# Pickle file for storing data
PICKLE_DB = "db.pkl"

# Directory containing www data
WWW_DATA = "www-data"

# Header template for a successful HTTP request
HEADER_RESPONSE_200 = """HTTP/1.1 200 OK
content-type: %s
content-length: %d
connection: Close

"""

HEADER_RESPONSE_301 = """HTTP/1.1 301 Moved Permanently
Location: %s

"""

# Represents a table row that holds user data
TABLE_ROW = """
<tr>
    <td>%d</td>
    <td>%s</td>
    <td>%s</td>
</tr>
"""

RESPONSE_200 = "200 OK"

RESPONSE_301 = "300 Moved Permanently"

# Template for a 404 (Not found) error
RESPONSE_404 = """HTTP/1.1 404 Not found
content-type: text/html
connection: Close

<!doctype html>
<h1>404 Page not found</h1>
<p>Page cannot be found.</p>
"""

RESPONSE_400 = """HTTP/1.1 400 Bad request
content-type: text/html
connection: Close

<!doctype html>
<h1>400 Bad request</h1>
<p>Your request is bad</p>
"""


def save_to_db(first, last):
    """Create a new user with given first and last name and store it into
    file-based database.

    For instance, save_to_db("Mick", "Jagger"), will create a new user
    "Mick Jagger" and also assign him a unique number.

    Do not modify this method."""

    existing = read_from_db()
    existing.append({
        "number": 1 if len(existing) == 0 else existing[-1]["number"] + 1,
        "first": first,
        "last": last
    })
    with open(PICKLE_DB, "wb") as handle:
        pickle.dump(existing, handle)


def read_from_db(criteria=None):
    """Read entries from the file-based DB subject to provided criteria

    Use this method to get users from the DB. The criteria parameters should
    either be omitted (returns all users) or be a dict that represents a query
    filter. For instance:
    - read_from_db({"number": 1}) will return a list of users with number 1
    - read_from_db({"first": "bob"}) will return a list of users whose first
    name is "bob".

    Do not modify this method."""
    if criteria is None:
        criteria = {}
    else:
        # remove empty criteria values
        for key in ("number", "first", "last"):
            if key in criteria and criteria[key] == "":
                del criteria[key]

        # cast number to int
        if "number" in criteria:
            criteria["number"] = int(criteria["number"])

    try:
        with open(PICKLE_DB, "rb") as handle:
            data = pickle.load(handle)

        filtered = []
        for entry in data:
            predicate = True

            for key, val in criteria.items():
                if val != entry[key]:
                    predicate = False

            if predicate:
                filtered.append(entry)

        return filtered
    except (IOError, EOFError):
        return []


def extract_headers(file_input):
    headers = dict()

    while True:
        line = file_input.readline().strip()
        if (line == ""):
            break
        print("ERROR split line: "+line)
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip().lower()

    return headers






def process_request(connection, address):
    # Make reading from a socket like reading from a file
    file_input = connection.makefile()
    method = ""
    version = ""
    # Read request line
    try:
        request_line = file_input.readline().strip()
        try:
            method, uri, version = request_line.split()
        except ValueError as error:
            connection.sendall(RESPONSE_400.encode("utf-8"))

        if not (method == "GET" or method == "POST"):
            connection.sendall(RESPONSE_400.encode("utf-8"))
            return
        if version != "HTTP/1.1":
            connection.sendall(RESPONSE_400.encode("utf-8"))
            return

        print("[%s:%d] %s %s %s" % (address[0], address[1], method, uri, version))
    except ValueError as error:
        print("[%s:%d] ERROR cannot parse request line '%s' (%s)" % (address[0], address[1], request_line, error))
        return

    headers = extract_headers(file_input)

    if not headers["host"]:
        connection.sendall(RESPONSE_400.encode("utf-8"))
        return

    uri = uri[1:]
    varGet = ""
    varPost = ""
    file = ""
    if method == "GET":
        if "?" in uri:
            temp = uri.split('?')
            file = temp[0]
            varGet = temp[1]
        else:
            file = uri

    print("GET: " + varGet)

    if method == "POST":
        varPost = file_input.read(int(headers["content-length"]))

   # print("POST: "+varPost)

    if file and file == "app-index":
        querr = dict()
        if "&" in varGet:
            temp = varGet.split("&")
        else:
            temp = [varGet]
        for neki in temp:
            if not neki:
                continue
            tmp = neki.split("=")
            querr[unquote_plus(tmp[0])] = unquote_plus(tmp[1])

        zadetki = read_from_db(querr)

        vstavljanje = ""

        for blazeit in zadetki:
            vstavljanje += TABLE_ROW % (int(blazeit["number"]), blazeit["first"], blazeit["last"])


        with open("./www-data/app_list.html", "r") as file:
            response_body = file.read()
        response_body = response_body.replace("{{students}}", vstavljanje)
        minetype, _ = mimetypes.guess_type("user_list.html")
        response_header = HEADER_RESPONSE_200 % (minetype, len(response_body))
        connection.sendall(response_header.encode("utf-8"))
        connection.sendall(response_body.encode("utf-8"))





        return

    if uri == "app-add":
        if "&" in varPost:
            temp = varPost.split("&")
        else:
            temp = [varPost]
        first = ""; last = ""
        for neki in temp:
            if not neki:
                continue
            tmp = neki.split("=")
            if unquote_plus(tmp[0]) == "first":
                first = unquote_plus(tmp[1])
            if unquote_plus(tmp[0]) == "last":
                last = unquote_plus(tmp[1])

        if not first or not last:
            connection.sendall(RESPONSE_400.encode("utf-8"))
            return
        else:
            print("save_to_db" + last, first)
            save_to_db(first, last)
            minetype, _ = mimetypes.guess_type(uri)
            link = "http://" + headers['host'] + "/app_add.html"
            response_header = HEADER_RESPONSE_301 % link
            connection.sendall(response_header.encode("utf-8"))

            return



    # print("URI:-> ", uri)
    # Ce navedemo samo /
    # RESPONSE 301
    if uri.endswith("/") or uri == "":
        link = "http://" + headers['host'] + "/index.html"
        response_header = HEADER_RESPONSE_301 % link
        connection.sendall(response_header.encode("utf-8"))
        return



    try:
        # Odpremo file
        #  RESPONSE 200
        uri = WWW_DATA + "/" + uri


             #POST
        if method == "POST":
            print(headers['content-length'])
            len1 = int(headers['content-length'])
            print(headers)
            with open(uri, "rb") as file:
                response_body = file.read(len1)
            minetype, _ = mimetypes.guess_type(uri)
            response_header = HEADER_RESPONSE_200 % (minetype, len(response_body))
            connection.sendall(response_header.encode("utf-8"))
            connection.sendall(response_body)
            return
        else:
            with open(uri, "rb") as file:
                response_body = file.read()
            minetype, _ = mimetypes.guess_type(uri)
            response_header = HEADER_RESPONSE_200 % (minetype, len(response_body))
            connection.sendall(response_header.encode("utf-8"))
            connection.sendall(response_body)
            return

    #RESPONE 404
    except FileNotFoundError:
        connection.sendall(RESPONSE_404.encode("utf-8"))

    # Create a response: the same text, but in upper case
    # response = line.upper()

    # Write the response to the socket
    # connection.sendall(response.encode("utf-8"))

    # Close the file-like object (reading part)
    file_input.close()


def main(port):
    """Starts the server and waits for connections."""
    # Create a TCP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # To prevent "Address already in use" error,
    # set the reuse address socket option
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind on all network addresses (interfaces)
    server.bind(("", port))
    # Start listening and allow at most 1 queued connection
    server.listen(1)
    print("Listening on %d" % port)
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
    main(8080)