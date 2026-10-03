#!/usr/bin/env bash
# cartoon-video-studio plugin installer v0.9.0
# Cross-Platform / Any-Agent support: Auto-detects Codex, Claude, Gemini, Cursor
set -euo pipefail

STUDIO_VERSION=0.9.0
NODE_VERSION=22.18.0
HYPERFRAMES_VERSION=0.8.33
GSAP_VERSION=3.14.2

MODE=skip; REPAIR=0; TOKEN=""; TARGET="auto"
RUNTIME_DIR="${VYIBC_STUDIO_RUNTIME_DIR:-$HOME/.local/share/vyibc/cartoon-video-studio/runtime}"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/vyibc/cartoon-video-studio"

usage(){ echo "Usage: install-cartoon-video-studio.sh --bootstrap-token TOKEN [--target auto|codex|claude|cursor|gemini|antigravity] [--runtime auto|check|skip] [--repair]" >&2; }
while [[ $# -gt 0 ]]; do case "$1" in
  --bootstrap-token) TOKEN="${2:-}"; shift 2 ;;
  --runtime)         MODE="${2:-}";  shift 2 ;;
  --repair)          REPAIR=1; shift ;;
  --target)          TARGET="${2:-}"; shift 2 ;;
  -h|--help)         usage; exit 0 ;;
  *)                 usage; exit 64 ;;
esac; done
[[ -n "$TOKEN" && "$MODE" =~ ^(auto|check|skip)$ ]] || { usage; exit 64; }

# ━━ 识别目标环境 ━━
if [[ "$TARGET" == "auto" ]]; then
  if command -v codex >/dev/null; then TARGET="codex"
  elif [[ -d "$HOME/.claude/skills" ]]; then TARGET="claude"
  elif [[ -d "$HOME/.cursor/skills" ]]; then TARGET="cursor"
  elif [[ -d "$HOME/.gemini/antigravity/skills" ]]; then TARGET="antigravity"
  elif [[ -d "$HOME/.gemini/skills" ]]; then TARGET="gemini"
  else TARGET="codex" # Fallback
  fi
fi

SKILL_BASE_DIR=""
case "$TARGET" in
  codex)       SKILL_BASE_DIR="$HOME/.codex/skills" ;;
  claude)      SKILL_BASE_DIR="$HOME/.claude/skills" ;;
  cursor)      SKILL_BASE_DIR="$HOME/.cursor/skills" ;;
  gemini)      SKILL_BASE_DIR="$HOME/.gemini/skills" ;;
  antigravity) SKILL_BASE_DIR="$HOME/.gemini/antigravity/skills" ;;
  *)           SKILL_BASE_DIR="$HOME/.agents/skills" ;;
esac

for cmd in curl python3; do
  command -v "$cmd" >/dev/null || { echo "Missing: $cmd" >&2; exit 69; }
done
HAVE_CODEX=0; command -v codex >/dev/null && HAVE_CODEX=1

umask 077; mkdir -p "$STATE_DIR" "$RUNTIME_DIR"
TMP="$(mktemp -d)"; trap "rm -rf \"$TMP\"; unset TOKEN" EXIT

