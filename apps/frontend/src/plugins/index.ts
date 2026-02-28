// Types
import type { App } from 'vue'

import router from '../router'

import i18n from './i18n'

// Plugins
import vuetify from './vuetify'

export function registerPlugins (app: App) {
  app.use(vuetify)
  app.use(i18n)
  app.use(router)
}
