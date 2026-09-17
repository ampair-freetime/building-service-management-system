export const MAX_DESCRIPTION_LENGTH = 2_000;

// Count Unicode code points consistently with backend string length validation.
export function descriptionLength(value) {
  return Array.from(value).length;
}

export function validateCleaningDescription(value) {
  if (descriptionLength(value) > MAX_DESCRIPTION_LENGTH) {
    return "รายละเอียดต้องไม่เกิน 2,000 ตัวอักษร กรุณาย่อข้อความ";
  }
  return "";
}
