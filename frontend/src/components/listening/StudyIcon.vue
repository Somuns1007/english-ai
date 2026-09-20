<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <template v-if="name === 'headphones'"><path d="M4 14v-3a8 8 0 0 1 16 0v3" /><rect x="3" y="12" width="4" height="8" rx="2" /><rect x="17" y="12" width="4" height="8" rx="2" /></template>
    <template v-else-if="name === 'grid'"><rect x="3" y="3" width="7" height="7" rx="2" /><rect x="14" y="3" width="7" height="7" rx="2" /><rect x="3" y="14" width="7" height="7" rx="2" /><rect x="14" y="14" width="7" height="7" rx="2" /></template>
    <template v-else-if="name === 'book'"><path d="M12 5v15M12 5C8 2 4 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1Z" /></template>
    <template v-else-if="name === 'wave'"><path d="M4 10v4m4-8v12m4-15v18m4-15v12m4-8v4" /></template>
    <template v-else-if="name === 'chart'"><path d="M4 4v16h16M8 15l4-5 4 2 4-7" /></template>
    <template v-else-if="name === 'arrow'"><path d="M5 12h14m-6-6 6 6-6 6" /></template>
    <template v-else-if="name === 'file'"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6Zm0 0v6h6M8 13h8m-8 4h5" /></template>
    <template v-else-if="name === 'home'"><path d="m3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9" /></template>
    <template v-else-if="name === 'refresh'"><path d="M20 10a8 8 0 0 0-14-5L3 8m0-5v5h5M4 14a8 8 0 0 0 14 5l3-3m0 5v-5h-5" /></template>
    <template v-else><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10v.01" /></template>
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ name: string; size?: number }>(), { size: 20 })
</script>
