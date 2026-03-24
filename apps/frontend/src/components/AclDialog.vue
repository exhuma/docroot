<template>
  <v-dialog
    :model-value="modelValue"
    max-width="520"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card :title="t('manageAccess')">
      <v-card-text>
        <v-alert v-if="forbidden" density="compact" type="warning">
          {{ t('aclForbidden') }}
        </v-alert>

        <v-alert v-else-if="loadError" density="compact" type="error">
          {{ loadError }}
        </v-alert>

        <template v-else-if="!loading">
          <v-switch
            v-model="publicRead"
            :label="t('publicRead')"
            :hint="t('aclPublicReadHint')"
            :loading="savingPublicRead"
            :disabled="savingPublicRead || savingBrowsable"
            density="compact"
            persistent-hint
            @update:model-value="saveFlags()"
          />
          <v-switch
            v-model="browsable"
            :label="t('browsable')"
            :hint="t('aclBrowsableHint')"
            :loading="savingBrowsable"
            :disabled="savingPublicRead || savingBrowsable"
            density="compact"
            persistent-hint
            class="mt-2"
            @update:model-value="saveFlags()"
          />

          <v-divider class="my-4" />

          <p v-if="rows.length === 0" class="text-body-2 text-medium-emphasis">
            {{ t('aclNoRoles') }}
          </p>

          <v-table v-else density="compact">
            <thead>
              <tr>
                <th>{{ t('aclRoleName') }}</th>
                <th style="align: center">{{ t('aclCanRead') }}</th>
                <th style="align: center">{{ t('aclCanWrite') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.role">
                <td>
                  <code class="text-body-2">{{ row.role }}</code>
                </td>
                <td class="text-center">
                  <v-checkbox
                    v-model="row.read"
                    density="compact"
                    hide-details
                    :loading="row.saving"
                    @change="save(row)"
                  />
                </td>
                <td class="text-center">
                  <v-checkbox
                    v-model="row.write"
                    density="compact"
                    hide-details
                    :loading="row.saving"
                    @change="save(row)"
                  />
                </td>
              </tr>
            </tbody>
          </v-table>

          <v-alert v-if="saveError" class="mt-3" density="compact" type="error">
            {{ saveError }}
          </v-alert>
        </template>

        <v-progress-circular v-else indeterminate />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn @click="$emit('update:modelValue', false)">
          {{ t('back') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { api, type AclRole } from '@/api'
import { token } from '@/auth'

const props = defineProps<{
  modelValue: boolean
  namespace: string
}>()

defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const { t } = useI18n()

interface Row extends AclRole {
  saving: boolean
}

const loading = ref(false)
const forbidden = ref(false)
const loadError = ref<string | null>(null)
const saveError = ref<string | null>(null)
const rows = ref<Row[]>([])

const publicRead = ref(false)
const browsable = ref(false)
const savingPublicRead = ref(false)
const savingBrowsable = ref(false)

async function load() {
  if (!props.namespace || !token.value) return
  loading.value = true
  forbidden.value = false
  loadError.value = null
  saveError.value = null
  rows.value = []
  try {
    const [acl, me] = await Promise.all([
      api.getAcl(props.namespace, token.value),
      api.getMe(token.value),
    ])

    publicRead.value = acl.public_read
    browsable.value = acl.browsable

    const userRoles = me.roles.map((r) => r.toLowerCase())

    // Build a map of existing ACL entries keyed by lowercase role.
    const aclMap = new Map<string, AclRole>(acl.roles.map((r) => [r.role.toLowerCase(), r]))

    rows.value = userRoles.map((lowerRole) => {
      const existing = aclMap.get(lowerRole)
      // Preserve the role name as stored in the ACL when present,
      // otherwise use the name as it appears in the server roles.
      const roleName =
        existing?.role ?? me.roles.find((r) => r.toLowerCase() === lowerRole) ?? lowerRole
      return {
        role: roleName,
        read: existing?.read ?? false,
        write: existing?.write ?? false,
        saving: false,
      }
    })
  } catch (err) {
    const msg = (err as Error).message ?? ''
    if (msg.toLowerCase().includes('403') || msg.toLowerCase().includes('access denied')) {
      forbidden.value = true
    } else {
      loadError.value = msg
    }
  } finally {
    loading.value = false
  }
}

async function saveFlags() {
  if (!token.value) return
  saveError.value = null
  savingPublicRead.value = true
  savingBrowsable.value = true
  try {
    await api.patchAclFlags(props.namespace, publicRead.value, browsable.value, token.value)
  } catch (err) {
    saveError.value = (err as Error).message ?? 'Save failed'
  } finally {
    savingPublicRead.value = false
    savingBrowsable.value = false
  }
}

async function save(row: Row) {
  if (!token.value) return
  saveError.value = null
  row.saving = true
  try {
    if (!row.read && !row.write) {
      await api.removeAclRole(props.namespace, row.role, token.value)
    } else {
      await api.upsertAclRole(props.namespace, row.role, row.read, row.write, token.value)
    }
  } catch (err) {
    saveError.value = (err as Error).message ?? 'Save failed'
  } finally {
    row.saving = false
  }
}

watch(
  () => [props.modelValue, props.namespace] as const,
  ([open]) => {
    if (open) load()
  },
)
</script>
