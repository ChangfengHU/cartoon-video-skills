import test, {afterEach, beforeEach, describe} from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import worker from '../src/worker.mjs';
import {sha} from '../src/library.mjs';

const AUTHORIZE_URL = 'https://fleet.vyibc.com/api/hub/install-token/authorize';
const MCP_ID = 'vyibc-cartoon-assets';
const ORIGIN = 'https://cartoon-assets-mcp.vyibc.com';
const VAULT = 'vault-secret';
const CURRENT = 'vmat_current_install_token';
const READ_ONLY = 'read-only-secret';
const digest = value => createHash('sha256').update(value).digest('base64url');
const vaultHash = await sha(VAULT);
const readOnlyHash = await sha(READ_ONLY);

function clientRecord(tokenHash, permissions = ['read', 'write'], scope = {}) {
  return {
    token_sha256: tokenHash,
    tenant: scope.tenant ?? 'vyibc',
    brand: scope.brand ?? 'cartoon-xiaban',
    prefix: scope.prefix ?? 'xiaban/v2',
    legacy_prefix: scope.legacy_prefix === undefined ? 'xiaban/v1' : scope.legacy_prefix,
    permissions,
  };
}

function envFor(clients, {guardLibrary = false} = {}) {
  const touches = [];
  const allowed = {AUTH_CLIENTS: JSON.stringify(clients), LIBRARY: {}};
  const env = new Proxy(allowed, {
    get(target, key) {
      if (key === 'AUTH_CLIENTS') return target.AUTH_CLIENTS;
      if (key === 'LIBRARY') {
        if (guardLibrary) {
          touches.push('LIBRARY');
          throw new Error('tool touched env.LIBRARY');
        }
        return target.LIBRARY;
      }
      if (typeof key === 'symbol') return undefined;
      touches.push(String(key));
      throw new Error(`tool touched env.${String(key)}`);
    },
  });
  return {env, touches};
}

function guardedEnv() {
  return envFor([clientRecord(vaultHash)], {guardLibrary: true});
}

function upgradeBody(boundVersion = '0.9.0') {
  const message = boundVersion === null
    ? `能力 ${MCP_ID} 未绑定版本，无法证明自己是当前版本。`
    : `能力 ${MCP_ID} 需要升级：当前安装令牌绑定的是 ${boundVersion}，最新版本是 1.0.0。`;
  return {
    ok: false,
    code: 'capability_version_upgrade_required',
    mcpId: MCP_ID,
    boundVersion,
    latestVersion: '1.0.0',
    pluginId: 'demo-plugin',
    pluginVersion: '2.0.0',
    pluginUrl: 'https://fleet.vyibc.com/#/hub?view=plugins&plugin=demo-plugin',
    message,
  };
}

const fallbackBody = {
  ok: false,
  code: 'capability_version_upgrade_required',
  mcpId: MCP_ID,
  message: '能力 vyibc-cartoon-assets 需要升级：安装令牌无法证明自己是当前版本。',
};

const originalFetch = globalThis.fetch;
const originalTimeout = AbortSignal.timeout;
const originalConsole = {log: console.log, info: console.info, warn: console.warn, error: console.error, debug: console.debug};
let calls;
let logs;
let timeouts;
let hub;

beforeEach(() => {
  calls = [];
  logs = [];
  timeouts = [];
  hub = () => Response.json({ok: false, code: 'install_token_unknown'}, {status: 401});
  globalThis.fetch = async (input, init) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    if (url !== AUTHORIZE_URL) throw new Error(`unexpected fetch ${url}`);
    calls.push({input, init});
    return hub(calls.at(-1));
  };
  AbortSignal.timeout = ms => {
    timeouts.push(ms);
    return originalTimeout(ms);
  };
  for (const method of ['log', 'info', 'warn', 'error', 'debug']) {
    console[method] = (...args) => { logs.push(args.map(item => String(item)).join(' ')); };
  }
});

afterEach(() => {
  globalThis.fetch = originalFetch;
  AbortSignal.timeout = originalTimeout;
  Object.assign(console, originalConsole);
});

function requestRecord(call) {
  const url = typeof call.input === 'string' ? call.input : call.input instanceof URL ? call.input.href : call.input.url;
  return {
    url,
    headers: new Headers(call.init?.headers),
    body: JSON.parse(String(call.init?.body)),
    init: call.init,
  };
}

