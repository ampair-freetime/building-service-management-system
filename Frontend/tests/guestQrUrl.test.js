import test from "node:test";
import assert from "node:assert/strict";
import { buildGuestQrUrl } from "../src/services/guestQrUrl.js";

test("a cleaning QR opens the guest form with the location token", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/cleaning?old=1", "room 101", "clean"),
    "https://example.com/user?token=room+101&service=clean",
  );
});

test("a repair QR opens the repair form with the same location token", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/app/", "room-101", "repair"),
    "https://example.com/app/user?token=room-101&service=repair",
  );
});

test("a shared QR opens the service chooser", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/user", "room-101"),
    "https://example.com/user?token=room-101",
  );
});

test("an existing cleaning QR URL can provide the token for a repair QR", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/user", "https://example.com/cleaning?token=room-101", "repair"),
    "https://example.com/user?token=room-101&service=repair",
  );
});
