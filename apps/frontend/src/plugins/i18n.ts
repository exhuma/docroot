import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    namespaces: 'Namespaces',
    projects: 'Projects',
    versions: 'Versions',
    upload: 'Upload',
    delete: 'Delete',
    create: 'Create',
    name: 'Name',
    version: 'Version',
    locale: 'Locale',
    latest: 'latest',
    setLatest: 'Set as latest',
    noNamespaces: 'No namespaces found.',
    noProjects: 'No projects found.',
    noVersions: 'No versions found.',
    uploadTitle: 'Upload Documentation',
    uploadSuccess: 'Upload successful.',
    uploadError: 'Upload failed.',
    loginRequired: 'Login required for write operations.',
    authToken: 'Bearer token',
    login: 'Set token',
    logout: 'Clear token',
    loginWithOidc: 'Login with OIDC',
    localeShown: 'Showing locale: {locale}',
    fallbackNotice:
      'Requested locale not available. Showing: {locale}',
    back: 'Back',
    cancel: 'Cancel',
    selectVersion: 'Select version',
    selectLocale: 'Select locale',
    language: 'Language',
    markAsLatest: 'Mark as latest',
    isLatest: 'Is latest',
    viewDocs: 'View docs',
    publicRead: 'Public read',
    createdBy: 'Created by: {creator}',
    takeOwnership: 'Take ownership',
    dragPanel: 'Drag to reposition panel',
    devModeNotice:
      'Documentation preview is not available in the'
      + ' dev server. nginx is required to serve static'
      + ' documentation files.',
    userManual: 'User Manual',
    manualBrowsing: 'Browsing Documentation',
    manualBrowsingText:
      'Open the application in a browser. The home page'
      + ' lists all namespaces you have access to. Select'
      + ' a namespace to see its projects, then select a'
      + ' project to see available versions. Select a'
      + ' version and locale to open the documentation'
      + ' viewer.',
    manualAuthentication: 'Authentication',
    manualAuthText:
      'Protected operations require a Bearer token issued'
      + ' by the configured OIDC provider.',
    manualAuthStep1:
      'Click the Login button in the top-right corner.',
    manualAuthStep2:
      'If OIDC is configured, click "Login with OIDC" to'
      + ' be redirected to the identity provider.',
    manualAuthStep3:
      'After authenticating, you are redirected back and'
      + ' logged in automatically.',
    manualAuthDev:
      'For local development, paste a raw Bearer token'
      + ' directly into the text field instead.',
    manualUpload: 'Uploading Documentation',
    manualUploadText:
      'Navigate to a project, then click Upload (visible'
      + ' only when authenticated with write access).'
      + ' The uploaded ZIP must satisfy these constraints:',
    manualUploadRule1: 'Contains index.html at the archive root',
    manualUploadRule2: 'No path-traversal (..) entries',
    manualUploadRule3: 'No symlink entries',
    manualUploadRule4: 'No more than 500 files',
    manualUploadRule5: 'No more than 500 MB extracted size',
    manualUploadCurl: 'Example: upload via curl',
    manualClientCredentials: 'Automated Uploads (CI/CD)',
    manualClientCredentialsText:
      'Use the OAuth2 client-credentials grant to obtain'
      + ' a token for automated uploads:',
    manualClientCredentialsCurl: 'Obtain a token:',
    manualClientCredentialsWarning:
      'Known limitation (alpha): when using a'
      + ' client-credentials flow, the service account'
      + ' may not have roles matching human users. ACL'
      + ' entries set via this flow may not grant access'
      + ' to other users. Use a device-code flow to act'
      + ' on behalf of a user.',
    manualAcl: 'Access Control (ACL)',
    manualAclText:
      'Each namespace has a namespace.toml file that'
      + ' controls who can read and write. Roles are'
      + ' matched exactly against JWT role claims.',
    manualAclAlphaNotice:
      'Alpha limitation: ACL roles cannot be granted or'
      + ' revoked via the API yet. Edit namespace.toml'
      + ' directly or contact your operator.',
  },
  fr: {
    namespaces: 'Espaces de noms',
    projects: 'Projets',
    versions: 'Versions',
    upload: 'Téléverser',
    delete: 'Supprimer',
    create: 'Créer',
    name: 'Nom',
    version: 'Version',
    locale: 'Locale',
    latest: 'dernière',
    setLatest: 'Définir comme dernière',
    noNamespaces: 'Aucun espace de noms trouvé.',
    noProjects: 'Aucun projet trouvé.',
    noVersions: 'Aucune version trouvée.',
    uploadTitle: 'Téléverser la documentation',
    uploadSuccess: 'Téléversement réussi.',
    uploadError: 'Échec du téléversement.',
    loginRequired:
      'Connexion requise pour les opérations d\'écriture.',
    authToken: 'Jeton Bearer',
    login: 'Définir le jeton',
    logout: 'Effacer le jeton',
    loginWithOidc: 'Connexion via OIDC',
    localeShown: 'Locale affichée: {locale}',
    fallbackNotice:
      'Locale demandée non disponible. Affichage: {locale}',
    back: 'Retour',
    cancel: 'Annuler',
    selectVersion: 'Sélectionner la version',
    selectLocale: 'Sélectionner la locale',
    language: 'Langue',
    markAsLatest: 'Marquer comme dernière',
    isLatest: 'Est la dernière',
    viewDocs: 'Voir la doc',
    publicRead: 'Lecture publique',
    createdBy: 'Créé par : {creator}',
    takeOwnership: 'Prendre possession',
    dragPanel: 'Faire glisser pour repositionner',
    devModeNotice:
      'L\'aperçu de la documentation n\'est pas disponible'
      + ' en mode dev. nginx est requis pour servir les'
      + ' fichiers statiques.',
    userManual: 'Manuel utilisateur',
    manualBrowsing: 'Parcourir la documentation',
    manualBrowsingText:
      'Ouvrez l\'application dans un navigateur. La page'
      + ' d\'accueil liste les espaces de noms accessibles.',
    manualAuthentication: 'Authentification',
    manualAuthText:
      'Les opérations protégées nécessitent un jeton Bearer'
      + ' émis par le fournisseur OIDC configuré.',
    manualAuthStep1:
      'Cliquez sur le bouton Connexion en haut à droite.',
    manualAuthStep2:
      'Si OIDC est configuré, cliquez sur "Connexion via'
      + ' OIDC" pour être redirigé vers le fournisseur.',
    manualAuthStep3:
      'Après authentification, vous êtes redirigé et'
      + ' connecté automatiquement.',
    manualAuthDev:
      'Pour le développement local, collez directement un'
      + ' jeton Bearer dans le champ de texte.',
    manualUpload: 'Téléverser de la documentation',
    manualUploadText:
      'Naviguez vers un projet, puis cliquez sur'
      + ' Téléverser. L\'archive ZIP doit respecter:',
    manualUploadRule1:
      'Contient index.html à la racine de l\'archive',
    manualUploadRule2: 'Pas d\'entrées de traversal (..)',
    manualUploadRule3: 'Pas de liens symboliques',
    manualUploadRule4: 'Maximum 500 fichiers',
    manualUploadRule5: 'Maximum 500 Mo extraits',
    manualUploadCurl: 'Exemple : upload via curl',
    manualClientCredentials: 'Uploads automatisés (CI/CD)',
    manualClientCredentialsText:
      'Utilisez le flux client-credentials OAuth2 pour'
      + ' obtenir un jeton pour les uploads automatisés:',
    manualClientCredentialsCurl: 'Obtenir un jeton:',
    manualClientCredentialsWarning:
      'Limitation connue (alpha) : avec le flux'
      + ' client-credentials, les droits ACL peuvent ne'
      + ' pas correspondre aux utilisateurs humains.',
    manualAcl: 'Contrôle d\'accès (ACL)',
    manualAclText:
      'Chaque espace de noms contient un fichier'
      + ' namespace.toml qui contrôle les accès.',
    manualAclAlphaNotice:
      'Limitation alpha : les rôles ACL ne peuvent pas'
      + ' encore être modifiés via l\'API.',
  },
  de: {
    namespaces: 'Namensräume',
    projects: 'Projekte',
    versions: 'Versionen',
    upload: 'Hochladen',
    delete: 'Löschen',
    create: 'Erstellen',
    name: 'Name',
    version: 'Version',
    locale: 'Sprachversion',
    latest: 'aktuell',
    setLatest: 'Als aktuell markieren',
    noNamespaces: 'Keine Namensräume gefunden.',
    noProjects: 'Keine Projekte gefunden.',
    noVersions: 'Keine Versionen gefunden.',
    uploadTitle: 'Dokumentation hochladen',
    uploadSuccess: 'Hochladen erfolgreich.',
    uploadError: 'Hochladen fehlgeschlagen.',
    loginRequired:
      'Anmeldung für Schreibvorgänge erforderlich.',
    authToken: 'Bearer-Token',
    login: 'Token setzen',
    logout: 'Token löschen',
    loginWithOidc: 'Mit OIDC anmelden',
    localeShown: 'Angezeigte Sprachversion: {locale}',
    fallbackNotice:
      'Angefragte Sprachversion nicht verfügbar. Anzeige: {locale}',
    back: 'Zurück',
    cancel: 'Abbrechen',
    selectVersion: 'Version auswählen',
    selectLocale: 'Sprachversion auswählen',
    language: 'Sprache',
    markAsLatest: 'Als aktuell markieren',
    isLatest: 'Ist aktuell',
    viewDocs: 'Dokumentation anzeigen',
    publicRead: 'Öffentlich lesbar',
    createdBy: 'Erstellt von: {creator}',
    takeOwnership: 'Eigentümer werden',
    dragPanel: 'Ziehen zum Verschieben',
    devModeNotice:
      'Die Dokumentationsvorschau ist im Dev-Server'
      + ' nicht verfügbar. nginx wird benötigt, um'
      + ' statische Dateien zu liefern.',
    userManual: 'Benutzerhandbuch',
    manualBrowsing: 'Dokumentation durchsuchen',
    manualBrowsingText:
      'Öffnen Sie die Anwendung im Browser. Die'
      + ' Startseite listet alle zugänglichen Namensräume.',
    manualAuthentication: 'Authentifizierung',
    manualAuthText:
      'Geschützte Operationen erfordern ein Bearer-Token'
      + ' vom konfigurierten OIDC-Anbieter.',
    manualAuthStep1:
      'Klicken Sie oben rechts auf Anmelden.',
    manualAuthStep2:
      'Wenn OIDC konfiguriert ist, klicken Sie auf'
      + ' "Mit OIDC anmelden".',
    manualAuthStep3:
      'Nach der Authentifizierung werden Sie automatisch'
      + ' zurückgeleitet und angemeldet.',
    manualAuthDev:
      'Für lokale Entwicklung können Sie ein Bearer-Token'
      + ' direkt in das Textfeld einfügen.',
    manualUpload: 'Dokumentation hochladen',
    manualUploadText:
      'Navigieren Sie zu einem Projekt und klicken Sie'
      + ' auf Hochladen. Das ZIP-Archiv muss erfüllen:',
    manualUploadRule1:
      'Enthält index.html im Archivstamm',
    manualUploadRule2: 'Keine Pfad-Traversal-Einträge (..)',
    manualUploadRule3: 'Keine symbolischen Links',
    manualUploadRule4: 'Maximal 500 Dateien',
    manualUploadRule5:
      'Maximal 500 MB entpackte Größe',
    manualUploadCurl: 'Beispiel: Upload per curl',
    manualClientCredentials:
      'Automatisierte Uploads (CI/CD)',
    manualClientCredentialsText:
      'Nutzen Sie den OAuth2 Client-Credentials-Fluss für'
      + ' automatisierte Uploads:',
    manualClientCredentialsCurl: 'Token abrufen:',
    manualClientCredentialsWarning:
      'Bekannte Einschränkung (Alpha): Im'
      + ' Client-Credentials-Fluss stimmen die Rollen'
      + ' möglicherweise nicht mit menschlichen Nutzern'
      + ' überein.',
    manualAcl: 'Zugriffskontrolle (ACL)',
    manualAclText:
      'Jeder Namensraum enthält eine namespace.toml,'
      + ' die den Zugriff steuert.',
    manualAclAlphaNotice:
      'Alpha-Einschränkung: ACL-Rollen können noch nicht'
      + ' über die API geändert werden.',
  },
}

export default createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages,
})
