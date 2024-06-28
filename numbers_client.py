#!/usr/bin/python3
from socket import *
import sys
import struct
import useful_for_protocol

quited = False


def receive_arguments(args):
    """
    Check and parse the arguments to the program
    :param args: the program arguments
    :return: the port and the host for the connection
    """
    if len(args) == 3:
        port = args[2]
        host = args[1]
    elif len(args) == 2:
        port = 1337
        host = args[1]
    elif len(args) == 1:
        port = 1337
        host = "localhost"
    else:
        print("Should get 1 or 2 arguments: users file and port")
        sys.exit(1)
    return port, host


def is_int(checked_int):
    """Check if a string can be converted to int

    :param checked_int: the string to check
    :return: if the string can be converted to int- the integer else False
    """
    try:
        return int(checked_int)
    except (Exception,):
        return False


def calc_op_represent(op):
    """Return the protocol representation of a calculator operation

    :param op: the calculator operation
    :return: the protocol representation
    """
    if op == "+":
        return 0
    if op == "-":
        return 1
    if op == "x":
        return 2
    if op == "/":
        return 3
    else:
        return -1  # the operation is not valid


def all_digits(digits):
    """Check if all the characters in str are digits

    :param digits: the str to check
    :return: if all the characters in str are digits True, else False
    """
    for d in digits:
        if not '0' <= d <= '9':
            return False
    return True


def send_with_err(msg, soc):
    """Send data to the server, considering error (closes soc in case of error)

    :param msg: the msg to be sent to the server- false if there is an error/wants to quit
    :param soc: the socket to send the message on (and close in case of error)
    """
    global quited
    quit_message = struct.pack(">b", 3)
    if not msg:
        useful_for_protocol.send_all(soc, quit_message)
        soc.close()
        quited = True
    else:
        useful_for_protocol.send_all(soc, msg)


"""
HANDLING SENDING REQUESTS OF USER:
"""


def handle_calculate(data):
    """Handle the calculate request from user
    In case of palindrome request, the data to be sent to server is
    1. 0- means calculate request
    2. the operation of the calculation
    3. the first argument of the calculation
    4. the second argument of the calculation

    :param data: the data of the request
    :return: if the data is valid- the data to send to the server, else False
    """
    components = data.split()
    op = calc_op_represent(components[1])
    arg1 = is_int(components[0])
    arg2 = is_int(components[2])
    if arg1 and arg2 and op != -1:
        return struct.pack(">bbii", 0, op, int(arg1), int(arg2))
    else:
        return False


def handle_palindrome(data):
    """Handles the palindrome user's request
    In case of palindrome request, the data to be sent to server is
    1. 1- means palindrome request
    2. the string (of digits) to check if it is a palindrome with null byte at the end

    :param data: the data of the request
    :return: if the data is valid- the data to send to the server, else False
    """
    if all_digits(data):
        return struct.pack(">b", 1)+data.encode()+b'\x00'
    return False


def handle_primary(data):
    """Handles the primary user's request
    In case of primary request, the data to be sent to server is
    1. 2- means primary request
    2. the integer to check primary for

    :param data: the data of the request
    :return: if the data is valid- the data to send to the server, else False
    """
    num = is_int(data)
    if num:
        return struct.pack(">bi", 2, num)
    return False


def log_in(soc):
    """Implements the logging in protocol:
    1. Receiving 1 (means printing a welcome message)
    2. Sending the username and password received from user with null byte at the end of each
    3. Receiving the username that the server logged in which means printing for that user a "good to see you" message

    :param soc: the socket for communication with the server
    """
    if struct.unpack(">b", useful_for_protocol.rcv_all(soc, 1))[0] == 1:
        print("Welcome! Please log in.")
        logged_in = False
        while not logged_in:
            input1 = input()
            input2 = input()
            try:
                username_entry, username = input1.split()
                password_entry, password = input2.split()
                if username_entry == "User:" and password_entry == "Password:":
                    useful_for_protocol.send_all(soc, username.encode()+b"\x00"+password.encode()+b"\x00")
                    if struct.unpack(">b", useful_for_protocol.rcv_all(soc, 1))[0] == 1:
                        username_from_server = useful_for_protocol.rcv_str_till_null(soc)
                        print("Hi "+username_from_server+", good to see you.")
                        logged_in = True
                if not logged_in:
                    print("Failed to login.")
            except (Exception,):
                print("Failed to login.")


def binary_answer(soc):
    """ Read a binary answer (Yes/No) from the server and parse it

    :param soc: the socket for communication with the server
    :return: if server sent 1 "Yes.", else "No."
    """
    response = struct.unpack(">b", useful_for_protocol.rcv_all(soc, 1))[0]
    response_format = "Yes." if response == 1 else "No."
    print("response: " + response_format)


def handle_command(soc, command_input):
    """Handles a users command and communicate with the server by the protocol

    :param soc: the socket for communication with the server
    :param command_input: the command input as received from the user
    """
    try:
        command, data = command_input.split(":")
        if data[0] == " ":
            data = data[1:]  # remove the space in the first char
            if command == "calculate":
                send_with_err(handle_calculate(data), soc)
                # calculate response is an integer with is the result of the calculation
                print("response: "+str(struct.unpack(">i", useful_for_protocol.rcv_all(soc, 4))[0])+".")
            elif command == "is_palindrome":
                send_with_err(handle_palindrome(data), soc)
                binary_answer(soc)
            elif command == "is_primary":
                send_with_err(handle_primary(data), soc)
                binary_answer(soc)
        else:
            send_with_err(False, soc)
    except (Exception, ):
        # quit command also goes here
        send_with_err(False, soc)


def main():
    """
    create socket and connection, log in and loop over receiving commands (until quiting)

    """
    port, host = receive_arguments(sys.argv)
    soc = socket(AF_INET, SOCK_STREAM)
    soc.connect((host, port))
    log_in(soc)
    while not quited:
        handle_command(soc, input())


if __name__ == "__main__":
    main()
