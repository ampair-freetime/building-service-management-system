import test from 'node:test';
import assert from 'node:assert/strict';
import { descriptionLength, validateCleaningDescription } from '../src/services/cleaningValidation.js';

test('allows omitted descriptions, including whitespace-only input', () => {
  for (const value of ['', '   ', '\n\t', '\u00a0']) {
    assert.equal(validateCleaningDescription(value), "");
  }
});

test('accepts Thai multiline descriptions and the exact length boundary', () => {
  assert.equal(validateCleaningDescription('พื้นเปียก\nหน้าห้องเรียน'), '');
  assert.equal(validateCleaningDescription('ก'.repeat(2000)), '');
  assert.match(validateCleaningDescription('ก'.repeat(2001)), /2,000/);
});

test('counts emoji consistently and clears errors after corrections', () => {
  assert.equal(descriptionLength('🧹'), 1);
  assert.equal(validateCleaningDescription('🧹'.repeat(2000)), '');
  assert.match(validateCleaningDescription('🧹'.repeat(2001)), /2,000/);
  assert.equal(validateCleaningDescription('กรุณาเช็ดพื้น'), '');
});
