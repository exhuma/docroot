/**
 * main.ts
 *
 * Bootstraps Vuetify and other plugins then mounts the App`
 */

// Composables
import { createApp } from 'vue'

// Auth
import { initOidc, trySigninSilent } from '@/auth'

// Plugins
import { registerPlugins } from '@/plugins'

// Components
import App from './App.vue'

// Styles
import 'unfonts.css'

const app = createApp(App)

registerPlugins(app)

// Initialise the OIDC UserManager before mounting so that it is
// available synchronously in component onMounted hooks.
//
// The silent-renew iframe (``/oidc-silent``) also runs this file,
// so we must NOT call trySigninSilent() there — doing so would
// spawn another iframe, causing an infinite reload loop.
initOidc()
  .catch(() => undefined)
  .then(async () => {
    if (window.location.pathname !== '/oidc-silent') {
      await trySigninSilent()
    }
    app.mount('#app')
  })