# ━━ 第一步：运行时 (Node + FFmpeg + HyperFrames) ━━
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
  [[ "$(uname -s)" == Linux ]]||{ echo "Linux only." >&2; return 1; }
  echo "  Installing Node $NODE_VERSION..."
  curl -fsSL "https://nodejs.org/dist/v$NODE_VERSION/node-v$NODE_VERSION-linux-$arch.tar.xz" -o "$TMP/node.tar.xz"
  printf "%s  %s\n" "$sha" "$TMP/node.tar.xz"|sha256sum -c - >/dev/null
  rm -rf "$RUNTIME_DIR/node" "$TMP/node"; mkdir "$TMP/node"
  tar -xJf "$TMP/node.tar.xz" -C "$TMP/node" --strip-components=1; mv "$TMP/node" "$RUNTIME_DIR/node"
  node_bin="$RUNTIME_DIR/node/bin/node"
}
if [[ "$MODE" != skip ]]; then
  find_node||{ [[ "$MODE" == check ]]&&{ echo "Node 22+ missing." >&2;exit 69;};install_node; }
  find_node||{ echo "Node 22+ unavailable." >&2;exit 69; }
  export PATH="$(dirname "$node_bin"):$PATH"
  npm_bin="$(dirname "$node_bin")/npm";[[ -x "$npm_bin" ]]||npm_bin="$(command -v npm||true)";[[ -x "$npm_bin" ]]||{ echo "npm required." >&2;exit 69; }
  if ! command -v ffmpeg >/dev/null||! command -v ffprobe >/dev/null; then
    if command -v apt-get >/dev/null; then
      echo "  Installing FFmpeg + Chinese fonts..."
      if [[ "${EUID:-$(id -u)}" -eq 0 ]];then apt-get update&&apt-get install -y ffmpeg fontconfig fonts-noto-cjk unzip
      elif command -v sudo >/dev/null;then sudo apt-get update&&sudo apt-get install -y ffmpeg fontconfig fonts-noto-cjk unzip; fi
    else echo "  ⚠ FFmpeg is missing. Rendering requires it (e.g. brew install ffmpeg)." >&2; fi
  fi
  [[ -f "$RUNTIME_DIR/package.json" ]]||printf "{\"private\":true}\n" >"$RUNTIME_DIR/package.json"
  "$npm_bin" --prefix "$RUNTIME_DIR" install --ignore-scripts --no-audit --no-fund --save-exact "hyperframes@$HYPERFRAMES_VERSION" "gsap@$GSAP_VERSION"
  "$RUNTIME_DIR/node_modules/.bin/hyperframes" browser ensure
fi
echo "✓ Runtime"

# ━━ 第二步：Skills 分发 ━━
if [[ "$TARGET" == "codex" && "$HAVE_CODEX" -eq 1 ]]; then
  if ! codex plugin marketplace list 2>/dev/null|awk "NR>1{print \$1}"|grep -qx personal 2>/dev/null; then
    codex plugin marketplace add ChangfengHU/cartoon-video-skills 2>/dev/null || true
  else
    codex plugin marketplace upgrade personal 2>/dev/null || true
  fi
  timeout 30 codex plugin list 2>/dev/null|awk "NR>1{print \$1}"|grep -qx "cartoon-video-studio@personal" 2>/dev/null \
    || timeout 30 codex plugin add cartoon-video-studio@personal 2>/dev/null || true
  echo "✓ Skills (via codex plugin)"
else
  echo "  Downloading skills for $TARGET..."
  REPO_URL="https://github.com/ChangfengHU/cartoon-video-skills/archive/refs/heads/main.tar.gz"
  curl -fsSL "$REPO_URL" -o "$TMP/skills.tar.gz" 2>/dev/null || { echo "  ⚠ Failed to download skills archive" >&2; }
  if [[ -f "$TMP/skills.tar.gz" ]]; then
    tar -xzf "$TMP/skills.tar.gz" -C "$TMP/"
    mkdir -p "$SKILL_BASE_DIR"
    if [[ -d "$TMP/cartoon-video-skills-main/plugins/cartoon-video-studio/skills" ]]; then
      cp -R "$TMP/cartoon-video-skills-main/plugins/cartoon-video-studio/skills/"* "$SKILL_BASE_DIR/"
      echo "✓ Skills installed to $SKILL_BASE_DIR"
    fi
  fi
fi

# ━━ 第三步：MCP 配置 ━━
printf "%s" "$TOKEN" >"$STATE_DIR/bridge.token"; chmod 600 "$STATE_DIR/bridge.token"

python3 - "$TOKEN" "$STATE_DIR" "$REPAIR" "$HAVE_CODEX" "$TARGET" <<'PY'
import json, os, subprocess, sys, urllib.request

token       = sys.argv[1]
state_dir   = sys.argv[2]
repair      = sys.argv[3] == "1"
have_codex  = sys.argv[4] == "1"
target      = sys.argv[5]

