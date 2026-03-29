<template>
  <v-app-bar>
    <v-btn icon="mdi-arrow-left" to="/" />
    <v-toolbar-title>{{ t('userManual') }}</v-toolbar-title>
    <v-spacer />
    <AuthBar />
  </v-app-bar>

  <v-container class="user-manual">
    <v-card class="mb-6">
      <v-card-text>
        <ProseContent />
      </v-card-text>
    </v-card>

    <!-- Interactive configuration card -->
    <v-card class="mb-6">
      <v-card-title class="text-h5">
        {{ t('configureExamples') }}
      </v-card-title>
      <v-card-subtitle>
        {{ t('configureExamplesHint') }}
      </v-card-subtitle>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="docrootUrl"
              density="compact"
              :label="t('docrootUrl')"
              variant="outlined"
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="idpUrl"
              density="compact"
              :hint="t('idpUrlHint')"
              :label="t('idpUrl')"
              variant="outlined"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="ciClientId"
              density="compact"
              :hint="t('ciClientIdHint')"
              :label="t('ciClientId')"
              variant="outlined"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="ciClientSecret"
              density="compact"
              :hint="t('ciClientSecretHint')"
              :label="t('ciClientSecret')"
              variant="outlined"
            />
          </v-col>
          <v-col cols="6" md="2">
            <v-text-field
              v-model="targetNamespace"
              density="compact"
              :label="t('targetNamespace')"
              variant="outlined"
            />
          </v-col>
          <v-col cols="6" md="2">
            <v-text-field
              v-model="targetProject"
              density="compact"
              :label="t('targetProject')"
              variant="outlined"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Tabbed use-case sections -->
    <v-card>
      <v-tabs v-model="activeTab" color="primary">
        <v-tab value="browsing">{{ t('tabBrowsing') }}</v-tab>
        <v-tab value="automated">{{ t('tabAutomated') }}</v-tab>
        <v-tab value="manual">{{ t('tabManual') }}</v-tab>
        <v-tab value="acl">{{ t('tabAcl') }}</v-tab>
        <v-tab value="limitations">{{ t('tabLimitations') }}</v-tab>
      </v-tabs>

      <v-window v-model="activeTab">
        <!-- Browsing tab -->
        <v-window-item value="browsing">
          <v-card-text>
            <p>{{ t('manualBrowsingText') }}</p>
          </v-card-text>
        </v-window-item>

        <!-- Automated Upload (CI/CD) tab -->
        <v-window-item value="automated">
          <v-card-text>
            <p class="mb-3">{{ t('manualAutomatedText') }}</p>
            <ol class="ml-4 mb-4">
              <li>{{ t('manualAutomatedStep1') }}</li>
              <li>{{ t('manualAutomatedStep2') }}</li>
              <li>{{ t('manualAutomatedStep3') }}</li>
              <li>{{ t('manualAutomatedStep4') }}</li>
            </ol>

            <p class="text-subtitle-1 font-weight-bold mb-2">
              {{ t('keycloakSetup') }}
            </p>
            <p class="mb-2">{{ t('keycloakSetupText') }}</p>
            <ol class="ml-4 mb-4">
              <li>{{ t('keycloakStep1') }}</li>
              <li>{{ t('keycloakStep2') }}</li>
              <li>{{ t('keycloakStep3') }}</li>
            </ol>

            <p class="font-weight-bold mb-1">
              {{ t('manualClientCredentialsCurl') }}
            </p>
            <v-sheet class="pa-3 rounded mb-4" color="grey-darken-3">
              <pre class="text-caption text-white">{{ curlTokenExample }}</pre>
            </v-sheet>

            <p class="font-weight-bold mb-1">
              {{ t('manualUploadCurl') }}
            </p>
            <v-sheet class="pa-3 rounded mb-4" color="grey-darken-3">
              <pre class="text-caption text-white">{{ curlUploadExample }}</pre>
            </v-sheet>

            <v-alert density="compact" type="warning">
              {{ t('manualClientCredentialsWarning') }}
            </v-alert>
          </v-card-text>
        </v-window-item>

        <!-- Manual Upload tab -->
        <v-window-item value="manual">
          <v-card-text>
            <p class="mb-3">{{ t('manualAuthText') }}</p>
            <ol class="ml-4 mb-4">
              <li>{{ t('manualAuthStep1') }}</li>
              <li>{{ t('manualAuthStep2') }}</li>
              <li>{{ t('manualAuthStep3') }}</li>
            </ol>
            <p class="mb-3">{{ t('manualUploadText') }}</p>
            <ul class="ml-4">
              <li>{{ t('manualUploadRule1') }}</li>
              <li>{{ t('manualUploadRule2') }}</li>
              <li>{{ t('manualUploadRule3') }}</li>
              <li>{{ t('manualUploadRule4') }}</li>
              <li>{{ t('manualUploadRule5') }}</li>
            </ul>
            <p class="mt-3">{{ t('manualAuthDev') }}</p>
          </v-card-text>
        </v-window-item>

        <!-- Access Control tab -->
        <v-window-item value="acl">
          <v-card-text>
            <p class="mb-3">{{ t('manualAclText') }}</p>
            <v-sheet class="pa-3 rounded mb-4" color="grey-darken-3">
              <pre class="text-caption text-white">{{ aclExample }}</pre>
            </v-sheet>
            <v-alert density="compact" type="info">
              {{ t('manualAclAlphaNotice') }}
            </v-alert>
          </v-card-text>
        </v-window-item>

        <!-- Limitations tab -->
        <v-window-item value="limitations">
          <v-card-text>
            <p class="mb-3">{{ t('manualLimitationsText') }}</p>
            <ul class="ml-4">
              <li class="mb-2">{{ t('manualLimitationRole') }}</li>
              <li class="mb-2">{{ t('manualLimitationSearch') }}</li>
              <li class="mb-2">{{ t('manualLimitationStorage') }}</li>
            </ul>
          </v-card-text>
        </v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import AuthBar from '@/components/AuthBar.vue'
