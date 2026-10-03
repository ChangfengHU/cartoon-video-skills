#!/usr/bin/env bash
# cartoon-video-studio plugin installer v0.8.0
# One command: skills + runtime + MCP config, all wired.
set -euo pipefail

STUDIO_VERSION=0.8.0
NODE_VERSION=22.18.0
HYPERFRAMES_VERSION=0.8.33
GSAP_VERSION=3.14.2

MODE=skip; REPAIR=0; TOKEN=""
RUNTIME_DIR="${VYIBC_STUDIO_RUNTIME_DIR:-$HOME/.local/share/vyibc/cartoon-video-studio/runtime}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/vyibc/cartoon-video-studio"

usage(){ echo 'Usage: install-cartoon-video-studio.sh --bootstrap-token TOKEN [--runtime auto|check|skip] [--repair]' >&2; }
while [[ $# -gt 0 ]]; do case "$1" in
  --bootstrap-token) TOKEN="${2:-}"; shift 2 ;;
  --runtime)         MODE="${2:-}";  shift 2 ;;
  --repair)          REPAIR=1; shift ;;
  -h|--help)         usage; exit 0 ;;
  *)                 usage; exit 64 ;;
esac; done
[[ -n "$TOKEN" && "$MODE" =~ ^(auto|check|skip)$ ]] || { usage; exit 64; }

for cmd in curl python3; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 69; }
done
HAVE_CODEX=0; command -v codex >/dev/null && HAVE_CODEX=1

umask 077; mkdir -p "$STATE_DIR" "$RUNTIME_DIR"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"; unset TOKEN' EXIT

# ━━ 第一步：运行时 (Node + FFmpeg + HyperFrames) ━━━━━━━━━━━━━━━━━━━━━━━━━━
node_bin=""
find_node(){
  local p v m
  for p in "$RUNTIME_DIR/node/bin/node" "$(command -v node||true)" /usr/bin/node /usr/local/bin/node; do
    [[ -x "$p" ]]||continue; v="$("$p" --version 2>/dev/null||true)"; m="${v#v}"; m="${m%%.*}"
    [[ "$m" =~ ^[0-9]+$ ]] && ((m>=22)) && { node_bin="$p"; return 0; }
  done; return 1
}
install_node(){
  local arch sha
  case "$(uname -m)" in x86_64)arch=x64;sha=c1bfeecf1d7404fa74728f9db72e697decbd8119ccc6f5a294d795756dfcfca7;;aarch64|arm64)arch=arm64;sha=04fca1b9afecf375f26b41d65d52aa1703a621abea5a8948c7d1e351e85edade;;*)echo "Unsupported arch" >&2;return 1;;esac
  [[ "$(uname -s)" == Linux ]]||{ echo 'Linux only.' >&2; return 1; }
  echo "  Installing Node $NODE_VERSION..."
  curl -fsSL "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$arch.tar.xz" -o "$TMP/node.tar.xz"
  printf '%s  %s\n' "$sha" "$TMP/node.tar.xz"|sha256sum -c - >/dev/null
  rm -rf "$RUNTIME_DIR/node" "$TMP/node"; mkdir "$TMP/node"
  tar -xJf "$TMP/node.tar.xz" -C "$TMP/node" --strip-components=1; mv "$TMP/node" "$RUNTIME_DIR/node"
  node_bin="$RUNTIME_DIR/node/bin/node"
}
if [[ "$MODE" != skip ]]; then
  find_node||{ [[ "$MODE" == check ]]&&{ echo 'Node 22+ missing.' >&2;exit 69;};install_node; }
  find_node||{ echo 'Node 22+ unavailable.' >&2;exit 69; }
  export PATH="$(dirname "$node_bin"):$PATH"
  npm_bin="$(dirname "$node_bin")/npm";[[ -x "$npm_bin" ]]||npm_bin="$(command -v npm||true)";[[ -x "$npm_bin" ]]||{ echo 'npm required.' >&2;exit 69; }
  if ! command -v ffmpeg >/dev/null||! command -v ffprobe >/dev/null; then
    if command -v apt-get >/dev/null; then
      echo '  Installing FFmpeg + Chinese fonts...'
      if [[ "${EUID:-$(id -u)}" -eq 0 ]];then apt-get update&&apt-get install -y ffmpeg fontconfig fonts-noto-cjk unzip
      elif command -v sudo >/dev/null;then sudo apt-get update&&sudo apt-get install -y ffmpeg fontconfig fonts-noto-cjk unzip; fi
    else echo '  ⚠ FFmpeg is missing. Rendering requires it (e.g. brew install ffmpeg).' >&2; fi
  fi
  [[ -f "$RUNTIME_DIR/package.json" ]]||printf '{"private":true}\n' >"$RUNTIME_DIR/package.json"
  "$npm_bin" --prefix "$RUNTIME_DIR" install --ignore-scripts --no-audit --no-fund --save-exact "hyperframes@$HYPERFRAMES_VERSION" "gsap@$GSAP_VERSION"
  "$RUNTIME_DIR/node_modules/.bin/hyperframes" browser ensure
