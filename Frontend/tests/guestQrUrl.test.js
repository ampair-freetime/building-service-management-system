import test from "node:test";
import assert from "node:assert/strict";
import { buildGuestQrUrl } from "../src/services/guestQrUrl.js";

test("a location QR opens the guest home page with the location token", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/cleaning?old=1", "room 101"),
    "https://example.com/user?token=room+101",
  );
});

test("a shared QR opens the service chooser", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/user", "room-101"),
    "https://example.com/user?token=room-101",
  );
});

test("an existing service QR URL is normalized to the guest home page", () => {
  assert.equal(
    buildGuestQrUrl("https://example.com/user", "https://example.com/cleaning?token=room-101&service=clean"),
    "https://example.com/user?token=room-101",
  );
});