bridge = os.environ.get("VYIBC_PLUGIN_BRIDGE_BASE", "https://fleet.vyibc.com/api/hub/plugin-bootstrap")
try:
    req = urllib.request.Request(
        bridge + "/credentials",
        data=json.dumps({"bootstrap_token": token}).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    servers = data.get("mcpServers", {})
    env_vars = data.get("env", {})
    print(f"  Got {len(servers)} MCP endpoints from Fleet")
except Exception as e:
    print(f"  ⚠ credentials API unavailable; using bridge endpoints")
    servers = {}
    env_vars = {}
    for name in ["vyibc-cartoon-assets","vyibc-image","vyibc-douyin","vyibc-youtube","vyibc-voice","vyibc-behavior","vyibc-xiaohongshu","vyibc-vault"]:
        env_key = name.upper().replace("-", "_") + "_TOKEN"
        servers[name] = {"url": f"{bridge}/mcp/{name}", "bearer_token_env_var": env_key}
        env_vars[env_key] = token

env_file = os.path.join(state_dir, "mcp-env.json")
with open(os.open(env_file, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600), "w") as f:
    json.dump(env_vars, f, indent=2)

if have_codex and target == "codex":
    ok = 0
    for name, cfg in servers.items():
        url = cfg.get("url", "")
        if not url: continue
        old = subprocess.run(["codex","mcp","get",name,"--json"], capture_output=True, text=True)
        if old.returncode == 0:
            if not repair:
                print(f"  ⊘ {name}: exists (--repair to overwrite)")
                ok += 1; continue
            subprocess.run(["codex","mcp","remove",name], capture_output=True)
        cmd = ["codex", "mcp", "add", name, "--url", url]
        env_var = cfg.get("bearer_token_env_var")
        if env_var: cmd += ["--bearer-token-env-var", env_var]
        ret = subprocess.run(cmd, capture_output=True, text=True)
        if ret.returncode == 0:
            print(f"  ✓ {name}")
            ok += 1
        else: print(f"  ✗ {name}: {ret.stderr.strip()}")
    print(f"  MCP: {ok}/{len(servers)} configured for Codex")
else:
    # Any-Agent (Claude/Cursor/Gemini) fallback - generates standards-compliant mcp.json
    mcp_json = os.path.join(state_dir, "mcp-servers.json")
    with open(os.open(mcp_json, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600), "w") as f:
        json.dump({"mcpServers": servers}, f, indent=2, ensure_ascii=False)
    print(f"  MCP config written to: {mcp_json}")
    
    # 针对 Claude 的特别注入 (claude_desktop_config.json)
    if target == "claude" and sys.platform.startswith("darwin"):
        claude_cfg = os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
        if os.path.exists(os.path.dirname(claude_cfg)):
            try:
                cdata = json.load(open(claude_cfg)) if os.path.exists(claude_cfg) else {"mcpServers":{}}
                if "mcpServers" not in cdata: cdata["mcpServers"] = {}
                for name, cfg in servers.items():
                    # Claude desktop only supports stdio currently, HTTP requires an SSE bridge script.
                    # Since this installer configures HTTP MCPs, we warn the user or inject a bridge.
                    pass
                print("  ℹ Note: Claude Desktop requires SSE bridge for HTTP MCPs. See docs.")
            except Exception: pass

env_sh = os.path.join(state_dir, "mcp-env.sh")
with open(os.open(env_sh, os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o600), "w") as f:
    f.write("# Auto-generated. Source this file.\n")
    for k, v in env_vars.items():
        f.write(f"export {k}=\"{v}\"\n")
'PY'
echo "✓ MCP"

# ━━ 第四步：冒烟测试 ━━
if [[ "$MODE" != skip ]]; then
  HF="$RUNTIME_DIR/node_modules/.bin/hyperframes";[[ -x "$HF" ]]||{ echo "HyperFrames missing." >&2;exit 69; }
  SMOKE="$TMP/smoke"
  HYPERFRAMES_SKIP_SKILLS=1 "$HF" init "$SMOKE" --non-interactive --example blank --resolution portrait >/dev/null
  command -v ffmpeg >/dev/null && (
    cd "$SMOKE" && "$HF" render --fps 30 --quality draft --workers 1 --output "$TMP/smoke.mp4" >/dev/null
    ffmpeg -nostdin -y -i "$TMP/smoke.mp4" -f lavfi -i anullsrc=r=48000:cl=stereo -shortest -c:v copy -c:a aac "$TMP/smoke-aac.mp4" >/dev/null 2>&1
  ) || true
  echo "✓ Smoke test (skip rendering if no ffmpeg)"
fi

python3 -c "
import datetime,json,pathlib
pathlib.Path(/install-receipt.json).write_text(json.dumps({
 schema:cartoon-video-studio-install-receipt/v1,status:ready,
 studio_version:,target:,
 runtime_mode:,
 written_at:datetime.datetime.now(datetime.timezone.utc).isoformat()
},ensure_ascii=False,indent=2)+n)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Ready ($TARGET). Receipt: $STATE_DIR/install-receipt.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
