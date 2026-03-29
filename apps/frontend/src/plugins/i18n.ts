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
    login: 'Login',
    logout: 'Logout',
    setToken: 'Set token',
    loginWithOidc: 'Login with OIDC',
    localeShown: 'Showing locale: {locale}',
    fallbackNotice: 'Requested locale not available. Showing: {locale}',
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
      'Documentation preview is not available in the' +
      ' dev server. nginx is required to serve static' +
      ' documentation files.',
    userManual: 'User Manual',
    manualBrowsing: 'Browsing Documentation',
    manualBrowsingText:
      'Open the application in a browser. The home page' +
      ' lists all namespaces you have access to. Select' +
      ' a namespace to see its projects, then select a' +
      ' project to see available versions. Select a' +
      ' version and locale to open the documentation' +
      ' viewer.',
    manualAuthentication: 'Authentication',
    manualAuthText:
      'Protected operations require a Bearer token issued' + ' by the configured OIDC provider.',
    manualAuthStep1: 'Click the Login button in the top-right corner.',
    manualAuthStep2:
      'If OIDC is configured, click "Login with OIDC" to' +
      ' be redirected to the identity provider.',
    manualAuthStep3:
      'After authenticating, you are redirected back and' + ' logged in automatically.',
    manualAuthDev:
      'For local development, paste a raw Bearer token' + ' directly into the text field instead.',
    manualUpload: 'Uploading Documentation',
    manualUploadText:
      'Navigate to a project, then click Upload (visible' +
      ' only when authenticated with write access).' +
      ' The uploaded ZIP must satisfy these constraints:',
    manualUploadRule1: 'Contains index.html at the archive root',
    manualUploadRule2: 'No path-traversal (..) entries',
    manualUploadRule3: 'No symlink entries',
    manualUploadRule4: 'No more than 500 files',
    manualUploadRule5: 'No more than 500 MB extracted size',
    manualUploadCurl: 'Example: upload via curl',
    manualClientCredentials: 'Automated Uploads (CI/CD)',
    manualClientCredentialsText:
      'Use the OAuth2 client-credentials grant to obtain' + ' a token for automated uploads:',
    manualClientCredentialsCurl: 'Obtain a token:',
    manualClientCredentialsWarning:
      'Known limitation (alpha): when using a' +
      ' client-credentials flow, the service account' +
      ' may not have roles matching human users. ACL' +
      ' entries set via this flow may not grant access' +
      ' to other users. Use a device-code flow to act' +
      ' on behalf of a user.',
    manualAcl: 'Access Control (ACL)',
    manualAclText:
      'Each namespace has a namespace.toml file that' +
      ' controls who can read and write. Roles are' +
      ' matched exactly against JWT role claims.',
    manualAclAlphaNotice:
      'ACL roles can be granted or revoked via the API' +
      ' or via the Manage Access button (shield icon)' +
      ' on each namespace.',
    browsable: 'Browsable',
    manageAccess: 'Manage Access',
    hiddenNamespacesNotice:
      'Some namespaces may be hidden. Sign in to see' + ' all namespaces you have access to.',
    aclForbidden: 'You do not have permission to manage access' + ' for this namespace.',
    aclNoRoles: 'None of your current roles appear in this' + " namespace's ACL.",
    aclRoleName: 'Role',
    aclCanRead: 'Can read',
    aclCanWrite: 'Can write',
    aclPublicReadHint:
      'Allow anyone to read documentation in this' + ' namespace without logging in.',
    aclBrowsableHint:
      'Allow anyone to browse namespaces, projects and' +
      ' versions without granting documentation access.',
    tabBrowsing: 'Browsing',
    tabAutomated: 'Automated Upload (CI/CD)',
    tabManual: 'Manual Upload',
    tabAcl: 'Access Control',
    tabLimitations: 'Limitations',
    configureExamples: 'Configure Examples',
    configureExamplesHint:
      'Enter your values to make the code examples' +
      ' copy-pastable. You can enter real values or' +
      ' environment variable names (e.g. $MY_VAR).',
    docrootUrl: 'Docroot URL',
    idpUrl: 'IDP / Token URL',
    idpUrlHint: 'e.g. https://keycloak.example.com/realms/myrealm',
    ciClientId: 'CI Client ID',
    ciClientIdHint: 'The service-account client configured in your IDP',
    ciClientSecret: 'Client Secret',
    ciClientSecretHint:
      'Or an env-var reference, e.g. $CLIENT_SECRET',
    targetNamespace: 'Namespace',
    targetProject: 'Project',
    manualAutomatedText:
      'Use the OAuth2 client-credentials grant for' +
      ' automated CI/CD uploads. Namespaces must be' +
      ' set up first, a role must have write access,' +
      ' and the service account used for automated' +
      ' uploads must have that role assigned.',
    manualAutomatedStep1:
      'Create a namespace and project (once, by an admin).',
    manualAutomatedStep2:
      'Create a role with write access in the namespace ACL.',
    manualAutomatedStep3:
      'Create a service account (confidential client with' +
      ' client credentials) in your IDP and assign it' +
      ' the role.',
    manualAutomatedStep4:
      'Use the client credentials flow in your pipeline' +
      ' to obtain a token, then upload the ZIP.',
    keycloakSetup: 'Keycloak Setup for CI/CD',
    keycloakSetupText:
      'To configure a service account for automated' +
      ' uploads in Keycloak:',
    keycloakStep1:
      'Create a confidential client (e.g. my-ci-client)' +
      ' with "Service accounts enabled" ON and' +
      ' "Client authentication" ON.',
    keycloakStep2:
      `Under the client's "Service accounts roles" tab,` +
      ' assign the role that has write access to the' +
      ' target namespace.',
    keycloakStep3:
      'Copy the client secret from the "Credentials" tab' +
      ' and store it in your CI/CD secret store.',
    manualLimitationsText:
      'This is an early beta release. The following' +
      ' limitations apply:',
    manualLimitationRole:
      'Role extraction is only implemented for Keycloak.' +
      ' OIDC authentication works with any standards-' +
      'compliant provider (Keycloak, Entra ID, Google),' +
      ' but ACL enforcement relies on role extraction' +
      ' which is currently Keycloak-specific. Support' +
      ' for other providers will be added on demand.',
    manualLimitationSearch:
      'There is no full-text search. Documentation is' +
      ' served as static files without indexing.',
    manualLimitationStorage:
      'Storage is filesystem-only. S3 and other object' +
      ' stores are not supported in this release.',
    githubRepo: 'Source code',
    buildCommit: 'Build',
    buildTime: 'Built at',
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
    loginRequired: "Connexion requise pour les opérations d'écriture.",
    authToken: 'Jeton Bearer',
    login: 'Connexion',
    logout: 'Déconnexion',
    setToken: 'Définir le jeton',
    loginWithOidc: 'Connexion via OIDC',
    localeShown: 'Locale affichée: {locale}',
    fallbackNotice: 'Locale demandée non disponible. Affichage: {locale}',
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
      "L'aperçu de la documentation n'est pas disponible" +
      ' en mode dev. nginx est requis pour servir les' +
      ' fichiers statiques.',
    userManual: 'Manuel utilisateur',
    manualBrowsing: 'Parcourir la documentation',
    manualBrowsingText:
      "Ouvrez l'application dans un navigateur. La page" +
      " d'accueil liste les espaces de noms accessibles.",
    manualAuthentication: 'Authentification',
    manualAuthText:
      'Les opérations protégées nécessitent un jeton Bearer' +
      ' émis par le fournisseur OIDC configuré.',
    manualAuthStep1: 'Cliquez sur le bouton Connexion en haut à droite.',
    manualAuthStep2:
      'Si OIDC est configuré, cliquez sur "Connexion via' +
      ' OIDC" pour être redirigé vers le fournisseur.',
    manualAuthStep3: 'Après authentification, vous êtes redirigé et' + ' connecté automatiquement.',
    manualAuthDev:
      'Pour le développement local, collez directement un' +
      ' jeton Bearer dans le champ de texte.',
    manualUpload: 'Téléverser de la documentation',
    manualUploadText:
      'Naviguez vers un projet, puis cliquez sur' + " Téléverser. L'archive ZIP doit respecter:",
    manualUploadRule1: "Contient index.html à la racine de l'archive",
    manualUploadRule2: "Pas d'entrées de traversal (..)",
    manualUploadRule3: 'Pas de liens symboliques',
    manualUploadRule4: 'Maximum 500 fichiers',
    manualUploadRule5: 'Maximum 500 Mo extraits',
    manualUploadCurl: 'Exemple : upload via curl',
    manualClientCredentials: 'Uploads automatisés (CI/CD)',
    manualClientCredentialsText:
      'Utilisez le flux client-credentials OAuth2 pour' +
      ' obtenir un jeton pour les uploads automatisés:',
    manualClientCredentialsCurl: 'Obtenir un jeton:',
    manualClientCredentialsWarning:
      'Limitation connue (alpha) : avec le flux' +
      ' client-credentials, les droits ACL peuvent ne' +
      ' pas correspondre aux utilisateurs humains.',
    manualAcl: "Contrôle d'accès (ACL)",
    manualAclText:
      'Chaque espace de noms contient un fichier' + ' namespace.toml qui contrôle les accès.',
    manualAclAlphaNotice:
      'Les rôles ACL peuvent être accordés ou révoqués' +
      " via l'API ou via le bouton Gérer l'accès" +
      ' (icône bouclier) sur chaque espace de noms.',
    browsable: 'Consultable',
    manageAccess: "Gérer l'accès",
    hiddenNamespacesNotice:
      'Certains espaces de noms peuvent être masqués.' +
      ' Connectez-vous pour voir tous ceux auxquels' +
      ' vous avez accès.',
    aclForbidden: "Vous n'avez pas la permission de gérer" + " l'accès à cet espace de noms.",
    aclNoRoles: "Aucun de vos rôles actuels n'apparaît dans" + " l'ACL de cet espace de noms.",
    aclRoleName: 'Rôle',
    aclCanRead: 'Peut lire',
    aclCanWrite: 'Peut écrire',
    aclPublicReadHint:
      'Autoriser tout le monde à lire la documentation' +
      ' de cet espace de noms sans se connecter.',
    aclBrowsableHint:
      'Autoriser tout le monde à parcourir les espaces' +
      ' de noms, projets et versions sans accéder à' +
      ' la documentation.',
    tabBrowsing: 'Navigation',
    tabAutomated: 'Upload automatisé (CI/CD)',
    tabManual: 'Upload manuel',
    tabAcl: "Contrôle d'accès",
    tabLimitations: 'Limitations',
    configureExamples: 'Configurer les exemples',
    configureExamplesHint:
      'Entrez vos valeurs pour rendre les exemples de' +
      ' code copiables. Vous pouvez entrer des valeurs' +
      " réelles ou des noms de variables d'environnement" +
      ' (ex. $MA_VARIABLE).',
    docrootUrl: 'URL Docroot',
    idpUrl: 'URL IDP / Token',
    idpUrlHint:
      'ex. https://keycloak.example.com/realms/myrealm',
    ciClientId: 'ID client CI',
    ciClientIdHint:
      'Le client compte de service configuré dans votre IDP',
    ciClientSecret: 'Secret client',
    ciClientSecretHint:
      'Ou une référence de variable, ex. $CLIENT_SECRET',
    targetNamespace: 'Espace de noms',
    targetProject: 'Projet',
    manualAutomatedText:
      'Utilisez le flux client-credentials OAuth2 pour' +
      ' les uploads CI/CD automatisés. Les espaces de' +
      ' noms doivent être créés au préalable, un rôle' +
      ' doit avoir un accès en écriture, et le compte de' +
      ' service doit avoir ce rôle.',
    manualAutomatedStep1:
      'Créez un espace de noms et un projet (une fois,' +
      ' par un administrateur).',
    manualAutomatedStep2:
      "Créez un rôle avec accès en écriture dans l'ACL" +
      " de l'espace de noms.",
    manualAutomatedStep3:
      'Créez un compte de service (client confidentiel' +
      ' avec client credentials) dans votre IDP et' +
      ' attribuez-lui le rôle.',
    manualAutomatedStep4:
      'Utilisez le flux client credentials dans votre' +
      ' pipeline pour obtenir un jeton, puis uploadez' +
      ' le ZIP.',
    keycloakSetup: 'Configuration Keycloak pour CI/CD',
    keycloakSetupText:
      'Pour configurer un compte de service pour les' +
      ' uploads automatisés dans Keycloak :',
    keycloakStep1:
      'Créez un client confidentiel (ex. my-ci-client)' +
      ' avec "Comptes de service activés" ON et' +
      ' "Authentification client" ON.',
    keycloakStep2:
      `Dans l'onglet "Rôles des comptes de service"` +
      ' du client, attribuez le rôle ayant un accès' +
      " en écriture à l'espace de noms cible.",
    keycloakStep3:
      "Copiez le secret client depuis l'onglet" +
      ` "Informations d'identification" et stockez-le` +
      ' dans le magasin de secrets CI/CD.',
    manualLimitationsText:
      "Il s'agit d'une première version bêta." +
      " Les limitations suivantes s'appliquent :",
    manualLimitationRole:
      "L'extraction des rôles est uniquement implémentée" +
      " pour Keycloak. L'authentification OIDC fonctionne" +
      ' avec tout fournisseur conforme (Keycloak, Entra' +
      " ID, Google), mais l'application des ACL repose" +
      " sur l'extraction des rôles, actuellement" +
      " spécifique à Keycloak. Le support d'autres" +
      ' fournisseurs sera ajouté à la demande.',
    manualLimitationSearch:
      "Il n'y a pas de recherche en texte intégral. La" +
      ' documentation est servie sous forme de fichiers' +
      ' statiques sans indexation.',
    manualLimitationStorage:
      'Le stockage est uniquement sur système de fichiers.' +
      ' S3 et autres objets de stockage ne sont pas' +
      ' pris en charge dans cette version.',
    githubRepo: 'Code source',
    buildCommit: 'Version du build',
    buildTime: 'Construit le',
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
    loginRequired: 'Anmeldung für Schreibvorgänge erforderlich.',
    authToken: 'Bearer-Token',
    login: 'Anmelden',
    logout: 'Abmelden',
    setToken: 'Token setzen',
    loginWithOidc: 'Mit OIDC anmelden',
    localeShown: 'Angezeigte Sprachversion: {locale}',
    fallbackNotice: 'Angefragte Sprachversion nicht verfügbar. Anzeige: {locale}',
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
      'Die Dokumentationsvorschau ist im Dev-Server' +
      ' nicht verfügbar. nginx wird benötigt, um' +
      ' statische Dateien zu liefern.',
    userManual: 'Benutzerhandbuch',
    manualBrowsing: 'Dokumentation durchsuchen',
    manualBrowsingText:
      'Öffnen Sie die Anwendung im Browser. Die' +
      ' Startseite listet alle zugänglichen Namensräume.',
    manualAuthentication: 'Authentifizierung',
    manualAuthText:
      'Geschützte Operationen erfordern ein Bearer-Token' + ' vom konfigurierten OIDC-Anbieter.',
    manualAuthStep1: 'Klicken Sie oben rechts auf Anmelden.',
    manualAuthStep2: 'Wenn OIDC konfiguriert ist, klicken Sie auf' + ' "Mit OIDC anmelden".',
    manualAuthStep3:
      'Nach der Authentifizierung werden Sie automatisch' + ' zurückgeleitet und angemeldet.',
    manualAuthDev:
      'Für lokale Entwicklung können Sie ein Bearer-Token' + ' direkt in das Textfeld einfügen.',
    manualUpload: 'Dokumentation hochladen',
    manualUploadText:
      'Navigieren Sie zu einem Projekt und klicken Sie' +
      ' auf Hochladen. Das ZIP-Archiv muss erfüllen:',
    manualUploadRule1: 'Enthält index.html im Archivstamm',
    manualUploadRule2: 'Keine Pfad-Traversal-Einträge (..)',
    manualUploadRule3: 'Keine symbolischen Links',
    manualUploadRule4: 'Maximal 500 Dateien',
    manualUploadRule5: 'Maximal 500 MB entpackte Größe',
    manualUploadCurl: 'Beispiel: Upload per curl',
    manualClientCredentials: 'Automatisierte Uploads (CI/CD)',
    manualClientCredentialsText:
      'Nutzen Sie den OAuth2 Client-Credentials-Fluss für' + ' automatisierte Uploads:',
    manualClientCredentialsCurl: 'Token abrufen:',
    manualClientCredentialsWarning:
      'Bekannte Einschränkung (Alpha): Im' +
      ' Client-Credentials-Fluss stimmen die Rollen' +
      ' möglicherweise nicht mit menschlichen Nutzern' +
      ' überein.',
    manualAcl: 'Zugriffskontrolle (ACL)',
    manualAclText: 'Jeder Namensraum enthält eine namespace.toml,' + ' die den Zugriff steuert.',
    manualAclAlphaNotice:
      'ACL-Rollen können über die API oder über die' +
      ' Schaltfläche Zugriff verwalten (Schild-Symbol)' +
      ' an jedem Namensraum verwaltet werden.',
    browsable: 'Auflistbar',
    manageAccess: 'Zugriff verwalten',
    hiddenNamespacesNotice:
      'Einige Namensräume können ausgeblendet sein.' +
      ' Melden Sie sich an, um alle zugänglichen' +
      ' Namensräume zu sehen.',
    aclForbidden:
      'Sie haben keine Berechtigung, den Zugriff' + ' für diesen Namensraum zu verwalten.',
    aclNoRoles: 'Keiner Ihrer aktuellen Rollen taucht in der' + ' ACL dieses Namensraums auf.',
    aclRoleName: 'Rolle',
    aclCanRead: 'Kann lesen',
    aclCanWrite: 'Kann schreiben',
    aclPublicReadHint:
      'Erlaubt jedem, die Dokumentation in diesem' + ' Namensraum ohne Anmeldung zu lesen.',
    aclBrowsableHint:
      'Erlaubt jedem, Namensräume, Projekte und' +
      ' Versionen zu durchsuchen, ohne Zugriff auf' +
      ' die Dokumentation zu erhalten.',
    tabBrowsing: 'Durchsuchen',
    tabAutomated: 'Automatisierter Upload (CI/CD)',
    tabManual: 'Manueller Upload',
    tabAcl: 'Zugriffskontrolle',
    tabLimitations: 'Einschränkungen',
    configureExamples: 'Beispiele konfigurieren',
    configureExamplesHint:
      'Geben Sie Ihre Werte ein, damit die' +
      ' Code-Beispiele direkt kopierbar sind.' +
      ' Sie können echte Werte oder Namen von' +
      ' Umgebungsvariablen angeben (z.B. $MEINE_VAR).',
    docrootUrl: 'Docroot-URL',
    idpUrl: 'IDP / Token-URL',
    idpUrlHint:
      'z.B. https://keycloak.example.com/realms/myrealm',
    ciClientId: 'CI Client-ID',
    ciClientIdHint:
      'Der Dienstkonto-Client in Ihrem IDP',
    ciClientSecret: 'Client-Secret',
    ciClientSecretHint:
      'Oder eine Umgebungsvariable, z.B. $CLIENT_SECRET',
    targetNamespace: 'Namensraum',
    targetProject: 'Projekt',
    manualAutomatedText:
      'Verwenden Sie den OAuth2 Client-Credentials-Fluss' +
      ' für automatisierte CI/CD-Uploads. Namensräume' +
      ' müssen zuerst eingerichtet werden, eine Rolle' +
      ' muss Schreibzugriff haben und das Dienstkonto' +
      ' muss diese Rolle haben.',
    manualAutomatedStep1:
      'Erstellen Sie einen Namensraum und ein Projekt' +
      ' (einmalig, durch einen Administrator).',
    manualAutomatedStep2:
      'Erstellen Sie eine Rolle mit Schreibzugriff' +
      ' in der Namespace-ACL.',
    manualAutomatedStep3:
      'Erstellen Sie ein Dienstkonto (vertraulicher' +
      ' Client mit Client Credentials) in Ihrem IDP' +
      ' und weisen Sie ihm die Rolle zu.',
    manualAutomatedStep4:
      'Verwenden Sie den Client-Credentials-Fluss in' +
      ' Ihrer Pipeline, um ein Token zu erhalten,' +
      ' und laden Sie dann das ZIP hoch.',
    keycloakSetup: 'Keycloak-Einrichtung für CI/CD',
    keycloakSetupText:
      'So konfigurieren Sie ein Dienstkonto für' +
      ' automatisierte Uploads in Keycloak:',
    keycloakStep1:
      'Erstellen Sie einen vertraulichen Client' +
      ' (z.B. my-ci-client) mit aktivierten' +
      ' "Dienstkonten" und "Client-Authentifizierung".',
    keycloakStep2:
      'Weisen Sie im Tab "Dienstkonto-Rollen" des Clients' +
      ' die Rolle zu, die Schreibzugriff auf den' +
      ' Ziel-Namensraum hat.',
    keycloakStep3:
      'Kopieren Sie das Client-Secret aus dem' +
      ' "Anmeldeinformationen"-Tab und speichern Sie es' +
      ' in Ihrem CI/CD-Secret-Speicher.',
    manualLimitationsText:
      'Dies ist eine frühe Beta-Version.' +
      ' Folgende Einschränkungen gelten:',
    manualLimitationRole:
      'Die Rollenextraktion ist nur für Keycloak' +
      ' implementiert. Die OIDC-Authentifizierung' +
      ' funktioniert mit jedem konformen Anbieter' +
      ' (Keycloak, Entra ID, Google), aber die' +
      ' ACL-Durchsetzung basiert auf der Rollenextraktion,' +
      ' die derzeit Keycloak-spezifisch ist. Unterstützung' +
      ' für andere Anbieter wird nach Bedarf hinzugefügt.',
    manualLimitationSearch:
      'Es gibt keine Volltextsuche. Die Dokumentation' +
      ' wird als statische Dateien ohne Indizierung' +
      ' bereitgestellt.',
    manualLimitationStorage:
      'Der Speicher ist nur dateisystembasiert. S3 und' +
      ' andere Objektspeicher werden in dieser Version' +
      ' nicht unterstützt.',
    githubRepo: 'Quellcode',
    buildCommit: 'Build-Version',
    buildTime: 'Erstellt am',
  },
}

export default createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages,
})
