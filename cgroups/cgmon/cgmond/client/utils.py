import jsonrpclib

def servercmd(cmd, *args):
    jsonrpclib.config.version = 1.0
    server = jsonrpclib.Server('http://localhost:8080')

    ret, res = getattr(server, cmd)(*args)
    if not ret:
        raise Exception("ERROR::Server returned: '%s'" % res.replace('\n', '\\n'))

    return res
