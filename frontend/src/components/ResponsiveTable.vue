<script setup lang="ts">
defineProps<{
  headers: string[]
  rows: any[][]
}>()
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm text-left">
      <thead class="text-xs text-slate-500 uppercase bg-slate-50">
        <tr>
          <th
            v-for="(header, index) in headers"
            :key="index"
            class="px-3 sm:px-4 py-2 sm:py-3 font-medium whitespace-nowrap"
          >
            {{ header }}
          </th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-100">
        <tr
          v-for="(row, rowIndex) in rows"
          :key="rowIndex"
          class="hover:bg-slate-50/60 transition-colors"
        >
          <td
            v-for="(cell, cellIndex) in row"
            :key="cellIndex"
            class="px-3 sm:px-4 py-2 sm:py-3 whitespace-nowrap"
          >
            <slot :name="'cell-' + cellIndex" :value="cell" :row="row">
              {{ cell }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
