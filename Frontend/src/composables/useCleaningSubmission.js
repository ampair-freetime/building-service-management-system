import { ref } from "vue";
import { uploadCleaningRequest } from "../services/cleaningRequests.js";

export function useCleaningSubmission(upload = uploadCleaningRequest) {
  const isSubmitting = ref(false);
  const status = ref("idle");
  const message = ref("");
  let requestId;
  let previousEntries;

  function markChanged() {
    if (isSubmitting.value) return;
    requestId = undefined;
    status.value = "idle";
    message.value = "";
  }

  async function submit(payload, onSuccess, onFailure) {
    if (isSubmitting.value) return;
    isSubmitting.value = true;
    status.value = "uploading";
    message.value = "กำลังส่งคำขอและอัปโหลดรูป กรุณารอสักครู่…";
    try {
      const entries = Array.from(payload.entries());
      const unchanged = previousEntries?.length === entries.length &&
        entries.every(([key, value], index) =>
          key === previousEntries[index][0] && value === previousEntries[index][1]);
      if (!unchanged) requestId = undefined;
      requestId ??= crypto.randomUUID();
      previousEntries = entries;
      const result = await upload(payload, { requestId });
      onSuccess(result);
      status.value = "success";
      message.value = result.demo
        ? "ส่งคำขอทำความสะอาดเรียบร้อยแล้ว"
        : `ส่งคำขอสำเร็จ รหัสติดตาม: ${result.request_code}`;
      requestId = undefined;
    } catch (error) {
      status.value = "error";
      message.value = error.message || "ส่งไม่สำเร็จ กรุณาลองส่งอีกครั้ง";
      onFailure?.(error);
    } finally {
      isSubmitting.value = false;
    }
  }

  return { isSubmitting, status, message, submit, markChanged };
}