fi
echo "✓ Runtime"

# ━━ 第二步：Skills ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$HAVE_CODEX" -eq 1 ]]; then
  # codex marketplace — 失败不致命
  if ! codex plugin marketplace list 2>/dev/null|awk 'NR>1{print $1}'|grep -qx personal 2>/dev/null; then
    codex plugin marketplace add ChangfengHU/cartoon-video-skills 2>/dev/null || true
  else
    codex plugin marketplace upgrade personal 2>/dev/null || true
  fi
  timeout 30 codex plugin list 2>/dev/null|awk 'NR>1{print $1}'|grep -qx 'cartoon-video-studio@personal' 2>/dev/null \
    || timeout 30 codex plugin add cartoon-video-studio@personal 2>/dev/null || true
  echo "✓ Skills"
else
  echo "⚠ codex not found; install skills separately"
fi

# ━━ 第三步：MCP 配置（直接写 config，不启动进程）━━━━━━━━━━━━━━━━━━━━━━━━━━
printf '%s' "$TOKEN" >"$STATE_DIR/bridge.token"; chmod 600 "$STATE_DIR/bridge.token"

python3 - "$TOKEN" "$STATE_DIR" "$REPAIR" "$HAVE_CODEX" <<'PY'
import json, os, subprocess, sys, urllib.request

token       = sys.argv[1]
state_dir   = sys.argv[2]
repair      = sys.argv[3] == '1'
have_codex  = sys.argv[4] == '1'

# 向 Fleet 换取 MCP 端点和凭据
bridge = os.environ.get('VYIBC_PLUGIN_BRIDGE_BASE',
    'https://fleet.vyibc.com/api/hub/plugin-bootstrap')
