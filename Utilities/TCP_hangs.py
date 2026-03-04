import socket
# Force IPv4 only to prevent TCP handshake hangs
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(*args, **kwargs):
    responses = orig_getaddrinfo(*args, **kwargs)
    return [r for r in responses if r[0] == socket.AF_INET]
socket.getaddrinfo = getaddrinfo_ipv4_only