function post(path, token, body, env = envFor([clientRecord(vaultHash)]).env) {
  const headers = {host: 'cartoon-assets-mcp.vyibc.com', accept: 'application/json, text/event-stream', 'content-type': 'application/json'};
  if (token !== undefined) headers.authorization = `Bearer ${token}`;
  return worker.fetch(new Request(`${ORIGIN}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  }), env);
}

async function readBody(response) {
  const text = await response.text();
  const type = response.headers.get('content-type') || '';
  if (!type.includes('text/event-stream')) return JSON.parse(text);
  const data = text.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).filter(Boolean);
  return JSON.parse(data.at(-1));
}

const initialize = {jsonrpc: '2.0', id: 1, method: 'initialize', params: {protocolVersion: '2025-06-18', capabilities: {}, clientInfo: {name: 'test', version: '0'}}};
const toolCall = (name, arguments_) => ({jsonrpc: '2.0', id: 2, method: 'tools/call', params: {name, arguments: arguments_}});

function assertNoSecret(token) {
  const hash = digest(token);
  const logged = logs.join('\n');
  assert.equal(logged.includes(token), false);
  assert.equal(logged.includes(hash), false);
  assert.deepEqual(timeouts, calls.map(() => 4000));
  for (const call of calls) {
    const recorded = requestRecord(call);
    assert.equal(recorded.url, AUTHORIZE_URL);
    assert.equal(new URL(recorded.url).search, '');
    assert.equal(recorded.url.includes(token), false);
    assert.equal(recorded.url.includes(hash), false);
    assert.equal(recorded.headers.get('authorization'), null);
    assert.equal(recorded.init.method, 'POST');
    assert.equal(recorded.init.redirect, 'manual');
    assert.equal(recorded.init.cache, 'no-store');
    assert.ok(recorded.init.signal instanceof AbortSignal);
    assert.equal(recorded.headers.get('content-type'), 'application/json');
    assert.equal(recorded.init.body, JSON.stringify({mcpId: MCP_ID, tokenHash: hash}));
    assert.equal(JSON.stringify(recorded.body).includes(token), false);
    assert.deepEqual(Object.keys(recorded.body).sort(), ['mcpId', 'tokenHash']);
  }
}

describe('cartoon-assets origin install-token hook', {concurrency: 1}, () => {
  test('accepts a current Hub token without an upgrade reminder', async () => {
    hub = () => Response.json({ok: true, mcpId: MCP_ID, version: '9.9.9'}, {status: 200});
    const response = await post('/mcp', CURRENT, initialize);
    assert.equal(response.status, 200);
    const body = await readBody(response);
    assert.equal(body.result.serverInfo.name, MCP_ID);
    assert.equal(body.message, undefined);
    assert.equal(JSON.stringify(body).includes('需要升级'), false);
    assert.equal(JSON.stringify(body).includes('9.9.9'), false);
    assert.equal(calls.length, 1);
    assert.equal(requestRecord(calls[0]).body.mcpId, MCP_ID);
    assertNoSecret(CURRENT);

    const listed = await post('/mcp', CURRENT, {jsonrpc: '2.0', id: 3, method: 'tools/list'});
    for (const tool of (await readBody(listed)).result.tools) {
      assert.equal(tool.inputSchema.properties?.version, undefined);
      assert.equal((tool.inputSchema.required ?? []).includes('version'), false);
    }

    const info = await post('/mcp', CURRENT, toolCall('library_info', {}));
    assert.equal(info.status, 200);
    const infoBody = await readBody(info);
    const payload = JSON.parse(infoBody.result.content[0].text);
    assert.equal(payload.tenant, 'vyibc');
    assert.equal(payload.brand, 'cartoon-xiaban');
    assert.deepEqual(payload.permissions, ['read', 'write']);
    assert.equal(JSON.stringify(infoBody).includes('9.9.9'), false);
    assert.equal(JSON.stringify(infoBody).includes('需要升级'), false);
  });

  test('a matching read-only credential keeps its own scope when Hub accepts', async () => {
    hub = () => Response.json({ok: true, mcpId: MCP_ID, version: '1.0.0'}, {status: 200});
    const env = envFor([
      clientRecord(readOnlyHash, ['read']),
      clientRecord(vaultHash, ['read', 'write']),
    ]).env;
    const info = await post('/mcp', READ_ONLY, toolCall('library_info', {}), env);
    assert.equal(info.status, 200);
    const payload = JSON.parse((await readBody(info)).result.content[0].text);
    assert.deepEqual(payload.permissions, ['read']);
    assertNoSecret(READ_ONLY);
  });

  test("returns Hub's 409 and does not run the tool, even for the vault secret", async () => {
    const expected = upgradeBody();
    hub = () => Response.json(expected, {status: 409});
    const guard = guardedEnv();
    const marker = 'do-not-forward-marker';
    const response = await post('/mcp', VAULT, toolCall('library_info', {marker, character_id: 'https://example.invalid/private'}), guard.env);
    assert.equal(response.status, 409);
    assert.equal(response.headers.get('cache-control'), 'no-store');
    assert.deepEqual(await response.json(), expected);
    assert.deepEqual(guard.touches, []);
    assert.equal(calls.length, 1);
    const recorded = requestRecord(calls[0]);
    assert.equal(recorded.body.mcpId, MCP_ID);
    assert.equal(JSON.stringify(recorded.body).includes(marker), false);
    assert.equal(JSON.stringify(recorded.body).includes('character_id'), false);
    assert.equal(JSON.stringify(recorded.body).includes('example.invalid'), false);
    assertNoSecret(VAULT);
  });

  test('passes an unbound 409 through with its Chinese message', async () => {
    const expected = upgradeBody(null);
    hub = () => Response.json(expected, {status: 409});
    const response = await post('/mcp', VAULT, toolCall('library_info', {}));
    assert.equal(response.status, 409);
    const body = await response.json();
    assert.equal(body.boundVersion, null);
    assert.equal(body.message, expected.message);
    assert.match(body.message, /未绑定版本/);
    assert.equal(JSON.stringify(body).includes(VAULT), false);
  });

  test('a missing, oversized, or non-JSON 409 still blocks the tool', async () => {
    const guard = guardedEnv();
    const failures = [
      () => new Response('not-json', {status: 409, headers: {'content-type': 'text/plain'}}),
      () => new Response(null, {status: 409}),
      () => Response.json(['not', 'an', 'object'], {status: 409}),
      () => new Response('x', {status: 409, headers: {'content-length': '8193'}}),
      () => new Response(new ReadableStream({start(controller) { controller.enqueue(new Uint8Array(9000)); controller.close(); }}), {status: 409}),
    ];
    for (const failure of failures) {
      calls.length = 0;
      timeouts.length = 0;
      guard.touches.length = 0;
      hub = failure;
      const response = await post('/mcp', VAULT, toolCall('library_info', {marker: VAULT}), guard.env);
      assert.equal(response.status, 409);
      assert.deepEqual(await response.json(), fallbackBody);
      assert.deepEqual(guard.touches, []);
      assert.equal(JSON.stringify(fallbackBody).includes(VAULT), false);
      assertNoSecret(VAULT);
    }
  });

  test('treats install_token_unknown as the existing bearer check', async () => {
    hub = () => Response.json({ok: false, code: 'install_token_unknown', mcpId: MCP_ID}, {status: 401});
    const accepted = await post('/mcp', VAULT, initialize);
    assert.equal(accepted.status, 200);
    assert.equal((await readBody(accepted)).result.serverInfo.name, MCP_ID);
    assert.equal(calls.length, 1);

    calls.length = 0;
    timeouts.length = 0;
    const guard = guardedEnv();
    const rejected = await post('/mcp', 'someone-else', toolCall('library_info', {}), guard.env);
    assert.equal(rejected.status, 401);
    const body = await rejected.json();
    assert.equal(body.error, 'Invalid service credential');
    assert.equal(body.code, undefined);
    assert.deepEqual(guard.touches, []);
    assertNoSecret('someone-else');
  });

  test('an unmatched current token does not cross library scopes', async () => {
    hub = () => Response.json({ok: true, mcpId: MCP_ID, version: '1.0.0'}, {status: 200});
    const guard = envFor([
      clientRecord(vaultHash, ['read', 'write'], {brand: 'cartoon-xiaban', prefix: 'xiaban/v2'}),
      clientRecord(readOnlyHash, ['read'], {brand: 'other-brand', prefix: 'other/v2'}),
    ], {guardLibrary: true});
    const response = await post('/mcp', CURRENT, toolCall('library_info', {}), guard.env);
    assert.equal(response.status, 401);
    assert.equal((await response.json()).error, 'Invalid service credential');
    assert.deepEqual(guard.touches, []);
  });

  test('falls back to the existing check when Hub is unavailable', async () => {
    const failures = [
      () => { throw new TypeError('fetch failed'); },
      () => { throw new DOMException('The operation was aborted due to timeout', 'TimeoutError'); },
      () => Response.json({ok: false}, {status: 404}),
      () => Response.json({ok: false}, {status: 500}),
    ];
    for (const failure of failures) {
      calls.length = 0;
      hub = failure;
      const accepted = await post('/mcp', VAULT, initialize);
      assert.equal(accepted.status, 200);
      const acceptedBody = await readBody(accepted);
      assert.equal(acceptedBody.result.serverInfo.name, MCP_ID);
      assert.equal(acceptedBody.code, undefined);
      assert.equal(calls.length, 1);

      calls.length = 0;
      const guard = guardedEnv();
      const rejected = await post('/mcp', 'someone-else', toolCall('library_info', {}), guard.env);
      assert.equal(rejected.status, 401);
      assert.equal((await rejected.json()).code, undefined);
      assert.deepEqual(guard.touches, []);
    }
  });

  test('one HTTP request is authorised once, including a batch', async () => {
    hub = () => Response.json(upgradeBody(), {status: 409});
    const guard = guardedEnv();
    const marker = 'batch-body-must-stay-here';
    const response = await post('/mcp', VAULT, [
      toolCall('library_info', {marker}),
      toolCall('asset_search', {query: marker}),
    ], guard.env);
    assert.equal(response.status, 409);
    assert.equal(calls.length, 1);
    assert.deepEqual(guard.touches, []);
    assert.equal(JSON.stringify(requestRecord(calls[0]).body).includes(marker), false);
    assertNoSecret(VAULT);
  });

  test('health, anonymous calls, and non-MCP routes do not ask Hub', async () => {
    hub = () => { throw new Error('Hub must not be called'); };
    const health = await worker.fetch(new Request(`${ORIGIN}/health`, {headers: {authorization: `Bearer ${VAULT}`}}));
    assert.equal(health.status, 200);
    assert.equal((await health.json()).service, MCP_ID);

    const anonymous = await post('/mcp', undefined, initialize);
    assert.equal(anonymous.status, 401);
    assert.equal((await anonymous.json()).error, 'Authentication required');

    const wrongScheme = await worker.fetch(new Request(`${ORIGIN}/mcp`, {
      method: 'POST',
      headers: {authorization: `Token ${VAULT}`, 'content-type': 'application/json', accept: 'application/json, text/event-stream'},
      body: JSON.stringify(initialize),
    }), envFor([clientRecord(vaultHash)]).env);
    assert.equal(wrongScheme.status, 401);

    const deniedOrigin = await worker.fetch(new Request(`${ORIGIN}/mcp`, {
      method: 'POST',
      headers: {authorization: `Bearer ${VAULT}`, origin: 'https://evil.example', 'content-type': 'application/json'},
      body: JSON.stringify(initialize),
    }), guardedEnv().env);
    assert.equal(deniedOrigin.status, 403);

    const file = await worker.fetch(new Request(`${ORIGIN}/v1/assets/abc/file`, {headers: {authorization: 'Bearer someone-else'}}), guardedEnv().env);
    assert.equal(file.status, 401);

    const missing = await worker.fetch(new Request(`${ORIGIN}/missing`, {method: 'POST', headers: {authorization: `Bearer ${VAULT}`}}), envFor([clientRecord(vaultHash)]).env);
    assert.equal(missing.status, 404);
    assert.equal((await missing.json()).error, 'Not found');
    assert.equal(calls.length, 0);
    assert.equal(logs.join('\n').includes(VAULT), false);
  });
});
