<template>
  <div class="demo-background">
    <div class="phone">
      <div class="dynamic-island"></div>

      <iframe
        src="/user"
        class="phone-screen"
        title="Building Service Mobile Demo"
      ></iframe>
    </div>
  </div>
</template>

<style scoped>
.demo-background {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #e9ecef;
  padding: 30px;
}

.phone {
  position: relative;
  width: 390px;
  height: 844px;
  padding: 10px;
  background: #111;
  border-radius: 50px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
}

.phone-screen {
  width: 100%;
  height: 100%;
  border: 0;
  border-radius: 40px;
  background: white;
}

.dynamic-island {
  position: absolute;
  z-index: 10;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);

  width: 100px;
  height: 28px;

  background: #111;
  border-radius: 20px;
}
</style>
