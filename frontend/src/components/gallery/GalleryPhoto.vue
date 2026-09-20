<!-- Load protected images with headers, never put the teacher secret into an image URL. -->
<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { galleryBlob } from '../../services/galleryApi'
const props = defineProps<{ url: string; admin: boolean; alt: string }>()
const src = ref('')
const error = ref('')
let generation = 0
function clear() { if (src.value) URL.revokeObjectURL(src.value); src.value = '' }
async function load() {
  const ticket = ++generation
  clear(); error.value = ''
  try {
    const value = await galleryBlob(props.url, props.admin)
    if (ticket !== generation) URL.revokeObjectURL(value)
    else src.value = value
  } catch { if (ticket === generation) error.value = '图片暂时无法加载' }
}
watch(() => [props.url, props.admin], load, { immediate: true })
onBeforeUnmount(() => { ++generation; clear() })
</script>
<template>
  <img v-if="src" :src="src" :alt="alt" decoding="async" />
  <span v-else-if="error" class="photo-state">{{ error }}，请刷新重试</span>
  <span v-else class="photo-state" role="status">正在加载图片…</span>
</template>
<style scoped>
img { display: block; width: 100%; height: 100%; object-fit: cover; }
.photo-state { display: grid; place-content: center; min-height: 180px; padding: 12px; }
</style>
