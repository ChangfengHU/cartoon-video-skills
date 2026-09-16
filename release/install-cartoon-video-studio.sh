#!/usr/bin/env bash
# Reviewed release source. It never prints the bootstrap token or provider keys.
set -euo pipefail
STUDIO_VERSION=0.7.3; NODE_VERSION=22.18.0; HYPERFRAMES_VERSION=0.8.33; GSAP_VERSION=3.14.2; MCP_REMOTE_VERSION=0.14.2
MODE=auto; REPAIR=0; TOKEN=""; RUNTIME_DIR="${VYIBC_STUDIO_RUNTIME_DIR:-$HOME/.local/share/vyibc/cartoon-video-studio/runtime}"; STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/vyibc/cartoon-video-studio"; BRIDGE_BASE="${VYIBC_PLUGIN_BRIDGE_BASE:-https://fleet.vyibc.com/api/hub/plugin-bootstrap/mcp}"
usage(){ echo 'Usage: install-cartoon-video-studio.sh --bootstrap-token TOKEN [--runtime auto|check|skip] [--repair] [--runtime-dir DIR]' >&2; }
while [[ $# -gt 0 ]]; do case "$1" in --bootstrap-token) TOKEN="${2:-}";shift 2;;--runtime) MODE="${2:-}";shift 2;;--repair) REPAIR=1;shift;;--runtime-dir) RUNTIME_DIR="${2:-}";shift 2;;-h|--help) usage;exit 0;;*) usage;exit 64;;esac;done
[[ -n "$TOKEN" && "$MODE" =~ ^(auto|check|skip)$ ]] || { usage; exit 64; }
for cmd in curl python3 codex;do command -v "$cmd" >/dev/null || { echo "Missing bootstrap command: $cmd" >&2;exit 69;};done
umask 077; mkdir -p "$STATE_DIR" "$RUNTIME_DIR"; TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"; unset TOKEN' EXIT
node_bin=""
find_node(){ local p v m;for p in "$RUNTIME_DIR/node/bin/node" "$(command -v node || true)" /usr/bin/node /usr/local/bin/node;do [[ -x "$p" ]]||continue;v="$($p --version 2>/dev/null||true)";m="${v#v}";m="${m%%.*}";[[ "$m" =~ ^[0-9]+$ ]]&&((m>=22))&&{ node_bin="$p";return 0;};done;return 1; }
install_node(){ local arch sha url;case "$(uname -m)" in x86_64)arch=x64;sha=c1bfeecf1d7404fa74728f9db72e697decbd8119ccc6f5a294d795756dfcfca7;;aarch64|arm64)arch=arm64;sha=04fca1b9afecf375f26b41d65d52aa1703a621abea5a8948c7d1e351e85edade;;*)echo "Unsupported architecture: $(uname -m)" >&2;return 1;;esac;[[ "$(uname -s)" == Linux ]]||{ echo 'Automatic runtime bootstrap supports Linux only.' >&2;return 1;};url="https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$arch.tar.xz";curl -fsSL "$url" -o "$TMP/node.tar.xz";printf '%s  %s\n' "$sha" "$TMP/node.tar.xz"|sha256sum -c - >/dev/null;rm -rf "$RUNTIME_DIR/node" "$TMP/node";mkdir "$TMP/node";tar -xJf "$TMP/node.tar.xz" -C "$TMP/node" --strip-components=1;mv "$TMP/node" "$RUNTIME_DIR/node";node_bin="$RUNTIME_DIR/node/bin/node";}
if [[ "$MODE" != skip ]]&&! find_node;then [[ "$MODE" == check ]]&&{ echo 'Node 22+ missing.' >&2;exit 69;};install_node;fi
find_node||{ echo 'Node 22+ unavailable.' >&2;exit 69;};export PATH="$(dirname "$node_bin"):$PATH";npm_bin="$(dirname "$node_bin")/npm";[[ -x "$npm_bin" ]]||npm_bin="$(command -v npm||true)";[[ -x "$npm_bin" ]]||{ echo 'npm paired with Node 22+ is required.' >&2;exit 69;}
if [[ "$MODE" == auto ]];then
 if ! command -v ffmpeg >/dev/null||! command -v ffprobe >/dev/null;then
  if command -v apt-get >/dev/null&&{ [[ "$EUID" -eq 0 ]]||command -v sudo >/dev/null;};then echo 'Installing missing FFmpeg and Chinese fonts…';if [[ "$EUID" -eq 0 ]];then apt-get update&&apt-get install -y ffmpeg fontconfig fonts-noto-cjk unzip;else sudo apt-get update&&sudo apt-get install -y ffmpeg fontconfig fonts-noto-cjk unzip;fi;else echo 'FFmpeg/ffprobe missing; install them with your package manager and retry.' >&2;exit 69;fi
 fi
 [[ -f "$RUNTIME_DIR/package.json" ]]||printf '{"private":true}\n' >"$RUNTIME_DIR/package.json"
 "$npm_bin" --prefix "$RUNTIME_DIR" install --ignore-scripts --no-audit --no-fund --save-exact "hyperframes@$HYPERFRAMES_VERSION" "gsap@$GSAP_VERSION" "mcp-remote@$MCP_REMOTE_VERSION"
 "$RUNTIME_DIR/node_modules/.bin/hyperframes" browser ensure
