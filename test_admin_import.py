# Vérification que le blueprint admin est correctement configuré
try:
    from routes.admin import admin_bp
    print("Blueprint admin importé avec succès")
    
    # Vérifier que toutes les routes sont définies
    for rule in admin_bp.url_map.iter_rules():
        print(f"Route admin trouvée: {rule.rule} -> {rule.endpoint}")
        
except Exception as e:
    print(f"Erreur lors de l'import du blueprint admin: {e}")
    import traceback
    traceback.print_exc()