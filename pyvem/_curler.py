"""Convert requests.requests to cURL requests"""

import json
from shlex import quote

from requests import Request


class CurledRequest():
    def _convert_to_curl_command(
            self,
            request,
            compressed=True,
            verify=True,
            allow_redirects=True,
            output=None
    ):
        # maintain a list of request parts, which are tuples comprised of the
        # "option identifier" and "value" of a given part of the request.
        parts = [('curl', None), ('-X', request.method)]

        # add all the request headers to the list of request parts.
        for k, v in sorted(request.headers.items()):
            parts += [('-H', '{0}: {1}'.format(k, v))]

        # add all of the elements from the request body to the list of parts.
        if request.body:
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            parts += [('-d', body)]

        # conditionally add additional arguments to the request parts.
        if compressed:
            parts += [('--compressed', None)]

        if not verify:
            parts += [('--insecure', None)]

        if allow_redirects:
            parts += [('-L', None)]

        # Add the url to the request parts
        parts += [(None, request.url)]

        # Add an output location, if specified
        if output:
            parts += [('-o', output)]

        # flatten the parts (of tuples) into a 1d list
        flat_parts = []
        for k, v in parts:
            if k:
                flat_parts.append(quote(k))
            if v:
                flat_parts.append(quote(v))

        # join the flattened parts into a string
        return ' '.join(flat_parts)


    def request(self, method, url, **kwargs):
        # Pop specific curl-conversion-related items from the kwargs before
        # sending them to the Request (since it won't recognize them)
        allow_redirects = kwargs.pop('allow_redirects', True)
        compressed = kwargs.pop('compressed', True)
        output = kwargs.pop('output', None)
        output_dir = kwargs.pop('output_dir', None)

        if output_dir and not output:
            output = f'{output_dir}/{url.split("/")[-1]}'

        # Make the prepared request
        prepared_request = Request(method, url, **kwargs).prepare()

        # Convert the prepared request to its cURL equivalent
        curled_request = self._convert_to_curl_command(
            prepared_request,
            allow_redirects=allow_redirects,
            compressed=compressed,
            output=output
        )

        return curled_request


    def get(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('GET', url, params=params, **kwargs)


    def head(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', False)
        return self.request('HEAD', url, params=params, **kwargs)


    def options(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('HEAD', url, params=params, **kwargs)


    def post(self, url, data={}, headers={}, **kwargs):
        kwargs.setdefault('compressed', True)
        return self.request('POST', url, data=json.dumps(data), headers=headers, **kwargs)
