<script setup>
import { nextTick, computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
  id: { type: String, required: true },
  name: { type: String, default: "" },
  label: { type: String, required: true },
  placeholder: { type: String, default: "พิมพ์เพื่อค้นหา" },
  options: { type: Array, default: () => [] },
  required: { type: Boolean, default: false },
  allowCustom: { type: Boolean, default: true },
  modelValue: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);

const root = ref(null);
const input = ref(null);
const query = ref(props.modelValue);
const isOpen = ref(false);
const activeIndex = ref(-1);
let parentForm;

const normalizedQuery = computed(() => query.value.trim().toLocaleLowerCase("th"));
const filteredOptions = computed(() => {
  if (!normalizedQuery.value) return props.options;
  return props.options.filter((option) =>
    String(option).toLocaleLowerCase("th").includes(normalizedQuery.value),
  );
});

function openSuggestions() {
  isOpen.value = true;
  activeIndex.value = filteredOptions.value.length ? 0 : -1;
}

function handleInput(event) {
  query.value = event.target.value;
  emit("update:modelValue", query.value);
  openSuggestions();
}

function selectOption(option) {
  query.value = option;
  emit("update:modelValue", option);
  isOpen.value = false;
  activeIndex.value = -1;
  input.value?.focus();
  // Selecting a suggestion must update form validation just like typing does.
  nextTick(() => input.value?.dispatchEvent(new Event("change", { bubbles: true })));
}

function toggleSuggestions() {
  if (isOpen.value) {
    isOpen.value = false;
    return;
  }
  input.value?.focus();
  openSuggestions();
}

function handleKeydown(event) {
  if (event.key === "Escape") {
    isOpen.value = false;
    return;
  }

  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (!isOpen.value) openSuggestions();
    const count = filteredOptions.value.length;
    if (!count) return;
    const step = event.key === "ArrowDown" ? 1 : -1;
    activeIndex.value = (activeIndex.value + step + count) % count;
    document
      .getElementById(`${props.id}-option-${activeIndex.value}`)
      ?.scrollIntoView({ block: "nearest" });
    return;
  }

  if (event.key === "Enter" && isOpen.value && activeIndex.value >= 0) {
    event.preventDefault();
    selectOption(filteredOptions.value[activeIndex.value]);
  }
}

function handleDocumentPointerDown(event) {
  if (!root.value?.contains(event.target)) isOpen.value = false;
}

function handleFocusOut(event) {
  if (!root.value?.contains(event.relatedTarget)) isOpen.value = false;
}

function handleFormReset() {
  window.setTimeout(() => {
    query.value = "";
    emit("update:modelValue", "");
    isOpen.value = false;
  }, 0);
}

watch(() => props.modelValue, (value) => {
  if (value !== query.value) query.value = value;
});

onMounted(() => {
  document.addEventListener("pointerdown", handleDocumentPointerDown);
  parentForm = root.value?.closest("form");
  parentForm?.addEventListener("reset", handleFormReset);
});

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", handleDocumentPointerDown);
  parentForm?.removeEventListener("reset", handleFormReset);
});
</script>

<template>
  <div ref="root" class="field location-combobox" @focusout="handleFocusOut">
    <label :for="id">{{ label }}</label>
    <div class="location-combobox-control">
      <input
        :id="id"
        ref="input"
        class="location-combobox-input"
        :name="name || undefined"
        type="text"
        :value="query"
        :readonly="!allowCustom"
        :placeholder="placeholder"
        autocomplete="off"
        role="combobox"
        :required="required"
        :aria-expanded="isOpen"
        :aria-controls="`${id}-suggestions`"
        :aria-activedescendant="
          isOpen && activeIndex >= 0 ? `${id}-option-${activeIndex}` : undefined
        "
        @focus="openSuggestions"
        @input="handleInput"
        @keydown="handleKeydown"
      />
      <button
        class="location-combobox-toggle"
        type="button"
        tabindex="-1"
        :aria-label="`เปิดรายการ${label}`"
        @click="toggleSuggestions"
      >
        <svg viewBox="0 0 20 20" aria-hidden="true">
          <path d="m5 7.5 5 5 5-5" />
        </svg>
      </button>
    <div
      v-if="isOpen"
      :id="`${id}-suggestions`"
      class="location-suggestions"
      role="listbox"
    >
      <button
        v-for="(option, index) in filteredOptions"
        :id="`${id}-option-${index}`"
        :key="option"
        type="button"
        class="location-suggestion"
        :class="{ active: index === activeIndex }"
        role="option"
        :aria-selected="query === option"
        @mouseenter="activeIndex = index"
        @mousedown.prevent="selectOption(option)"
      >
        <span>{{ option }}</span>
        <svg v-if="query === option" viewBox="0 0 20 20" aria-hidden="true">
          <path d="m4.5 10 3.2 3.2L15.5 5.5" />
        </svg>
      </button>
      <p v-if="!filteredOptions.length" class="location-suggestions-empty">
        ไม่พบรายการแนะนำ สามารถใช้ข้อความที่พิมพ์ได้
      </p>
    </div>
    </div>
    <p :id="`${id}Error`" class="field-error" aria-live="polite"></p>
  </div>
</template>
