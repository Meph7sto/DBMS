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
// Remove oneDark to use the default light theme which perfectly fits the UI
// import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps({
  modelValue: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue', 'execute'])

const editorEl = ref(null)
let view = null

const customTheme = EditorView.theme({
  '&': {
    backgroundColor: 'rgba(20, 20, 19, 0.02)',
    color: 'var(--near-black, #141413)',
    fontSize: '14px',
  },
  '.cm-content': {
    fontFamily: "'DM Mono', 'Fira Code', 'JetBrains Mono', monospace",
    caretColor: 'var(--charcoal, #4d4c48)',
    padding: '12px 0',
  },
  '.cm-line': {
    lineHeight: '1.6',
  },
  '.cm-gutters': {
    backgroundColor: 'transparent',
    color: 'var(--stone-gray, #87867f)',
    borderRight: '1px solid var(--border-cream, #f0eee6)',
  },
  '&.cm-focused': {
    outline: 'none',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: 'var(--terracotta, #c96442)',
    borderLeftWidth: '2px',
  },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection': {
    backgroundColor: 'rgba(201, 100, 66, 0.15)',
  },
  '.cm-activeLine': {
    backgroundColor: 'rgba(20, 20, 19, 0.03)',
  },
  '.cm-activeLineGutter': {
    backgroundColor: 'transparent',
    color: 'var(--olive-gray, #5e5d59)',
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
  background: transparent;
}
.editor-container {
  flex: 1;
  overflow: auto;
}
/* Use :deep() to correctly target elements created by CodeMirror */
.editor-container :deep(.cm-editor) {
  height: 100%;
}
.editor-container :deep(.cm-scroller) {
  font-family: inherit;
}
</style>
