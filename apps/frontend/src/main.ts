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

app.mount('#app')

// Initialise OIDC in the background so the UserManager is ready
// when the user clicks Login.  Errors are silently ignored here;
// the login button will fall back to manual token entry.
initOidc().catch(() => undefined)
