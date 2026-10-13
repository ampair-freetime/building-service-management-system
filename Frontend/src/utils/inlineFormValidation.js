function validationMessage(field) {
  if (field.validity.valueMissing) return "กรุณากรอกข้อมูลในช่องนี้";
  if (field.validity.typeMismatch && field.type === "email") {
    return "กรุณากรอกอีเมลให้ถูกต้อง";
  }
  if (field.validity.tooLong) {
    return `กรอกได้ไม่เกิน ${field.maxLength} ตัวอักษร`;
  }
  return field.validationMessage || "กรุณาตรวจสอบข้อมูลในช่องนี้";
}

export function setInlineFieldError(field, message) {
  if (!field) return false;
  const errorId = `${field.id}Error`;
  let error = document.getElementById(errorId);
  if (!error) {
    error = document.createElement("p");
    error.id = errorId;
    error.className = "field-error";
    error.setAttribute("aria-live", "polite");
    field.closest(".field")?.append(error);
  }
  field.setAttribute("aria-invalid", String(Boolean(message)));
  field.setAttribute("aria-describedby", [
    ...(field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean),
    errorId,
  ].filter((id, index, ids) => ids.indexOf(id) === index).join(" "));
  if (error) error.textContent = message;
  return !message;
}

export function validateInlineField(field) {
  if (!field || field.disabled || field.type === "hidden") return true;
  return setInlineFieldError(
    field,
    field.checkValidity() ? "" : validationMessage(field),
  );
}

export function validateInlineForm(form) {
  const fields = [...form.querySelectorAll("input, select, textarea")]
    .filter((field) => !field.disabled && field.type !== "hidden");
  const valid = fields.map(validateInlineField).every(Boolean);
  if (!valid) {
    fields.find((field) => field.getAttribute("aria-invalid") === "true")?.focus();
  }
  return valid;
}
