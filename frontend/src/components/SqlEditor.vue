<template>
  <div class="editor-wrap">
    <div v-if="editorError" class="editor-fallback">
      <div class="fallback-note">
        SQL 编辑器组件加载失败，已切换到备用输入框。
      </div>
      <textarea
        class="fallback-textarea"
        :value="modelValue"
        spellcheck="false"
        @input="handleFallbackInput"
        @keydown.ctrl.enter.prevent="emit('execute')"
        @keydown.meta.enter.prevent="emit('execute')"
      />
    </div>
    <div v-else ref="editorEl" class="editor-container"></div>
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
const editorError = ref('')
let view = null

const customTheme = EditorView.theme({
  '&': {
    backgroundColor: 'rgba(20, 20, 19, 0.02)',
    color: 'var(--near-black, #141413)',
    fontSize: '14px',
    height: '100%',
  },
  '.cm-content': {
    fontFamily: "'DM Mono', 'Fira Code', 'JetBrains Mono', monospace",
    caretColor: 'var(--charcoal, #4d4c48)',
    padding: '12px 0',
    minHeight: '100%',
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
  {
    key: 'Mod-Enter',
    run: () => {
      emit('execute')
      return true
    },
  },
])

onMounted(() => {
  try {
    const state = EditorState.create({
      doc: props.modelValue,
      extensions: [
        lineNumbers(),
        sql({ dialect: PostgreSQL }),
        customTheme,
        ctrlEnter,
        EditorView.lineWrapping,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            emit('update:modelValue', update.state.doc.toString())
          }
        }),
      ],
    })

    view = new EditorView({ state, parent: editorEl.value })
    editorError.value = ''
  } catch (error) {
    editorError.value = error instanceof Error ? error.message : 'CodeMirror 初始化失败'
    view = null
  }
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

function handleFallbackInput(event) {
  emit('update:modelValue', event.target.value)
}
</script>

<style scoped>
.editor-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: transparent;
  min-width: 0;
}
.editor-container {
  flex: 1;
  min-height: 220px;
  height: 100%;
  overflow: hidden;
  border-top: 1px solid rgba(28, 40, 52, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 243, 235, 0.92));
}
/* Use :deep() to correctly target elements created by CodeMirror */
.editor-container :deep(.cm-editor) {
  height: 100%;
  min-height: 0;
  border-left: 4px solid rgba(201, 100, 66, 0.22);
}
.editor-container :deep(.cm-scroller) {
  font-family: inherit;
  height: 100%;
  overflow: auto;
  overscroll-behavior: contain;
}
.editor-container :deep(.cm-gutters) {
  min-height: 100%;
}
.editor-container :deep(.cm-scroller::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}
.editor-container :deep(.cm-scroller::-webkit-scrollbar-thumb) {
  background: rgba(28, 40, 52, 0.2);
}
.editor-container :deep(.cm-scroller::-webkit-scrollbar-track) {
  background: transparent;
}

.editor-fallback {
  display: grid;
  grid-template-rows: auto minmax(220px, 1fr);
  gap: 10px;
  height: 100%;
  min-height: 220px;
  padding: 12px;
  border-top: 1px solid rgba(28, 40, 52, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 243, 235, 0.92));
}

.fallback-note {
  font-size: 12px;
  color: var(--signal, #b91c1c);
}

.fallback-textarea {
  width: 100%;
  min-height: 220px;
  resize: vertical;
  border: 1px solid rgba(28, 40, 52, 0.14);
  background: rgba(255, 255, 255, 0.94);
  color: var(--near-black, #141413);
  font-family: "'DM Mono', 'Fira Code', 'JetBrains Mono', monospace";
  font-size: 14px;
  line-height: 1.6;
  padding: 12px 14px;
  outline: none;
}

.fallback-textarea:focus {
  border-color: rgba(201, 100, 66, 0.36);
  box-shadow: 0 0 0 3px rgba(201, 100, 66, 0.12);
}
</style>
