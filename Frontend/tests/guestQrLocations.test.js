import test from "node:test";
import assert from "node:assert/strict";
import {
  listCleaningLocations,
  resolveCleaningLocationByQr,
} from "../src/services/cleaningRequests.js";
import {
  listRepairLocations,
  resolveRepairLocationByQr,
} from "../src/services/repairRequests.js";

const location = { id: 12, floor: "1", area: "ห้อง 101" };

for (const [service, listLocations, resolveLocation] of [
  ["cleaning-requests", listCleaningLocations, resolveCleaningLocationByQr],
  ["repair-requests", listRepairLocations, resolveRepairLocationByQr],
]) {
  test(`${service} loads real locations and resolves a QR token`, async () => {
    const urls = [];
    const fetchImpl = async (url) => {
      urls.push(url);
      return new Response(JSON.stringify(url.endsWith("/locations") ? [location] : location));
    };

    assert.deepEqual(await listLocations({ fetchImpl }), [location]);
    assert.deepEqual(await resolveLocation("room_101", { fetchImpl }), location);
    assert.deepEqual(urls, [
      `http://localhost:8000/api/v1/guest/${service}/locations`,
      `http://localhost:8000/api/v1/guest/${service}/locations/by-qr/room_101`,
    ]);
  });

  test(`${service} lets the guest choose a location when the QR is invalid`, async () => {
    for (const status of [404, 422]) {
      const result = await resolveLocation("invalid", {
        fetchImpl: async () => new Response(null, { status }),
      });
      assert.equal(result, null);
    }
    await assert.rejects(
      resolveLocation("room_101", {
        fetchImpl: async () => new Response(null, { status: 503 }),
      }),
      /QR/,
    );
  });
}
