#!/usr/bin/python3
def send_all(soc, msg):
    """
    Send the message on the socket
    """
    sent = 0
    while sent < len(msg):
        sent += soc.send(msg[sent:])


def rcv_all(soc, msg_len):
    """
    Receive msg_len bytes on soc. Closes soc if the connection is closed
    :return: the accepted message
    """
    received = 0
    msg = b''
    while received < msg_len:
        msg += soc.recv(msg_len-received)
        received += len(msg)
        if msg == b'':
            soc.close()
    return msg


def rcv_str_till_null(soc):
    """
    Receive string bytes on soc until the first null character
    :return: the decoded string
    """
    msg = soc.recv(1)
    if msg == b'':
        soc.close()
    while msg[-1] != 0:
        msg += soc.recv(1)
    return msg[:-1].decode()
