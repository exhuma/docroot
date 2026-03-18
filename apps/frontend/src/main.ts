/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Composables
import { createApp } from 'vue'

// Auth
import { initOidc } from '@/auth'

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Styles
import 'unfonts.css'

const app = createApp(App)

registerPlugins(app)

// Initialise OIDC before mounting so the UserManager is
// available synchronously in component onMounted hooks.
// Without this, TokenDialog.onMounted sees getUserManager()
// as null and never shows the OIDC login button.
initOidc()
  .catch(() => undefined)
  .then(() => app.mount('#app'))
