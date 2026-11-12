import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'
import * as Vue from 'vue'
import { compileScript, parse } from '@vue/compiler-sfc'
import { canAccessRoute } from '../src/router/access.js'

// Compile the real components; only transport, routing and Vuetify are stubbed.
function component(file, modules, template = true) {
  const { descriptor } = parse(readFileSync(new URL(`../src/${file}`, import.meta.url), 'utf8'))
  const script = compileScript(descriptor, { id: file, inlineTemplate: template, genDefaultAs: 'component' })
  const code = script.content.replace(
    /import\s+(\{[^}]*\}|[\w$]+)\s+from\s+['"]([^'"]+)['"];?/g,
    (_, binding, path) => {
      const source = path === 'vue' ? 'Vue' : `modules[${JSON.stringify(path)}]`
      return `const ${binding.replace(/\bas\b/g, ':')} = ${source};`
    },
  )
  return new Function('Vue', 'modules', `${code}; return component`)(Vue, modules)
}

function renderer() {
  const remove = (node) => {
    if (node.parent) node.parent.children.splice(node.parent.children.indexOf(node), 1)
    node.parent = null
  }
  return Vue.createRenderer({
    createElement: (tag) => ({ tag, children: [], props: {} }),
    createText: (text) => ({ text }),
    createComment: (text) => ({ text }),
    insert(node, parent, anchor) {
      remove(node)
      const index = anchor ? parent.children.indexOf(anchor) : -1
      parent.children.splice(index < 0 ? parent.children.length : index, 0, node)
      node.parent = parent
    },
    remove,
    setText: (node, text) => { node.text = text },
    setElementText: (node, text) => { node.text = text; node.children = [] },
    parentNode: (node) => node.parent,
    nextSibling: (node) => node.parent?.children[node.parent.children.indexOf(node) + 1],
    patchProp: (node, key, oldValue, value) => { node.props[key] = value },
  })
}

test('server switch replaces rows and dialogs; late responses and actions retain their original server', async () => {
  const servers = Vue.reactive({ selectedId: 1, loaded: true, loading: false, activeItems: [{ id: 1 }, { id: 2 }], fetch: async () => {} })
  const pending = []
  const mutations = []
  let deferred = true
  const api = {
    list: (serverId) => deferred ? new Promise(resolve => pending.push({ serverId, resolve })) : Promise.resolve({ rows: [] }),
    setState: async (...args) => { mutations.push(args) },
  }
  const auth = { can: (permission) => permission !== 'lb:read', user: { username: 'admin' }, role: 'admin' }
  const route = Vue.reactive({ name: 'dispatcher', meta: {} })
  const empty = { render: () => Vue.h('div') }
  const modules = {
    '@/router/access': { canAccessRoute },
    '@/api': { dispatcherApi: api },
    '@/stores/auth': { useAuthStore: () => auth },
    '@/stores/servers': { useServersStore: () => servers },
    '@/stores/ui': { useUiStore: () => ({ success() {}, error() {} }) },
    'vue-router': { useRoute: () => route, useRouter: () => ({ getRoutes: () => [] }) },
    '@/components/ConfirmDialog.vue': empty,
    '@/components/DispatcherRowDialog.vue': empty,
    '@/components/NodeStateSwitch.vue': empty,
    '@/components/LoadBalancerPanel.vue': empty,
  }
  const instances = []
  const panel = component('components/DispatcherPanel.vue', modules, false)
  const setup = panel.setup
  panel.setup = (props, context) => {
    const state = setup(props, context)
    instances.push({ state, instance: Vue.getCurrentInstance() })
    return state
  }
  panel.render = () => Vue.h('div')
  modules['@/components/DispatcherPanel.vue'] = panel
  const view = component('views/DispatcherView.vue', modules)
  const layout = component('layouts/AppLayout.vue', modules)
  const app = renderer().createApp(layout)
  const passthrough = { setup: (_, { slots }) => () => Vue.h('div', slots.default?.()) }
  const tags = new Set()
  for (const file of ['layouts/AppLayout.vue', 'views/DispatcherView.vue']) {
    const source = readFileSync(new URL(`../src/${file}`, import.meta.url), 'utf8')
    for (const [, tag] of source.matchAll(/<(v-[a-z-]+)/g)) tags.add(tag)
  }
  for (const tag of tags) app.component(tag, passthrough)
  app.component('RouterLink', passthrough)
  app.component('RouterView', { render: () => Vue.h(view) })
  app.mount({ children: [] })
  try {
    const first = instances[0]
    first.state.openEdit({ id: 7, destination: 'A' })
    first.state.askDelete({ id: 7, destination: 'A' })
    servers.selectedId = 2
    await Vue.nextTick()
    const second = instances[1]
    assert.equal(first.instance.isUnmounted, true)
    assert.equal(second.state.dialog.value, false)
    assert.equal(second.state.confirmDelete.value, false)
    assert.deepEqual(second.state.rows.value, [])
    pending[1].resolve({ rows: [{ id: 7, destination: 'B' }] })
    await Vue.nextTick()
    pending[0].resolve({ rows: [{ id: 7, destination: 'A' }] })
    await Vue.nextTick()
    assert.equal(second.state.rows.value[0].destination, 'B')
    // Even a callback retained from the old instance must never target B.
    deferred = false
    await first.state.changeState({ id: 7, destination: 'A' }, 'inactive')
    assert.deepEqual(mutations, [[1, 7, 'inactive']])
    servers.selectedId = 1
    await Vue.nextTick()
    assert.notEqual(instances[2], first)
    assert.equal(instances[2].state.dialog.value, false)
  } finally {
    app.unmount()
  }
})

for (const [permissions, expectedTab] of [
  [['lb:read'], 'loadbalancer'],
  [['dispatcher:read'], 'dispatcher'],
  [['dispatcher:read', 'lb:read'], 'dispatcher'],
]) {
  test(`distribution view mounts only permitted panels: ${permissions.join(', ')}`, () => {
    const mounted = []
    const tabs = []
    const panel = name => ({ setup: () => { mounted.push(name); return () => Vue.h('div') } })
    const view = component('views/DispatcherView.vue', {
      '@/stores/auth': { useAuthStore: () => ({ can: p => permissions.includes(p) }) },
      '@/stores/servers': { useServersStore: () => ({ selectedId: 1 }) },
      '@/components/DispatcherPanel.vue': panel('dispatcher'),
      '@/components/LoadBalancerPanel.vue': panel('loadbalancer'),
    })
    const app = renderer().createApp(view)
    const passthrough = { setup: (_, { slots }) => () => Vue.h('div', slots.default?.()) }
    for (const tag of ['v-card', 'v-tab', 'v-divider', 'v-card-text', 'v-window', 'v-window-item']) {
      app.component(tag, passthrough)
    }
    app.component('v-tabs', {
      props: ['modelValue'],
      setup: (props, { slots }) => {
        tabs.push(props.modelValue)
        return () => Vue.h('div', slots.default?.())
      },
    })
    app.mount({ children: [] })
    try {
      assert.deepEqual(tabs, [expectedTab])
      assert.equal(mounted.includes('dispatcher'), permissions.includes('dispatcher:read'))
      assert.equal(mounted.includes('loadbalancer'), permissions.includes('lb:read'))
    } finally {
      app.unmount()
    }
  })
}
