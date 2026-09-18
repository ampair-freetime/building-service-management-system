import { MAX_DESCRIPTION_LENGTH, descriptionLength } from "./cleaningValidation.js";

export function serviceFieldError(field) {
  const value = field.value.trim();
  const label = field.labels?.[0]?.textContent.replace(/\s*\([^)]*\)/g, "").trim() || "ข้อมูล";
  if (field.required && !value) return `กรุณาระบุ${label}`;
  if (field.type === "email" && value && field.validity.typeMismatch) {
    return "กรุณาระบุอีเมลให้ถูกต้อง";
  }
  const maxLength = field.maxLength > 0 ? field.maxLength : MAX_DESCRIPTION_LENGTH;
  if (field.name === "description" && descriptionLength(field.value) > maxLength) {
    return `รายละเอียดต้องไม่เกิน ${maxLength.toLocaleString("th-TH")} ตัวอักษร กรุณาย่อข้อความ`;
  }
  return "";
}

// Use the same inline errors, aria-invalid and native validity as lost/found forms.
export function installServiceFormValidation(form) {
  const fields = Array.from(form.querySelectorAll("input, select, textarea"))
    .filter(field => field.type !== "file" && field.type !== "hidden");
  const errors = new Map();
  const cleanups = [];
  const listen = (element, event, handler, capture = false) => {
    element.addEventListener(event, handler, capture);
    cleanups.push(() => element.removeEventListener(event, handler, capture));
  };
  for (const field of fields) {
    const id = `${field.id}Error`;
    let error = form.querySelector(`#${id}`);
    if (!error) {
      error = document.createElement("p");
      error.id = id;
      field.closest(".field").append(error);
    }
    error.className = "field-error";
    error.setAttribute("aria-live", "polite");
    errors.set(field, error);
    const describedBy = new Set((field.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
    describedBy.add(id);
    field.setAttribute("aria-describedby", [...describedBy].join(" "));
    const validate = () => validateField(field);
    listen(field, "input", validate);
    listen(field, "change", validate);
    listen(field, "blur", validate);
  }

  function validateField(field) {
    const message = serviceFieldError(field);
    field.setCustomValidity(message);
    field.setAttribute("aria-invalid", String(Boolean(message)));
    errors.get(field).textContent = message;
    return !message;
  }

  // Capture runs before either Vue's submit handler or the demo handler.
  listen(form, "submit", event => {
    const valid = fields.map(validateField).every(Boolean);
    if (!valid || !form.checkValidity()) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);

  listen(form, "reset", () => {
    for (const field of fields) {
      field.setCustomValidity("");
      field.setAttribute("aria-invalid", "false");
      errors.get(field).textContent = "";
    }
  });
  return () => cleanups.forEach(cleanup => cleanup());
}