fi
[[ "$MODE" != check || -x "$RUNTIME_DIR/node_modules/.bin/mcp-remote" ]] || { echo 'Managed runtime is incomplete; rerun with --runtime auto.' >&2;exit 69; }
if ! codex plugin marketplace list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx personal;then
 codex plugin marketplace add ChangfengHU/cartoon-video-skills
else
 codex plugin marketplace upgrade personal
fi
if codex plugin list 2>/dev/null | awk 'NR>1 {print $1}' | grep -qx 'cartoon-video-studio@personal';then
 if [[ "$REPAIR" -eq 1 ]];then codex plugin remove cartoon-video-studio@personal;codex plugin add cartoon-video-studio@personal;fi
else
 codex plugin add cartoon-video-studio@personal
fi
AUTH_FILE="$STATE_DIR/mcp-remote.sh";cat >"$AUTH_FILE" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
state="${XDG_STATE_HOME:-$HOME/.local/state}/vyibc/cartoon-video-studio"
runtime="${VYIBC_STUDIO_RUNTIME_DIR:-$HOME/.local/share/vyibc/cartoon-video-studio/runtime}"
exec "$runtime/node_modules/.bin/mcp-remote" "$@" --header "Authorization: Bearer $(<"$state/bridge.token")"
SH
chmod 700 "$AUTH_FILE";printf %s "$TOKEN" >"$STATE_DIR/bridge.token";chmod 600 "$STATE_DIR/bridge.token"
python3 - "$BRIDGE_BASE" "$TOKEN" "$AUTH_FILE" "$REPAIR" <<'PY'
import json,subprocess,sys,urllib.request
base,token,auth,repair=sys.argv[1].rstrip('/'),sys.argv[2],sys.argv[3],sys.argv[4]=='1'
names=['vyibc-cartoon-assets','vyibc-image','vyibc-douyin','vyibc-youtube','vyibc-voice','vyibc-behavior','vyibc-xiaohongshu','vyibc-vault']
def call(url,i,method,params=None):
 req=urllib.request.Request(url,data=json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params or {}}).encode(),headers={'content-type':'application/json','accept':'application/json, text/event-stream','authorization':'Bearer '+token})
 with urllib.request.urlopen(req,timeout=30) as response: raw=response.read().decode();ctype=response.headers.get('content-type','')
 if 'text/event-stream' not in ctype:return json.loads(raw)
 for event in raw.split('\n\n'):
  for line in event.splitlines():
   if line.startswith('data:') and (packet:=json.loads(line[5:].lstrip())).get('id')==i:return packet
 raise RuntimeError('MCP returned no matching response')
for i,name in enumerate(names,1):
 url=base+'/'+name;init=call(url,i*10,'initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'cartoon-bootstrap','version':'0.7.3'}})
 if 'error' in init:raise SystemExit(name+': initialize failed')
 tools=call(url,i*10+1,'tools/list').get('result',{}).get('tools',[]);old=subprocess.run(['codex','mcp','get',name,'--json'],capture_output=True,text=True)
 if old.returncode==0:
  if not repair:raise SystemExit(name+': existing configuration found; rerun with --repair to rotate this plugin-owned entry')
  subprocess.run(['codex','mcp','remove',name],check=True)
 subprocess.run(['codex','mcp','add',name,'--',auth,url],check=True);print(name+': configured; tools='+str(len(tools)))
PY
if [[ "$MODE" != skip ]];then
 HF="$RUNTIME_DIR/node_modules/.bin/hyperframes";[[ -x "$HF" ]]||{ echo 'HyperFrames runtime missing.' >&2;exit 69;};"$HF" doctor --json >"$TMP/doctor.json"
 SMOKE="$TMP/smoke";HYPERFRAMES_SKIP_SKILLS=1 "$HF" init "$SMOKE" --non-interactive --example blank --resolution portrait >/dev/null;python3 - "$SMOKE/index.html" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]); source=p.read_text(); changed=source.replace('data-duration="10"','data-duration="3"',1); assert changed!=source,'blank smoke template duration changed';p.write_text(changed)
PY
 (cd "$SMOKE"&&HYPERFRAMES_SKIP_SKILLS=1 "$HF" check >/dev/null&&"$HF" render --fps 30 --quality draft --workers 1 --output "$TMP/smoke.mp4" >/dev/null)
 python3 - "$TMP/smoke.mp4" <<'PY'
import json,subprocess,sys
d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,r_frame_rate','-of','json',sys.argv[1]]));v=next((s for s in d['streams'] if s.get('codec_name')=='h264'),None);assert v and v.get('width')==1080 and v.get('height')==1920 and v.get('r_frame_rate')=='30/1',d;assert float(d['format']['duration'])>1,d
PY
fi
python3 - "$STATE_DIR/install-receipt.json" "$STUDIO_VERSION" "$RUNTIME_DIR" "$MODE" <<'PY'
import datetime,json,pathlib,sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({'schema':'cartoon-video-studio-install-receipt/v1','status':'ready','studio_version':sys.argv[2],'runtime_dir':sys.argv[3],'runtime_mode':sys.argv[4],'mcp_servers':8,'local_smoke':'passed' if sys.argv[4]!='skip' else 'skipped','written_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},ensure_ascii=False,indent=2)+'\n')
PY
echo "Ready: plugin MCP bridges and local runtime passed. Receipt: $STATE_DIR/install-receipt.json"
