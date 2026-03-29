import prettierConfig from 'eslint-config-prettier'
import vuetify from 'eslint-config-vuetify'

// vuetify() is async; ESLint 9 awaits a Promise default export.
// prettierConfig is appended last to disable conflicting format rules.
export default vuetify({ ts: true }).then((configs) => [...configs, prettierConfig])
