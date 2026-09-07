#!/usr/bin/env python3
"""Scoped asset MCP client / stdio bridge, Python 3.9+. No CF admin credential."""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import urllib.request
import urllib.error
import urllib.parse
import uuid

DEFAULT_ENDPOINT = 'https://cartoon-assets-mcp.2513120790.workers.dev/mcp'
CONFIG = Path.home() / '.config/vyibc-cartoon-assets/credentials.json'
MAX_FILE = 20_000_000

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def safe_new(path, data):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlink output forbidden')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirect refused; credentials stay on the configured origin')

class Client:
    def __init__(self, endpoint=None, token=None):
        if token is None:
            endpoint = os.environ.get('CARTOON_ASSETS_MCP_URL', endpoint)
            token = os.environ.get('CARTOON_ASSETS_TOKEN')
        if token is None:
            if not CONFIG.is_file() or CONFIG.is_symlink():
                raise ValueError('Asset MCP is not configured. Run asset_mcp.py configure or inject CARTOON_ASSETS_TOKEN.')
            mode = CONFIG.stat()
            if stat.S_IMODE(mode.st_mode) & 0o077 or mode.st_uid != os.getuid():
                raise ValueError('Credential file must belong to this user and be mode 0600')
            config = json.loads(CONFIG.read_text())
            endpoint = endpoint or config['endpoint']
            token = config['token']
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        url = urllib.parse.urlsplit(self.endpoint)
        if url.scheme != 'https' or url.username or url.password or url.query or url.fragment or url.path != '/mcp':
            raise ValueError('Use an HTTPS MCP endpoint without credentials/query/fragment')
        if not token or '\n' in token or '\r' in token:
            raise ValueError('Invalid service credential')
        self.origin = f'{url.scheme}://{url.netloc}'
        self.token = token
        self.version = '2025-11-25'
        self.opener = urllib.request.build_opener(NoRedirect)

    def http(self, path, body=None, content_type='application/json'):
        req = urllib.request.Request(self.origin + path, data=body,
            headers={'Authorization':'Bearer ' + self.token, 'Content-Type':content_type,
                     'Accept':'application/json, text/event-stream', 'MCP-Protocol-Version':self.version,
                     'User-Agent':'vyibc-cartoon-assets/1.0 (Python standard-library MCP client)'})
        try:
            with self.opener.open(req, timeout=90) as response:
                raw = response.read(300_000_001)
                if len(raw) > 300_000_000:
                    raise ValueError('Response exceeds client limit')
                return raw, response.headers
        except urllib.error.HTTPError as e:
            raise ValueError(f'Asset service HTTP {e.code}; no success assumed') from None
        except urllib.error.URLError:
            raise ValueError('Asset service network request failed; credentials withheld') from None

    def rpc(self, message):
        raw, headers = self.http('/mcp', json.dumps(message).encode())
        if not raw:
            return None
        if 'text/event-stream' in headers.get('Content-Type', ''):
            payloads = [line[6:] for line in raw.decode().splitlines() if line.startswith('data: ')]
            values = [json.loads(x) for x in payloads]
            reply = next((x for x in values if x.get('id') == message.get('id')), None)
        else:
            reply = json.loads(raw)
        if message.get('method') == 'initialize' and reply and 'result' in reply:
            self.version = reply['result']['protocolVersion']
        return reply

    def call(self, name, arguments):
        reply = self.rpc({'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':name,'arguments':arguments}})
        if not reply or 'error' in reply:
            raise ValueError('MCP protocol error; no success assumed')
        result = reply['result']
        if result.get('isError'):
            raise ValueError('; '.join(c['text'] for c in result.get('content',[]) if c.get('type') == 'text'))
        return json.loads(next(c['text'] for c in result['content'] if c['type'] == 'text'))

    def download(self, ident, output):
        info = self.call('asset_get', {'id':ident})
        obj = info['asset'].get('object')
        if not obj:
            raise ValueError('Metadata-only asset has no archived media')
        raw, _ = self.http('/v1/assets/' + ident + '/file')
        if len(raw) != obj['size'] or hashlib.sha256(raw).hexdigest() != obj['sha256']:
            raise ValueError('Downloaded file failed SHA256/size validation')
        safe_new(output, raw)
        return {'path':str(Path(output).absolute()),'sha256':obj['sha256'],'size':len(raw)}