import ProseContent from '@/components/ProseContent.vue'

const { t } = useI18n()

const activeTab = ref('browsing')
const docrootUrl = ref('https://docroot.example.com')
const idpUrl = ref('https://idp.example.com/realms/myrealm')
const ciClientId = ref('my-ci-client')
const ciClientSecret = ref('$CLIENT_SECRET')
const targetNamespace = ref('myns')
const targetProject = ref('myproject')

const curlTokenExample = computed(
  () =>
    String.raw`curl -s -X POST \
  ${idpUrl.value}/protocol/openid-connect/token \
  -d grant_type=client_credentials \
  -d client_id=${ciClientId.value} \
  -d client_secret=${ciClientSecret.value}`,
)

const curlUploadExample = computed(
  () =>
    String.raw`# 1. Obtain a token via client-credentials grant
TOKEN=$(curl -s -X POST \
  ${idpUrl.value}/protocol/openid-connect/token \
  -d grant_type=client_credentials \
  -d client_id=${ciClientId.value} \
  -d client_secret=${ciClientSecret.value} \
  | jq -r .access_token)

# 2. Upload documentation
curl -X POST \
  ${docrootUrl.value}/api/namespaces/${targetNamespace.value}/projects/${targetProject.value}/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs.zip" \
  -F "version=1.0.0" \
  -F "locale=en" \
  -F "latest=true"`,
)

const aclExample = computed(
  () =>
    `# /data/namespaces/${targetNamespace.value}/namespace.toml

creator = "alice"
versioning = "semver"

[access]
public_read = false

[[access.roles]]
role = "docroot-editor"
read = true
write = true

[[access.roles]]
role = "docroot-reader"
read = true
write = false`,
)
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
}
</style>
