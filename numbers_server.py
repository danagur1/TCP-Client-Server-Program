#!/usr/bin/python3
import struct
from socket import *
import sys
import select
import useful_for_protocol

connected_sockets = []
logged_in_clients = []
users_dict = {}


def create_users_table(users_file_path):
    """
    Create the users dictionary for looking in time of logging in attempts
    :param users_file_path: the path for the users file which contain all the users and passwords
    """
    with open(users_file_path, "r") as users_file:
        for line in users_file.readlines():
            user = line.split("\t")
            if "\n" == user[1][-1]:
                user[1] = user[1][:-1]
            while user != ['']:
                users_dict[user[0]] = user[1]
                user = users_file.readline().split("\t")


def receive_arguments(args):
    """
    Check and parse the arguments to the program
    :param args: the program arguments
    :return: the port to bind the server's socket
    """
    if len(args) == 3:
        port = sys.argv[2]
    elif len(args) == 2:
        port = 1337
    else:
        print("Should get 1 or 2 arguments: users file and port")
        sys.exit(1)
    create_users_table(args[1])
    return port


def log_in(client_soc):
    """
    Implements the logging in protocol:
    1. Sending 1 (which means printing a welcome message)
    2. Receiving the username and password with null byte at the end of each
    3. Sending the username that the have been received (which means printing for that user a "good to see you" message)

    :param client_soc: the socket of the connection with the client
    """
    username = useful_for_protocol.rcv_str_till_null(client_soc)
    password = useful_for_protocol.rcv_str_till_null(client_soc)
    if username in users_dict and users_dict[username] == password:
        useful_for_protocol.send_all(client_soc, struct.pack(">b", 1))
        useful_for_protocol.send_all(client_soc, username.encode()+b"\x00")
        logged_in_clients.append(client_soc)
    else:
        useful_for_protocol.send_all(client_soc, struct.pack(">b", 0))


def calc_op(op, arg1, arg2):
    """
    Calculate the calculation given by the operation and arguments
    :param op: the operation of the calculation
    :param arg1: the first argument of the calculation
    :param arg2: the second argument of the calculation
    :return: the calculation result
    """
    if op == 0:
        return arg1+arg2
    if op == 1:
        return arg1-arg2
    if op == 2:
        return arg1*arg2
    if op == 3:
        return int(arg1/arg2)


def send_binary_answer(soc, answer):
    """Sending a binary response to client
    If answer is True send 1 else send 0

    :param soc: the socket to send the response on
    :param boolean answer: the binary answer
    """
    if answer:
        useful_for_protocol.send_all(soc, struct.pack(">b", 1))
    else:
        useful_for_protocol.send_all(soc, struct.pack(">b", 0))


def handle_calc(connection_socket):
    """Handle the calculate command from client
    Receive:
    1. the operation of the calculation
    2. the first argument of the calculation
    3. the second argument of the calculation
    Send:
    The integer result of the calculation

    :param connection_socket: the socket of the connection with the client
    """
    op, arg1, arg2 = struct.unpack(">bii", useful_for_protocol.rcv_all(connection_socket, 9))
    useful_for_protocol.send_all(connection_socket, struct.pack(">i", calc_op(op, arg1, arg2)))


def handle_palindrome(connection_socket):
    """Handle the palindrome command from client
    Receive:
    The string (of digits) to check if it is a palindrome with null byte at the end
    Send:
    Binary answer represented by 0 (not a palindrome) or 1 (a palindrome)

    :param connection_socket: the socket of the connection with the client
    """
    palindrome = useful_for_protocol.rcv_str_till_null(connection_socket)
    send_binary_answer(connection_socket, palindrome == palindrome[::-1])


def handle_primary(connection_socket):
    """Handle the primary command from client
    Receive:
    The integer to check primary for
    Send:
    Binary answer represented by 0 (not a primary) or 1 (a primary)

    :param connection_socket: the socket of the connection with the client
    """
    primary = struct.unpack(">i", useful_for_protocol.rcv_all(connection_socket, 4))[0]
    send_binary_answer(connection_socket, not any(primary % i == 0 for i in range(2, primary)))


def handle_client(connection_socket):
    """Handles the client command by the coding: 0=calculation, 1=palindrome, 2=primary, 3=quit

    :param connection_socket: the socket of the connection with the client
    """
    if connection_socket not in logged_in_clients:
        log_in(connection_socket)
    else:
        command_code = struct.unpack(">b", useful_for_protocol.rcv_all(connection_socket, 1))[0]
        if command_code == 0:
            handle_calc(connection_socket)
        if command_code == 1:
            handle_palindrome(connection_socket)
        if command_code == 2:
            handle_primary(connection_socket)
        if command_code == 3:
            connection_socket.close()
            connected_sockets.remove(connection_socket)


def handle_new_client(client_soc):
    """Handles new client, sends 1 (means printing a welcome message).
    Adding the client to the active connections list (which will receive messages later)

    :param client_soc: the socket of the connection with the client
    """
    connected_sockets.append(client_soc)
    useful_for_protocol.send_all(client_soc, struct.pack(">b", 1))


def main():
    port = receive_arguments(sys.argv)
    listen_soc = socket(AF_INET, SOCK_STREAM)
    listen_soc.bind(('', port))
    listen_soc.listen()
    while True:
        readable, _, _ = select.select([listen_soc]+connected_sockets, [], [])
        if listen_soc in readable:  # check for new connections
            client, address = listen_soc.accept()
            handle_new_client(client)
        for readable_socket in readable:
            if readable_socket in connected_sockets:  # handle already accepted connections
                handle_client(readable_socket)


if __name__ == "__main__":
    main()
