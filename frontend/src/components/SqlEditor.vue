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
    backgroundColor: 'rgba(28, 40, 52, 0.03)',
    color: 'var(--ink-950, #1b2730)',
    fontSize: '14px',
  },
  '.cm-content': {
    fontFamily: "'DM Mono', 'Fira Code', 'JetBrains Mono', monospace",
    caretColor: 'var(--ink-900, #23323d)',
    padding: '12px 0',
  },
  '.cm-line': {
    lineHeight: '1.6',
  },
  '.cm-gutters': {
    backgroundColor: 'transparent',
    color: 'rgba(28, 40, 52, 0.4)',
    borderRight: '1px solid rgba(28, 40, 52, 0.08)',
  },
  '&.cm-focused': {
    outline: 'none',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: 'var(--accent, #c4692f)',
    borderLeftWidth: '2px',
  },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection': {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
  },
  '.cm-activeLine': {
    backgroundColor: 'rgba(28, 40, 52, 0.04)',
  },
  '.cm-activeLineGutter': {
    backgroundColor: 'transparent',
    color: 'var(--ink-700, #394956)',
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
