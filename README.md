# RADIO-BOT

## Introduction
Le projet RADIO-BOT est un projet personnel permettant d'expérimenter le langage python et la technologie des bots discord.

## Installation (Debian)
### Prérequis
- Python 3.8 minimum

### Dépendances
- asyncio
- discord
- pynacl
- yt_dlp

### Environnement virtuel

Créez l'environnement dans un répertoire de votre choix
```bash
$ python3 -m venv .venv
```

Activez l'environnement
```bash
$ sudo chmod u+x .venv/bin/activate
$ ./.venv/bin/activate
```

Installez les dépendances
```bash
$ ./.venv/bin/pip install asyncio discord pynacl yt_dlp
```

Créez le fichier .env à partir du fichier donné en exemple
```bash
$ cp .env.example .env
```

Copiez votre TOKEN_BOT dans le fichier .env, plus d'informations sur où trouver votre token ici : https://discord.com/developers/docs/quick-start/getting-started#step-1-creating-an-app
```bash
$ sed -i 's/TOKEN="[^"]*"/TOKEN="votre_token"/g' .env
```

### Utilisation (Debian)

Lancer le bot
```bash
./.venv/bin/python main.py
```

## Copyright
99% du code source a été généré par IA et des modifications y ont été effectuées afin d'améliorer le code généré, représentant le 1% restant.
Ainsi, je ne me considère pas et ne peut être considéré comme le propriétaire du code source de ce projet puisqu'il a été créé à partir des nombreux codes sources utilisés pour former le modèle de l'IA.