try:
    req = urllib.request.Request(
        bridge + '/credentials',
        data=json.dumps({'bootstrap_token': token}).encode(),
        headers={'Content-Type': 'application/json',
                 'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    servers = data.get('mcpServers', {})
    env_vars = data.get('env', {})
    print(f'  Got {len(servers)} MCP endpoints from Fleet')
except Exception as e:
    print(f'  ⚠ credentials API unavailable ({e}); using bridge endpoints')
    servers = {}
    env_vars = {}
    # Fallback: 构造 bridge 端点
    for name in ['vyibc-cartoon-assets','vyibc-image','vyibc-douyin',
                 'vyibc-youtube','vyibc-voice','vyibc-behavior',
                 'vyibc-xiaohongshu','vyibc-vault']:
        env_key = name.upper().replace('-', '_') + '_TOKEN'
        servers[name] = {'url': f'{bridge}/mcp/{name}', 'bearer_token_env_var': env_key}
        env_vars[env_key] = token

# 保存环境变量到 state_dir（token 等敏感值）
env_file = os.path.join(state_dir, 'mcp-env.json')
with open(os.open(env_file, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600), 'w') as f:
    json.dump(env_vars, f, indent=2)

if not have_codex:
    # 没有 codex：写独立 JSON 配置供其他 Agent 平台使用
    mcp_json = os.path.join(state_dir, 'mcp-servers.json')
    with open(os.open(mcp_json, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600), 'w') as f:
        json.dump({'mcpServers': servers}, f, indent=2, ensure_ascii=False)
    print(f'  MCP config: {mcp_json}')
else:
    # 有 codex：用 codex mcp add --url 注册（简单命令，不启动进程）
    ok = 0
    for name, cfg in servers.items():
        url = cfg.get('url', '')
        if not url:
            continue
        # 检查已存在
        old = subprocess.run(['codex','mcp','get',name,'--json'],
                             capture_output=True, text=True)
        if old.returncode == 0:
            if not repair:
                print(f'  ⊘ {name}: exists (--repair to overwrite)')
                ok += 1; continue
            subprocess.run(['codex','mcp','remove',name], capture_output=True)

        # 构造 codex mcp add 命令
        cmd = ['codex', 'mcp', 'add', name, '--url', url]
        env_var = cfg.get('bearer_token_env_var')
        if env_var:
            cmd += ['--bearer-token-env-var', env_var]

        ret = subprocess.run(cmd, capture_output=True, text=True)
        if ret.returncode == 0:
            print(f'  ✓ {name}')
            ok += 1
        else:
            print(f'  ✗ {name}: {ret.stderr.strip()}')

    print(f'  MCP: {ok}/{len(servers)} configured')

# 把 env_vars 写入 shell profile 片段，方便 agent 加载
env_sh = os.path.join(state_dir, 'mcp-env.sh')
with open(os.open(env_sh, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600), 'w') as f:
    f.write('# Auto-generated by cartoon-video-studio installer. Source this file.\n')
    for k, v in env_vars.items():
        f.write(f'export {k}="{v}"\n')
PY
echo "✓ MCP"

# ━━ 第四步：冒烟测试 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if [[ "$MODE" != skip ]]; then
  HF="$RUNTIME_DIR/node_modules/.bin/hyperframes";[[ -x "$HF" ]]||{ echo 'HyperFrames missing.' >&2;exit 69; }
  SMOKE="$TMP/smoke"
  HYPERFRAMES_SKIP_SKILLS=1 "$HF" init "$SMOKE" --non-interactive --example blank --resolution portrait >/dev/null
  python3 -c "import pathlib;p=pathlib.Path('$SMOKE/index.html');s=p.read_text();p.write_text(s.replace('data-duration=\"10\"','data-duration=\"3\"',1))"
  (cd "$SMOKE" && HYPERFRAMES_SKIP_SKILLS=1 "$HF" check >/dev/null && "$HF" render --fps 30 --quality draft --workers 1 --output "$TMP/smoke.mp4" >/dev/null)
  command -v ffmpeg >/dev/null && ffmpeg -nostdin -y -i "$TMP/smoke.mp4" -f lavfi -i anullsrc=r=48000:cl=stereo -shortest -c:v copy -c:a aac "$TMP/smoke-aac.mp4" >/dev/null 2>&1
  python3 -c "
import json,subprocess
d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name,width,height,r_frame_rate','-of','json','$TMP/smoke-aac.mp4']))
v=next((s for s in d['streams'] if s.get('codec_name')=='h264'),None)
a=next((s for s in d['streams'] if s.get('codec_name')=='aac'),None)
assert v and a and v.get('width')==1080 and v.get('height')==1920,d
assert float(d['format']['duration'])>1,d"
  echo "✓ Smoke test"
fi

# ━━ 安装回执 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
python3 -c "
import datetime,json,pathlib
pathlib.Path('$STATE_DIR/install-receipt.json').write_text(json.dumps({
 'schema':'cartoon-video-studio-install-receipt/v1','status':'ready',
 'studio_version':'$STUDIO_VERSION','runtime_dir':'$RUNTIME_DIR',
 'runtime_mode':'$MODE','mcp_transport':'http-direct',
 'written_at':datetime.datetime.now(datetime.timezone.utc).isoformat()
},ensure_ascii=False,indent=2)+'\n')"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Ready. Receipt: $STATE_DIR/install-receipt.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
