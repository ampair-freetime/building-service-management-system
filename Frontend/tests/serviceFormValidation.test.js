import test from 'node:test';
import assert from 'node:assert/strict';
import { serviceFieldError, installServiceFormValidation } from '../src/services/serviceFormValidation.js';

function target(extra = {}) {
  const handlers = new Map();
  return {
    ...extra,
    addEventListener(name, handler) { handlers.set(name, handler); },
    removeEventListener(name) { handlers.delete(name); },
    emit(name, event = {}) { handlers.get(name)?.(event); },
    setAttribute(name, value) { this[name] = value; },
    getAttribute(name) { return this[name]; },
  };
}
function field(id, label, name = id) {
  return target({ id, name, value: '', required: true, type: 'text',
    labels: [{textContent: label}], validity: {typeMismatch: false},
    setCustomValidity(message) { this.customError = message; },
  });
}

test('required fields reject whitespace; email and long descriptions have clear messages', () => {
  const email = field('email', 'อีเมลสำหรับติดตามสถานะ');
  email.value = '  ';
  assert.match(serviceFieldError(email), /กรุณาระบุอีเมล/);
  email.type = 'email'; email.value = 'bad'; email.validity.typeMismatch = true;
  assert.equal(serviceFieldError(email), 'กรุณาระบุอีเมลให้ถูกต้อง');
  const description = field('description', 'รายละเอียด (จำเป็น)', 'description');
  assert.equal(serviceFieldError(description), 'กรุณาระบุรายละเอียด');
  description.value = 'ก'.repeat(2001);
  assert.match(serviceFieldError(description), /2,000/);
  description.value = 'ก'.repeat(2000);
  assert.equal(serviceFieldError(description), '');
});

test('submit displays all inline errors, blocks submission, then accepts corrections and resets', () => {
  const fields = [field('floor', 'ชั้น'), field('room', 'ห้อง'), field('problem', 'ปัญหาที่พบ')];
  const errors = new Map(fields.map(item => [`#${item.id}Error`, target({textContent: ''})]));
  let reports = 0, toasts = 0;
  const form = target({querySelectorAll: () => fields, querySelector: id => errors.get(id),
    checkValidity: () => fields.every(item => !item.customError),
    reportValidity() { reports++; },
  });
  const cleanup = installServiceFormValidation(form, () => toasts++);
  let blocked = false;
  form.emit('submit', {preventDefault() {blocked = true;}, stopImmediatePropagation() {}});
  assert.ok(blocked); assert.equal(reports, 0); assert.equal(toasts, 0);
  for (const item of fields) {
    assert.equal(item['aria-invalid'], 'true');
    assert.ok(errors.get(`#${item.id}Error`).textContent);
    assert.equal(item['aria-describedby'], `${item.id}Error`);
    item.value = 'valid'; item.emit('change');
    assert.equal(item['aria-invalid'], 'false');
    assert.equal(errors.get(`#${item.id}Error`).textContent, '');
  }
  form.emit('submit', {preventDefault() {assert.fail('valid form blocked');}});
  fields[0].value = ''; fields[0].emit('blur');
  form.emit('reset');
  assert.equal(fields[0].customError, '');
  assert.equal(errors.get('#floorError').textContent, '');
  cleanup(); fields[0].emit('input');
  assert.equal(fields[0].customError, '');
});


test('optional descriptions accept empty input but still enforce the length limit', () => {
  for (const id of ['cleanDetails', 'repairDetails']) {
    const description = field(id, 'รายละเอียด (ถ้ามี)', 'description');
    description.required = false;
    for (const value of ['', '   ', 'รายละเอียดเพิ่มเติม']) {
      description.value = value;
      assert.equal(serviceFieldError(description), '');
    }
    description.value = 'ก'.repeat(2001);
    assert.match(serviceFieldError(description), /2,000/);
  }
});
