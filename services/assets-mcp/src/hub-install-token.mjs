// Ask Hub whether a bearer is a current install token for one catalogue id.
// The tool call stays on this worker. Nothing except this POST goes to fleet.vyibc.com.
// Decision logic matches youtube-mcp/src/hub-install-token.js at
// ChangfengHU/cloudflare-youtube-pipeline commit 2b543604ebbd33b8325d0dbc4b45c68f28c1b58d
// (open pull request #2, branch cursor/hub-install-token-origins-3ddf).

export const HUB_INSTALL_AUTHORIZE_URL = 'https://fleet.vyibc.com/api/hub/install-token/authorize';
const HUB_AUTHORIZE_TIMEOUT_MS = 4000;
const MAX_AUTHORIZE_BODY_BYTES = 8192;

function upgradeFallback(mcpId) {
  return {
    ok: false,
    code: 'capability_version_upgrade_required',
    mcpId,
    message: `能力 ${mcpId} 需要升级：安装令牌无法证明自己是当前版本。`,
  };
}

async function cancelBody(response) {
  try { await response.body?.cancel(); } catch { /* The decision does not depend on the unread body. */ }
}

async function readUpgradeBody(response, mcpId) {
  const declared = Number(response.headers.get('content-length'));
  if (Number.isFinite(declared) && declared > MAX_AUTHORIZE_BODY_BYTES) {
    await cancelBody(response);
    return upgradeFallback(mcpId);
  }
  const reader = response.body?.getReader();
  if (!reader) return upgradeFallback(mcpId);
  const parts = [];
  let size = 0;
  try {
    for (;;) {
      const step = await reader.read();
      if (step.done) break;
      const value = step.value;
      if (!value?.byteLength) continue;
      size += value.byteLength;
      if (size > MAX_AUTHORIZE_BODY_BYTES) {
        await reader.cancel();
        return upgradeFallback(mcpId);
      }
      parts.push(value);
    }
  } catch {
    return upgradeFallback(mcpId);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const part of parts) {
    bytes.set(part, offset);
    offset += part.byteLength;
  }
  try {
    const parsed = JSON.parse(new TextDecoder().decode(bytes));
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed;
  } catch { /* A non-JSON 409 still blocks the tool. */ }
  return upgradeFallback(mcpId);
}

async function tokenHash(bearer) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(bearer)));
  let binary = '';
  for (const byte of digest) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

/**
 * @param {string} mcpId Catalogue id for the route being called.
 * @param {string} bearer Raw credential, without a Bearer prefix. Empty skips the network call.
 * @param {typeof fetch} [fetchImpl]
 * @returns {Promise<{ action: 'accept' } | { action: 'local' } | { action: 'upgrade', body: Record<string, unknown> }>}
 */
export async function authorizeHubInstallToken(mcpId, bearer, fetchImpl = globalThis.fetch) {
  if (!bearer) return {action: 'local'};
  try {
    const response = await fetchImpl(HUB_INSTALL_AUTHORIZE_URL, {
      method: 'POST',
      headers: {'content-type': 'application/json'},
      body: JSON.stringify({mcpId, tokenHash: await tokenHash(bearer)}),
      redirect: 'manual',
      cache: 'no-store',
      signal: AbortSignal.timeout(HUB_AUTHORIZE_TIMEOUT_MS),
    });
    if (response.status === 200) {
      await cancelBody(response);
      return {action: 'accept'};
    }
    if (response.status === 409) {
      return {action: 'upgrade', body: await readUpgradeBody(response, mcpId)};
    }
    await cancelBody(response);
    return {action: 'local'};
  } catch {
    return {action: 'local'};
  }
}
