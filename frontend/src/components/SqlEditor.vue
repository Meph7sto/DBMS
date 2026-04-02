<template>
  <div class="editor-wrap">
    <div ref="editorEl" class="editor-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { EditorView, lineNumbers, keymap } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { sql, PostgreSQL } from '@codemirror/lang-sql'
import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps({
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'execute'])

const editorEl = ref(null)
let view = null

const customTheme = EditorView.theme({
  '&': {
    backgroundColor: 'var(--bg-primary)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border)',
    fontSize: '13px',
  },
  '.cm-content': {
    fontFamily: "'DM Mono', monospace",
    caretColor: 'var(--accent)',
    padding: '8px 0',
  },
  '.cm-gutters': {
    backgroundColor: 'var(--bg-tertiary)',
    color: 'var(--text-muted)',
    border: 'none',
    borderRight: '1px solid var(--border)',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: 'var(--accent)',
  },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground': {
    backgroundColor: 'rgba(0, 220, 230, 0.15)',
  },
  '.cm-activeLine': {
    backgroundColor: 'rgba(0, 220, 230, 0.04)',
  },
  '.cm-activeLineGutter': {
    backgroundColor: 'var(--bg-hover)',
  },
})

const ctrlEnter = keymap.of([
  {
    key: 'Ctrl-Enter',
    run: () => {
      emit('execute')
      return true
    },
  },
])

onMounted(() => {
  const state = EditorState.create({
    doc: props.modelValue,
    extensions: [
      lineNumbers(),
      sql({ dialect: PostgreSQL }),
      oneDark,
      customTheme,
      ctrlEnter,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          emit('update:modelValue', update.state.doc.toString())
        }
      }),
    ],
  })

  view = new EditorView({ state, parent: editorEl.value })
})

watch(
  () => props.modelValue,
  (val) => {
    if (view && val !== view.state.doc.toString()) {
      view.dispatch({
        changes: { from: 0, to: view.state.doc.length, insert: val },
      })
    }
  }
)

onUnmounted(() => {
  if (view) view.destroy()
})
</script>

<style scoped>
.editor-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.editor-container {
  flex: 1;
  overflow: auto;
}
.editor-container .cm-editor {
  height: 100%;
}
</style>
