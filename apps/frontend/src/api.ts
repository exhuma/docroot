const BASE = '/api'

export interface Namespace {
  name: string
}

export interface Project {
  name: string
}

export interface VersionInfo {
  name: string
  locales: string[]
  is_latest: boolean
}

export interface ResolveResult {
  version: string
  locale: string
  fallback_used: boolean
}

async function handleResponse (res: Response): Promise<unknown> {
  if (!res.ok) {
    let msg = res.statusText
    try {
      const body = await res.json()
      msg = body.detail ?? body.message ?? msg
    } catch {
      // ignore parse errors
    }
    throw new Error(msg)
  }
  if (res.status === 204) {
    return undefined
  }
  return res.json()
}

function nsBase (ns: string): string {
  return `${BASE}/namespaces/${encodeURIComponent(ns)}`
}

function projBase (ns: string, proj: string): string {
  return (
    `${nsBase(ns)}/projects/${encodeURIComponent(proj)}`
  )
}

export const api = {
  async listNamespaces (): Promise<Namespace[]> {
    const res = await fetch(`${BASE}/namespaces`)
    return handleResponse(res) as Promise<Namespace[]>
  },

  async createNamespace (
    name: string,
    token: string,
  ): Promise<void> {
    const res = await fetch(`${BASE}/namespaces`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
    })
    await handleResponse(res)
  },

  async deleteNamespace (
    name: string,
    token: string,
  ): Promise<void> {
    const res = await fetch(
      `${BASE}/namespaces/${encodeURIComponent(name)}`,
      {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      },
    )
    await handleResponse(res)
  },

  async listProjects (ns: string): Promise<Project[]> {
    const res = await fetch(`${nsBase(ns)}/projects`)
    return handleResponse(res) as Promise<Project[]>
  },

  async createProject (
    ns: string,
    name: string,
    token: string,
  ): Promise<void> {
    const res = await fetch(`${nsBase(ns)}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
    })
    await handleResponse(res)
  },

  async deleteProject (
    ns: string,
    name: string,
    token: string,
  ): Promise<void> {
    const res = await fetch(
      `${nsBase(ns)}/projects/${encodeURIComponent(name)}`,
      {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      },
    )
    await handleResponse(res)
  },

  async listVersions (
    ns: string,
    proj: string,
  ): Promise<VersionInfo[]> {
    const res = await fetch(`${projBase(ns, proj)}/versions`)
    return handleResponse(res) as Promise<VersionInfo[]>
  },

  async resolveVersion (
    ns: string,
    proj: string,
    version: string,
    locale: string,
  ): Promise<ResolveResult> {
    const res = await fetch(
      `${projBase(ns, proj)}/resolve/`
      + `${encodeURIComponent(version)}/`
      + `${encodeURIComponent(locale)}`,
    )
    return handleResponse(res) as Promise<ResolveResult>
  },

  async uploadVersion (
    ns: string,
    proj: string,
    form: FormData,
    token: string,
  ): Promise<void> {
    const res = await fetch(`${projBase(ns, proj)}/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    })
    await handleResponse(res)
  },

  async setLatest (
    ns: string,
    proj: string,
    version: string,
    token: string,
  ): Promise<void> {
    const res = await fetch(
      `${projBase(ns, proj)}/versions/`
      + `${encodeURIComponent(version)}/latest`,
      {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      },
    )
    await handleResponse(res)
  },
}