def configure(endpoint):
    if not sys.stdin.isatty():
        raise ValueError('configure requires a hidden TTY prompt')
    token = getpass.getpass('Scoped asset MCP token (hidden): ')
    client = Client(endpoint, token)
    info = client.call('library_info', {})
    # Validate service before saving, never replace another configured credential.
    safe_new(CONFIG, encode({'endpoint':endpoint,'token':token}))
    CONFIG.parent.chmod(0o700)
    return {'configured':True,'path':str(CONFIG),'scope':info}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('configure'); p.add_argument('--endpoint',default=DEFAULT_ENDPOINT)
    sub.add_parser('stdio')
    p = sub.add_parser('call'); p.add_argument('name'); p.add_argument('--input',type=Path)
    p = sub.add_parser('upload'); p.add_argument('--card',type=Path,required=True); p.add_argument('--file',type=Path,required=True)
    p = sub.add_parser('download'); p.add_argument('--id',required=True); p.add_argument('--output',type=Path,required=True)
    p = sub.add_parser('freeze'); p.add_argument('--selection',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'configure':
        result = configure(args.endpoint)
    elif args.command == 'stdio':
        client = Client()
        for line in sys.stdin:
            if not line.strip(): continue
            message = json.loads(line)
            # Protocol notifications have no response; forward to the stateless server.
            try: reply = client.rpc(message)
            except Exception:
                reply = {'jsonrpc':'2.0','id':message.get('id'),'error':{'code':-32603,'message':'Asset MCP transport failed; check scoped credentials and service availability'}} if 'id' in message else None
            if reply is not None:
                print(json.dumps(reply,ensure_ascii=False),flush=True)
        return
    else:
        client = Client()
        if args.command == 'call':
            result = client.call(args.name,json.loads(args.input.read_text()) if args.input else {})
        elif args.command == 'download':
            result = client.download(args.id,args.output)
        elif args.command == 'upload':
            if not args.file.is_file() or args.file.stat().st_size > MAX_FILE:
                raise ValueError('Upload must be a local media file no larger than 20 MB')
            card = json.loads(args.card.read_text()); data = args.file.read_bytes()
            boundary = 'asset-' + uuid.uuid4().hex
            extension = args.file.suffix.lower()
            if not extension[1:].isalnum(): raise ValueError('Invalid file extension')
            body = (f'--{boundary}\r\nContent-Disposition: form-data; name="card"\r\n\r\n'.encode() + encode(card) +
                f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="media{extension}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + data + f'\r\n--{boundary}--\r\n'.encode())
            raw,_ = client.http('/v1/assets',body,'multipart/form-data; boundary=' + boundary)
            result = json.loads(raw)
            if result['record']['object']['sha256'] != hashlib.sha256(data).hexdigest(): raise ValueError('Upload receipt hash mismatch')
        else:
            output = args.output.absolute()
            if output.exists() or any(p.is_symlink() for p in (output,*output.parents)):
                raise ValueError('Freeze output must be a NEW directory without symlinks')
            frozen = client.call('project_freeze',{'selection':json.loads(args.selection.read_text())})
            output.mkdir(parents=True,exist_ok=False)
            files = []
            for card in frozen['snapshot']['records']:
                obj = card.get('object')
                if obj:
                    if not obj['extension'][1:].isalnum(): raise ValueError('Invalid extension')
                    name = 'assets/' + card['id'] + obj['extension']
                    saved = client.download(card['id'],output/name)
                    files.append({**saved,'path':name})
            safe_new(output/'ASSET_LIBRARY_LOCK.json',encode({**frozen,'files':files}))
            result = {'project_id':frozen['id'],'output':str(output),'verified_files':len(files)}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    try: main()
    except (ValueError, OSError, KeyError) as e:
        print(str(e),file=sys.stderr); sys.exit(1)
