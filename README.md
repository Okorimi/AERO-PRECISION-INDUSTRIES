# AERO PRECISION INDUSTRIES

Application Streamlit de management des risques AMDEC pour l'usinage aéronautique (ISO 31000, ISO 31010, EN 9100).

## Lancer l'application

Prérequis : Python 3.10 ou plus récent.

- **Windows** : double-cliquez sur `lancer.bat`.
- **macOS ou Linux** : exécutez `bash lancer.sh`.

Le premier lancement crée un environnement `.venv` et installe les dépendances, ce qui demande quelques minutes et une connexion Internet. L'application s'ouvre ensuite sur <http://localhost:8501>.

Lancement manuel :

```bash
python -m venv .venv
# Windows : .venv\Scripts\activate       macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Si Streamlit demande une adresse e-mail dans le terminal, appuyez sur Entrée.

**Connexion de démonstration** : `youssouf_aero` / `aero_20262027`, à saisir manuellement. Cochez « Se souvenir de moi » pour rester connecté 30 jours sur ce navigateur.

## Image de fond de l'accueil

La page d'accueil charge l'image depuis son lien LinkedIn, ce qui demande Internet. Pour une démonstration fiable ou hors ligne, enregistrez l'image sous `static/fond_accueil.jpg` : ce fichier est alors utilisé en priorité. Son intensité se règle avec `OPACITE_FOND_ACCUEIL` dans `aero/config.py`. Vérifiez vos droits d'utilisation avant toute mise en ligne publique.

## Utiliser votre vrai registre CSV

Le sujet YaneCode cite `guihini_abakar_youssouf.csv`. Ce fichier n'était pas fourni : la page **Registre 2023-2026** affiche donc `data/registre_demo_simule.csv`, un jeu **simulé** signalé par un bandeau.

Pour le remplacer, au choix :

1. copiez `guihini_abakar_youssouf.csv` dans le dossier `data/`, puis rechargez la page ;
2. importez-le depuis la page, dans le bloc « Source ».

Le fichier doit contenir les colonnes listées dans le sujet. Le séparateur, l'encodage, les dates françaises et les virgules décimales sont détectés. Si une colonne manque, l'application la nomme et conserve le registre précédent. Le détail du nettoyage figure dans l'onglet **Données**.

Le bandeau disparaît avec le vrai fichier. Ne présentez pas les chiffres ni la conclusion du jeu simulé comme des résultats réels.

## Scénario de démonstration conseillé

1. Connectez-vous : les KPI affichent 5 / 3 / 0 / 213, et le graphique avant / après montre une réduction globale moyenne de 74 %.
2. Sur le tableau de bord, passez l'action de R01 à « Terminé » : son NPR′ étant de 48, le KPI « Risques maîtrisés » passe à 1.
3. Cliquez sur « Gérer », onglet « Réévaluation », pour modifier G′, O′ ou D′ en direct.
4. Montrez la matrice en vue « Après actions », puis le Kanban en faisant glisser une carte.

Dans la barre latérale, **Données de démo** recharge l'étude de cas (5 risques) ou le portefeuille atelier (12 risques), et remet les données à zéro.

## Structure

| Élément | Rôle |
|---|---|
| `app.py` | Point d'entrée : contrôle d'accès, navigation, barre latérale |
| `views/` | Une page par fichier |
| `aero/scoring.py` | Règles de calcul NPR, niveaux, maîtrise |
| `aero/store.py` | Base SQLite unique, lue par toutes les pages |
| `aero/seed.py` | Jeux de démonstration |
| `aero/registry.py` | Chargement, nettoyage, KPI et conclusions du registre CSV |
| `aero/charts.py` | Graphiques Plotly |
| `aero/ui.py`, `aero/style.css` | Composants et design |
| `static/fonts/` | Space Grotesk et Inter, embarquées pour fonctionner hors ligne |
| `scripts/generer_registre_demo.py` | Régénère le registre simulé |
| `tests/` | Tests automatisés (`pip install -r requirements-dev.txt`, puis `pytest`) |

## Mise en ligne sur Streamlit Community Cloud

1. Publiez ce dossier sur un dépôt GitHub. Le fichier `.gitignore` exclut la base locale et les secrets.
2. Sur <https://share.streamlit.io>, créez une application avec `app.py` comme fichier principal.
3. Dans **Settings > Secrets**, collez le contenu de `.streamlit/secrets.toml.example`, puis changez le mot de passe et `cookie_secret`.

## Limites à connaître

- La connexion est une barrière de démonstration, sans gestion de comptes. Elle ne convient pas à des données réelles sensibles.
- La base SQLite est partagée par tous les visiteurs. Sur Community Cloud, elle est réinitialisée à chaque redémarrage du serveur.
- Sans « Se souvenir de moi », actualiser le navigateur ramène à la page d'accueil.
