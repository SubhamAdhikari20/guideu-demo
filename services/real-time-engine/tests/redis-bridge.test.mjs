import assert from 'node:assert/strict';
import test from 'node:test';

import { dispatchRedisEvent, rooms } from '../dist/redisBridge.js';
import { CHANNELS } from '../dist/types.js';


function recordingIo() {
  const sent = [];
  return {
    sent,
    to(target) {
      return {
        emit(event, payload) {
          sent.push({ target, event, payload });
        },
      };
    },
  };
}


test('user events are delivered only to the administrator role room', () => {
  const io = recordingIo();
  const event = { event: 'user.created', user_id: 42, role: 'GUIDE' };

  dispatchRedisEvent(io, CHANNELS.USER, JSON.stringify(event));

  assert.deepEqual(io.sent, [{ target: rooms.admin, event: 'user:update', payload: event }]);
});


test('malformed Redis events are ignored without emitting', () => {
  const io = recordingIo();

  dispatchRedisEvent(io, CHANNELS.USER, '{not-json');

  assert.deepEqual(io.sent, []);
});
