import assert from 'node:assert/strict';
import test from 'node:test';

import { authorizeRoom } from '../dist/roomAuthorization.js';

test('room authorization delegates membership to the core engine with the user token', async () => {
  const previousFetch = globalThis.fetch;
  let requested;
  globalThis.fetch = async (url, options) => {
    requested = { url: String(url), options };
    return { ok: true };
  };
  try {
    assert.equal(await authorizeRoom('signed-jwt', 'guide-request:42'), true);
    assert.match(requested.url, /chat\/threads\/authorize\/\?room=guide-request%3A42/);
    assert.equal(requested.options.headers.Authorization, 'Bearer signed-jwt');
  } finally {
    globalThis.fetch = previousFetch;
  }
});

test('room authorization fails closed when the core engine is unavailable', async () => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error('offline'); };
  try {
    assert.equal(await authorizeRoom('signed-jwt', 'booking:1'), false);
  } finally {
    globalThis.fetch = previousFetch;
  }
});
