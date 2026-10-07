<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";
import lottie from "lottie-web/build/player/lottie_light";
const props = defineProps({ label: { type: String, default: "กำลังโหลดข้อมูล…" } });
const container = ref(null);
let animation;
onMounted(() => {
  animation = lottie.loadAnimation({
    container: container.value,
    renderer: "svg",
    loop: true,
    autoplay: !window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    path: "/animations/moody-dog.json",
  });
});
onBeforeUnmount(() => animation?.destroy());
</script>
<template>
  <div class="dog-loading" role="status" aria-live="polite">
    <div ref="container" class="dog-loading-animation" aria-hidden="true"></div>
    <p>{{ props.label }}</p>
  </div>
</template>
<style scoped>
.dog-loading { display: grid; justify-items: center; gap: 12px; text-align: center; }
.dog-loading-animation { width: min(240px, 60vw); height: min(240px, 60vw); }
.dog-loading p { margin: 0; line-height: 1.6; color: #526175; }
</style>
