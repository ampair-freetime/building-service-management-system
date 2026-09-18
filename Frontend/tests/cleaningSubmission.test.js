import test from 'node:test';
import assert from 'node:assert/strict';
import { useCleaningSubmission } from '../src/composables/useCleaningSubmission.js';
import { uploadCleaningRequest } from '../src/services/cleaningRequests.js';

function payload(title = 'spill') {
  const data = new FormData();
  data.append('title', title);
  data.append('description', 'near the lift');
  data.append('priority', 'urgent');
  data.append('reporter_email', 'guest@example.com');
  data.append('location_id', '1');
  return data;
}

test('blocks concurrent submissions and only resets after confirmed success', async () => {
  let resolve;
  let calls = 0;
  let resets = 0;
  const state = useCleaningSubmission(() => {
    calls++;
    return new Promise(done => { resolve = done; });
  });
  const pending = state.submit(payload(), () => resets++);
  assert.equal(state.isSubmitting.value, true);
  assert.equal(state.status.value, 'uploading');
  await state.submit(payload(), () => resets++);
  assert.equal(calls, 1);
  assert.equal(resets, 0);
  resolve({ request_code: 'CL-1' });
  await pending;
  assert.equal(resets, 1);
  assert.equal(state.status.value, 'success');
  assert.equal(state.isSubmitting.value, false);
  assert.match(state.message.value, /CL-1/);
});

test('failure preserves payload and retry uses same key; changed payload uses a new key', async () => {
  const keys = [];
  let resets = 0;
  const state = useCleaningSubmission(async (_, { requestId }) => {
    keys.push(requestId);
    throw new Error('offline');
  });
  const data = payload();
  data.append('image', new File(['photo'], 'photo.png', { type: 'image/png' }));
  await state.submit(data, () => resets++);
  assert.equal(resets, 0);
  assert.equal(data.get('image').name, 'photo.png');
  assert.equal(state.status.value, 'error');
  assert.equal(state.isSubmitting.value, false);
  await state.submit(data, () => resets++);
  assert.equal(keys[0], keys[1]);
  data.set('title', 'different');
  await state.submit(data, () => resets++);
  assert.notEqual(keys[1], keys[2]);
});

test('successful retry resets once and new request gets a new key', async () => {
  const keys = [];
  let resets = 0;
  const state = useCleaningSubmission(async (_, { requestId }) => {
    keys.push(requestId);
    if (keys.length === 1) throw new Error('failed');
    return { request_code: 'CL-2' };
  });
  await state.submit(payload(), () => resets++);
  await state.submit(payload(), () => resets++);
  assert.equal(resets, 1);
  assert.equal(keys[0], keys[1]);
  await state.submit(payload(), () => resets++);
  assert.notEqual(keys[1], keys[2]);
});

test('uses the backend cleaning endpoint by default', async () => {
  let requestedUrl;
  await uploadCleaningRequest(payload(), {
    requestId: 'default-url',
    fetchImpl: async (url) => {
      requestedUrl = url;
      return new Response(JSON.stringify({ request_code: 'CLN-1' }), { status: 201 });
    },
  });
  assert.equal(requestedUrl, 'http://localhost:8000/api/v1/guest/cleaning-requests');
});

test('adapter sends multipart and idempotency key and requires a receipt', async () => {
  const data = payload();
  data.append('image', new File(['photo'], 'floor.png', { type: 'image/png' }));
  const result = await uploadCleaningRequest(data, {
    endpoint: '/test', requestId: 'same-key',
    fetchImpl: async (url, options) => {
      assert.equal(url, '/test');
      assert.equal(options.body, data);
      assert.equal(options.headers['Idempotency-Key'], 'same-key');
      assert.equal(options.headers['Content-Type'], undefined);
      assert.deepEqual([...options.body.keys()], [
        'title', 'description', 'priority', 'reporter_email', 'location_id', 'image',
      ]);
      assert.equal(options.body.getAll('image').length, 1);
      return new Response(JSON.stringify({ request_code: 'CL-3' }), { status: 201 });
    },
  });
  assert.equal(result.request_code, 'CL-3');
  await assert.rejects(uploadCleaningRequest(data, {
    endpoint: '/test', fetchImpl: async () => new Response('<html>fallback</html>'),
  }), /ยังยืนยัน/);
});

test('adapter handles validation errors, network errors and timeout', async () => {
  await assert.rejects(uploadCleaningRequest(payload(), {
    endpoint: '/test', fetchImpl: async () => new Response(JSON.stringify({ detail: [{ msg: 'Invalid photo' }] }), { status: 422 }),
  }), /Invalid photo/);
  await assert.rejects(uploadCleaningRequest(payload(), {
    endpoint: '/test', fetchImpl: async () => { throw new TypeError('offline'); },
  }), /อินเทอร์เน็ต/);
  await assert.rejects(uploadCleaningRequest(payload(), {
    endpoint: '/test', timeoutMs: 5,
    fetchImpl: (_, { signal }) => new Promise((_, reject) => {
      signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
    }),
  }), /นานเกินไป/);
});


test('demo success passes the result to the modal callback without claiming a real receipt', async () => {
  const state = useCleaningSubmission(async () => ({ demo: true }));
  let receipt;
  await state.submit(payload(), result => { receipt = result; });
  assert.deepEqual(receipt, { demo: true });
  assert.equal(state.status.value, 'success');
  assert.equal(state.isSubmitting.value, false);
  assert.equal(state.message.value, 'ส่งคำขอทำความสะอาดเรียบร้อยแล้ว');
  assert.doesNotMatch(state.message.value, /undefined|รหัสติดตาม/);
});
