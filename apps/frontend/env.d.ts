/// <reference types="vite/client" />
/// <reference types="unplugin-vue-router/client" />
/// <reference types="vite-plugin-vue-layouts-next/client" />

interface ImportMetaEnv {
  /** GitHub repository URL shown in the footer and panel. */
  readonly VITE_GITHUB_REPO_URL?: string
  /** Short git commit hash injected at Docker build time. */
  readonly VITE_APP_COMMIT?: string
  /** ISO-8601 build timestamp injected at Docker build time. */
  readonly VITE_APP_BUILD_TIME?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
