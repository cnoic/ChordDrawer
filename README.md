# ChordDrawer
Afficheur de l'activité sur un réseau Chord (TP SD)

## Utilisation comme submodule

### Pour l'ajouter a votre repo:

```bash
git submodule add git@github.com:FoxtrotNSF/ChordDrawer.git
```

### Pour le mettre a jour:

```bash
git submodule update --remote
```

## Utilisation / Prérequis
### Dans le fichier `chord_tools.py`:
  - Importer le module: (Par exemple si le module est dans le dossier ChordDrawer)
  ```python
  from ChordDrawer.chord_drawer import *
  ```
  - Décorer la fonction json_send
  ```python
  @draw_activity
  def json_send(ip, port, data):
    ...
  ```
### Dans votre noeud chord (a l'initialisation du noeud, avant la boucle de reception)
  - Configurer le notifieur associé au noeud
  ```python
  notifier.configure_node([votre_ip],[port_du_noeud])
  ```
  - Pour enregistrer le premier Noeud a rejoindre le réseau (seulement le premier Noeud)
  ```python
  notifier.notify_first_node([votre_ip],[port_du_noeud],[cle_du_noeud])
  ```
  
  
# Fonctionnement
