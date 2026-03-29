# Qu'est-ce que Docroot ?

**Docroot** est un serveur de documentation léger auto-hébergé.
Il stocke des archives de documentation versionnées (fichiers ZIP
contenant un `index.html`) et les sert via une interface web et
une API REST.

## Concepts clés

| Concept | Description |
|---|---|
| **Espace de noms** | Un regroupement de niveau supérieur — généralement une organisation ou une équipe. |
| **Projet** | Une source de documentation dans un espace de noms. |
| **Version** | Un instantané de la documentation pour une version donnée. |
| **Locale** | Une variante linguistique d'une version (`en`, `fr`, `de`, …). |

## Démarrage rapide

1. **Parcourir** — la page d'accueil liste les espaces de noms
   accessibles. Cliquez sur espace de noms → projet → version
   pour ouvrir la visionneuse.
2. **S'authentifier** — cliquez sur **Connexion** en haut à droite.
   Si OIDC est configuré, vous serez redirigé vers votre fournisseur
   d'identité. À votre retour, vous êtes connecté automatiquement.
3. **Téléverser** — accédez à un projet et cliquez sur **Téléverser**
   (visible après connexion avec accès en écriture). Le ZIP doit
   contenir un `index.html` à la racine.
4. **Automatiser** — utilisez l'API REST avec un token OAuth2
   [client-credentials](https://oauth.net/2/grant-types/client-credentials/)
   pour les pipelines CI/CD. Le Guide utilisateur contient des exemples curl.
