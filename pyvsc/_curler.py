import sys
import json
from requests import Request

if sys.version_info.major >= 3:
    from shlex import quote
else:
    from pipes import quote


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
        parts = [
            ('curl', None),
            ('-X', request.method),
        ]
        
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


    def _get_asset_name_from_url(self, url):
        return url.split('/')[-1]


    def request(self, method, url, **kwargs):
        # Pop specific curl-conversion-related items from the kwargs before 
        # sending them to the Request (since it won't recognize them)
        allow_redirects = kwargs.pop('allow_redirects', True)
        compressed = kwargs.pop('compressed', True)
        output = kwargs.pop('output', None)
        output_dir = kwargs.pop('output_dir', None)
        
        if output_dir and not output:
            output = '%s/%s' % (output_dir, self._get_asset_name_from_url(url))

        # Make the prepared request
        prepared_request = Request(method, url, **kwargs).prepare()

        # Convert the prepared request to its cURL equivalent
        curled_request = self._convert_to_curl_command(
            prepared_request,
            allow_redirects=allow_redirects,
            compressed=compressed,
            output=output)

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
        return self.request(
            'POST', url, data=json.dumps(data), headers=headers, **kwargs)



import os
from pyvsc._tunnel import tunnel

# from pyvsc._editor import Editors
# insiders_url = Editors.insiders.download_url


url = 'https://az764295.vo.msecnd.net/insider/ece7aaee861d7261a728d52ce436c667030ce17d/VSCode-darwin-insider.zip'

curled_request = CurledRequest()
# x = curled_request.get(url, output_dir='/tmp')
# print(x)


url = 'https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery'
data = {'filters': [{'pageNumber': 1, 'pageSize': 1, 'criteria': [{'filterType': 8, 'value': 'Microsoft.VisualStudio.Code'}, {'filterType': 7, 'value': 'twxs.cmake'}]}], 'flags': 17375}
headers = {'Accept': 'application/json;api-version=6.0-preview.1', 'Accept-Encoding': 'gzip', 'Content-Type': 'application/json'}

x = curled_request.post(url, data=data, headers=headers)
# print(x)

# t.run(x)
# res = json.loads(t.run(x, hide=True))

from beeprint import pp

res = tunnel.run(x, hide=True)
print(type(res))
print('stdout: %s' % res.stdout)
print('stderr: %s' % res.stderr)
pp(res)

# pp(res)