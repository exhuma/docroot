<template>
  <v-app-bar>
    <v-btn icon="mdi-arrow-left" to="/" />
    <v-toolbar-title>{{ t('userManual') }}</v-toolbar-title>
    <v-spacer />
    <TokenDialog />
  </v-app-bar>

  <v-container class="user-manual">
    <v-card class="mb-6">
      <v-card-title class="text-h5">
        {{ t('manualBrowsing') }}
      </v-card-title>
      <v-card-text>
        <p>{{ t('manualBrowsingText') }}</p>
      </v-card-text>
    </v-card>

    <v-card class="mb-6">
      <v-card-title class="text-h5">
        {{ t('manualAuthentication') }}
      </v-card-title>
      <v-card-text>
        <p class="mb-3">{{ t('manualAuthText') }}</p>
        <ol class="ml-4">
          <li>{{ t('manualAuthStep1') }}</li>
          <li>{{ t('manualAuthStep2') }}</li>
          <li>{{ t('manualAuthStep3') }}</li>
        </ol>
        <p class="mt-3">{{ t('manualAuthDev') }}</p>
      </v-card-text>
    </v-card>

    <v-card class="mb-6">
      <v-card-title class="text-h5">
        {{ t('manualUpload') }}
      </v-card-title>
      <v-card-text>
        <p class="mb-3">{{ t('manualUploadText') }}</p>
        <ul class="ml-4 mb-3">
          <li>{{ t('manualUploadRule1') }}</li>
          <li>{{ t('manualUploadRule2') }}</li>
          <li>{{ t('manualUploadRule3') }}</li>
          <li>{{ t('manualUploadRule4') }}</li>
          <li>{{ t('manualUploadRule5') }}</li>
        </ul>
        <p class="font-weight-bold mb-1">
          {{ t('manualUploadCurl') }}
        </p>
        <v-sheet
          class="pa-3 rounded"
          color="grey-darken-3"
        >
          <pre class="text-caption text-white">{{
            curlUploadExample
          }}</pre>
        </v-sheet>
      </v-card-text>
    </v-card>

    <v-card class="mb-6">
      <v-card-title class="text-h5">
        {{ t('manualClientCredentials') }}
      </v-card-title>
      <v-card-text>
        <p class="mb-3">
          {{ t('manualClientCredentialsText') }}
        </p>
        <p class="font-weight-bold mb-1">
          {{ t('manualClientCredentialsCurl') }}
        </p>
        <v-sheet
          class="pa-3 rounded"
          color="grey-darken-3"
        >
          <pre class="text-caption text-white">{{
            curlTokenExample
          }}</pre>
        </v-sheet>
        <v-alert
          class="mt-4"
          density="compact"
          type="warning"
        >
          {{ t('manualClientCredentialsWarning') }}
        </v-alert>
      </v-card-text>
    </v-card>

    <v-card class="mb-6">
      <v-card-title class="text-h5">
        {{ t('manualAcl') }}
      </v-card-title>
      <v-card-text>
        <p class="mb-3">{{ t('manualAclText') }}</p>
        <v-sheet
          class="pa-3 rounded"
          color="grey-darken-3"
        >
          <pre class="text-caption text-white">{{
            aclExample
          }}</pre>
        </v-sheet>
        <v-alert
          class="mt-4"
          density="compact"
          type="info"
        >
          {{ t('manualAclAlphaNotice') }}
        </v-alert>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
  import { useI18n } from 'vue-i18n'
  import TokenDialog from '@/components/TokenDialog.vue'

  const { t } = useI18n()

  const curlUploadExample = String.raw`# 1. Obtain a token via client-credentials grant
TOKEN=$(curl -s -X POST \
  https://idp.example.com/realms/myrealm/\
protocol/openid-connect/token \
  -d grant_type=client_credentials \
  -d client_id=my-ci-client \
  -d client_secret=MY_SECRET \
  | jq -r .access_token)

# 2. Upload documentation
curl -X POST \
  https://docroot.example.com/api/namespaces/myns/\
projects/myproject/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs.zip" \
  -F "version=1.0.0" \
  -F "locale=en" \
  -F "latest=true"`

  const curlTokenExample = String.raw`curl -s -X POST \
  https://idp.example.com/realms/myrealm/\
protocol/openid-connect/token \
  -d grant_type=client_credentials \
  -d client_id=my-ci-client \
  -d client_secret=MY_SECRET`

  const aclExample = `# /data/namespaces/myns/namespace.toml

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
write = false`
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
}
</style>
