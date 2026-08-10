/**
 * Tests for the JWT handshake and room naming.
 *
 * Both cases here are real defects that made live chat silently non-functional:
 * the socket rejected every genuine Django token, and booking events were fanned
 * out to a room nobody had joined. Neither showed up as an error — the socket
 * just refused to connect, and pushes went nowhere.
 *
 * Run with `npm test` (builds first, then runs against dist/).
 */
import assert from 'node:assert/strict';
import test from 'node:test';

import jwt from 'jsonwebtoken';

import { verifyToken } from '../dist/auth.js';
import { config } from '../dist/config.js';
import { rooms } from '../dist/redisBridge.js';

const sign = (payload) => jwt.sign(payload, config.jwtSecret, { algorithm: 'HS256' });

test('the default JWT secret matches Django\'s development SECRET_KEY', () => {
  // If these drift apart again, every socket handshake fails as "invalid token".
  assert.equal(config.jwtSecret, 'insecure-development-key-change-in-production');
});

test('accepts a SimpleJWT token whose user_id is a string', () => {
  // SimpleJWT serialises the claim as a string; requiring a number rejected
  // every real token the core-engine issued.
  const user = verifyToken(sign({ token_type: 'access', user_id: '23', role: 'TOURIST' }));
  assert.ok(user, 'expected a string user_id to be accepted');
  assert.equal(user.userId, 23, 'numeric strings should normalise to numbers');
  assert.equal(user.role, 'TOURIST');
});

test('accepts a numeric user_id', () => {
  const user = verifyToken(sign({ token_type: 'access', user_id: 42 }));
  assert.equal(user?.userId, 42);
});

test('keeps a non-numeric user_id as a string', () => {
  const user = verifyToken(sign({ token_type: 'access', user_id: 'a1b2-uuid' }));
  assert.equal(user?.userId, 'a1b2-uuid');
});

test('rejects a token signed with a different secret', () => {
  const forged = jwt.sign({ token_type: 'access', user_id: 1 }, 'not-the-real-secret', {
    algorithm: 'HS256',
  });
  assert.equal(verifyToken(forged), null);
});

test('rejects a token with no user_id', () => {
  assert.equal(verifyToken(sign({ token_type: 'access' })), null);
});

test('rejects a malformed token', () => {
  assert.equal(verifyToken('not-a-jwt'), null);
});

test('booking rooms are keyed by primary key, not booking reference', () => {
  // The Flutter app joins `booking:${booking.id}` and the core-engine parses the
  // room back to an integer pk. Fanning out on the reference put every booking
  // push in an empty room.
  assert.equal(rooms.booking(11), 'booking:11');
  assert.notEqual(rooms.booking(11), 'booking:CE6EDB151434');
});

test('identity rooms are stable across string and number ids', () => {
  assert.equal(rooms.user(23), rooms.user('23'));
});
