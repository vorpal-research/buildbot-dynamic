import re

from twisted.python.compat import networkString


def twisted_UnauthorizedResource_render(self, request):
    """
    Send www-authenticate headers to the client
    """

    def generateWWWAuthenticate(scheme, challenge):
        l = []
        for k, v in challenge.items():
            if isinstance(v, str):
                l.append(networkString("%s=%s" % (k, quoteString(v))))
            elif isinstance(v, bytes):
                l.append(networkString("%s=%s" % (k, quoteBytes(v))))
            else:
                l.append(networkString("%s=%s" % (k, v)))
        return b" ".join([scheme, b", ".join(l)])

    def quoteString(s):
        return '"%s"' % (s.replace('\\', '\\\\').replace('"', '\\"'),)

    def quoteBytes(s):
        return b'"' + s.replace(b'\\', b'\\\\').replace(b'"', b'\\"') + b'"'

    request.setResponseCode(401)
    for fact in self._credentialFactories:
        challenge = fact.getChallenge(request)
        request.responseHeaders.addRawHeader(
            b'www-authenticate',
            generateWWWAuthenticate(fact.scheme, challenge))
    if request.method == b'HEAD':
        return b''
    return b'Unauthorized'


correct_ident_re = re.compile(r"^[^\d\W][\w-]*$", re.UNICODE)
