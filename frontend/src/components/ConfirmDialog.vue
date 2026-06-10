<template>
  <div v-if="visible" class="confirm-overlay" @click.self="handleCancel">
    <div class="confirm-dialog">
      <div class="confirm-icon" :class="type">
        <svg v-if="type === 'danger'" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      </div>
      <h3>{{ title }}</h3>
      <p v-if="message">{{ message }}</p>
      <div class="confirm-actions">
        <button class="btn-secondary" @click="handleCancel">取消</button>
        <button class="btn-danger" @click="handleConfirm">{{ confirmText }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const visible = ref(false)
const title = ref('')
const message = ref('')
const confirmText = ref('确定')
const type = ref<'danger' | 'warning'>('danger')
let resolvePromise: ((value: boolean) => void) | null = null

const show = (options: {
  title: string
  message?: string
  confirmText?: string
  type?: 'danger' | 'warning'
}) => {
  title.value = options.title
  message.value = options.message || ''
  confirmText.value = options.confirmText || '确定'
  type.value = options.type || 'danger'
  visible.value = true

  return new Promise<boolean>((resolve) => {
    resolvePromise = resolve
  })
}

const handleConfirm = () => {
  visible.value = false
  resolvePromise?.(true)
}

const handleCancel = () => {
  visible.value = false
  resolvePromise?.(false)
}

defineExpose({ show })
</script>

<style scoped>
.confirm-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--dialog-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.confirm-dialog {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 24px;
  width: 400px;
  max-width: 90%;
  text-align: center;
  animation: scaleIn 0.2s;
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.confirm-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.confirm-icon.danger {
  background: var(--danger-bg);
  color: var(--danger-color);
}

.confirm-dialog h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--text-primary);
}

.confirm-dialog p {
  margin: 0 0 24px;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn-secondary, .btn-danger {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-secondary {
  background: var(--disabled-bg);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: var(--hover-bg);
}

.btn-danger {
  background: var(--danger-color);
  color: white;
}

.btn-danger:hover {
  background: color-mix(in srgb, var(--danger-color) 85%, black);
}
</style>
