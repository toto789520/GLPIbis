import os

print("=== VERIFICATION DES FICHIERS ===")

# Vérifier si app.py existe
if os.path.exists('app.py'):
    print("✓ app.py existe")
    
    # Lire le contenu
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Taille du fichier: {len(content)} caractères")
    print("Premières lignes du fichier:")
    print("-" * 40)
    print(content[:500])
    print("-" * 40)
    
    # Vérifier les imports critiques
    critical_imports = ['from flask import Flask', 'from flask import render_template']
    for imp in critical_imports:
        if imp in content:
            print(f"✓ Import trouvé: {imp}")
        else:
            print(f"✗ Import manquant: {imp}")
    
    # Vérifier les routes critiques
    if '@app.route(\'/login\')' in content or '@app.route("/login")' in content:
        print("✓ Route /login trouvée")
    else:
        print("✗ Route /login manquante")
        
    if 'app.run(' in content:
        print("✓ app.run() trouvé")
    else:
        print("✗ app.run() manquant")

else:
    print("✗ app.py n'existe pas dans le répertoire courant")
    print("Fichiers présents:")
    for f in os.listdir('.'):
        if f.endswith('.py'):
            print(f"  - {f}")
