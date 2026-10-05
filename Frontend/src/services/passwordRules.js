// กฎรหัสผ่านชุดเดียวกับ Backend (app/core/security.py: validate_password_strength)
// หน้าเว็บตรวจเพื่อแสดงผลทันที ส่วน Backend ตรวจซ้ำเพื่อความปลอดภัย
export const PASSWORD_MAX_LENGTH = 128;

export function passwordRequirements(password) {
  return [
    {
      label: "อย่างน้อย 8 ตัวอักษร",
      passed: password.length >= 8 && password.length <= PASSWORD_MAX_LENGTH,
    },
    { label: "มีตัวพิมพ์ใหญ่", passed: /[A-Z]/.test(password) },
    { label: "มีตัวพิมพ์เล็ก", passed: /[a-z]/.test(password) },
    { label: "มีตัวเลข", passed: /\d/.test(password) },
    { label: "มีอักขระพิเศษ", passed: /[^A-Za-z0-9]/.test(password) },
  ];
}

export function isStrongPassword(password) {
  return passwordRequirements(password).every((item) => item.passed);
}
