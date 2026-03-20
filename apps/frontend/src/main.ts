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
// Mount the app immediately after initialisation so the first
// render is not delayed by network-bound silent auth recovery.
// trySigninSilent() then runs in the background.
//
// Skip silent sign-in on ``/oidc-callback`` (the callback page
// completes the flow itself) and on ``/oidc-silent`` (the
// silent-renew iframe — calling it there would spawn a new
// iframe, causing an infinite reload loop).
initOidc()
  .catch(() => undefined)
  .then(() => {
    app.mount('#app')
    const path = window.location.pathname
    if (path !== '/oidc-callback' && path !== '/oidc-silent') {
      trySigninSilent().catch(() => undefined)
    }
  })
