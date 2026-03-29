const BASE = '/api'

export interface Namespace {
  name: string
  public_read: boolean
  browsable: boolean
  versioning: string
  creator: string
  creator_display_name: string
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

export interface AclRole {
  role: string
  read: boolean
  write: boolean
}

export interface AclData {
  public_read: boolean
  browsable: boolean
  roles: AclRole[]
}

export interface Me {
  subject: string
  roles: string[]
}

async function handleResponse(res: Response): Promise<unknown> {
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

function nsBase(ns: string): string {
  return `${BASE}/namespaces/${encodeURIComponent(ns)}`
}

function projBase(ns: string, proj: string): string {
  return `${nsBase(ns)}/projects/${encodeURIComponent(proj)}`
}

export const api = {
  async listNamespaces(token?: string | null): Promise<Namespace[]> {
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await fetch(`${BASE}/namespaces`, { headers })
    return handleResponse(res) as Promise<Namespace[]>
  },

  async createNamespace(
    name: string,
    token: string,
    publicRead = false,
    browsable = true,
  ): Promise<void> {
    const res = await fetch(`${BASE}/namespaces`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name, public_read: publicRead, browsable }),
    })
    await handleResponse(res)
  },

  async transferOwnership(name: string, token: string): Promise<void> {
    const res = await fetch(`${BASE}/namespaces/${encodeURIComponent(name)}/owner`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    })
    await handleResponse(res)
  },

  async deleteNamespace(name: string, token: string): Promise<void> {
    const res = await fetch(`${BASE}/namespaces/${encodeURIComponent(name)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    await handleResponse(res)
  },

  async listProjects(ns: string, token?: string | null): Promise<Project[]> {
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await fetch(`${nsBase(ns)}/projects`, { headers })
    return handleResponse(res) as Promise<Project[]>
  },

  async createProject(ns: string, name: string, token: string): Promise<void> {
    const res = await fetch(`${nsBase(ns)}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
    })
    await handleResponse(res)
  },

  async deleteProject(ns: string, name: string, token: string): Promise<void> {
    const res = await fetch(`${nsBase(ns)}/projects/${encodeURIComponent(name)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    await handleResponse(res)
  },

  async listVersions(ns: string, proj: string, token?: string | null): Promise<VersionInfo[]> {
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await fetch(`${projBase(ns, proj)}/versions`, { headers })
    return handleResponse(res) as Promise<VersionInfo[]>
  },

  async resolveVersion(
    ns: string,
    proj: string,
    version: string,
    locale: string,
    token?: string | null,
  ): Promise<ResolveResult> {
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {}
    const res = await fetch(
      `${projBase(ns, proj)}/resolve/` +
        `${encodeURIComponent(version)}/` +
        `${encodeURIComponent(locale)}`,
      { headers },
    )
    return handleResponse(res) as Promise<ResolveResult>
  },

  async uploadVersion(ns: string, proj: string, form: FormData, token: string): Promise<void> {
    const res = await fetch(`${projBase(ns, proj)}/upload`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    })
    await handleResponse(res)
  },

  async setLatest(ns: string, proj: string, version: string, token: string): Promise<void> {
    const res = await fetch(
      `${projBase(ns, proj)}/versions/` + `${encodeURIComponent(version)}/latest`,
      {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}` },
      },
    )
    await handleResponse(res)
  },

  async getAcl(ns: string, token: string): Promise<AclData> {
    const res = await fetch(`${nsBase(ns)}/acl`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return handleResponse(res) as Promise<AclData>
  },

  async upsertAclRole(
    ns: string,
    role: string,
    read: boolean,
    write: boolean,
    token: string,
  ): Promise<void> {
    const res = await fetch(`${nsBase(ns)}/acl/roles/${encodeURIComponent(role)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ read, write, role }),
    })
    await handleResponse(res)
  },

  async removeAclRole(ns: string, role: string, token: string): Promise<void> {
    const res = await fetch(`${nsBase(ns)}/acl/roles/${encodeURIComponent(role)}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${token}` },
    })
    await handleResponse(res)
  },

  /** Return the subject and roles of the authenticated caller. */
  async getMe(token: string): Promise<Me> {
    const res = await fetch(`${BASE}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    return handleResponse(res) as Promise<Me>
  },

  /** Update the public_read and browsable flags for a namespace. */
  async patchAclFlags(
    ns: string,
    publicRead: boolean,
    browsable: boolean,
    token: string,
  ): Promise<void> {
    const res = await fetch(`${nsBase(ns)}/acl`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        public_read: publicRead,
        browsable,
      }),
    })
    await handleResponse(res)
  },

  /**
   * Exchange a bearer token for an HttpOnly session cookie.
   * The cookie will be attached by the browser to all subsequent
   * same-origin requests, including iframe navigations.
   */
  async createSession(token: string): Promise<void> {
    const res = await fetch(`${BASE}/auth/session`, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { Authorization: `Bearer ${token}` },
    })
    await handleResponse(res)
  },

  /** Clear the HttpOnly session cookie server-side. */
  async deleteSession(): Promise<void> {
    const res = await fetch(`${BASE}/auth/session`, {
      method: 'DELETE',
      credentials: 'same-origin',
    })
    await handleResponse(res)
  },
}
