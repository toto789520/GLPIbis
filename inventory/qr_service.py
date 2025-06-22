import qrcode
from PIL import Image, ImageDraw, ImageFont
import os
import cv2
import numpy as np
from datetime import datetime
import json

class QRCodeService:
    def __init__(self, static_folder):
        self.qr_folder = os.path.join(static_folder, 'qr_codes')
        if not os.path.exists(self.qr_folder):
            os.makedirs(self.qr_folder)

    def generate_qr_code(self, hardware_id, equipment_name=None):
        """Génère un QR code pour un équipement"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Créer les données JSON pour le QR code
        qr_data = {
            "id": hardware_id,
            "name": equipment_name or f"Equipment {hardware_id}",
            "url": f"http://localhost:5000/inventory/item/{hardware_id}",
            "serial": f"ERXDTCFGVH",  # Comme dans l'image
            "generated": datetime.now().isoformat()
        }
        
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)

        # Créer l'image QR
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Sauvegarder l'image
        filename = f"qr_{hardware_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.qr_folder, filename)
        qr_image.save(filepath)
        
        return filename

    def generate_qr_label(self, hardware_info):
        """Génère une étiquette complète avec QR code pour l'impression"""
        # Dimensions de l'étiquette
        label_width = 600
        label_height = 400
        
        # Créer l'image de base
        label = Image.new('RGB', (label_width, label_height), 'white')
        draw = ImageDraw.Draw(label)
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        
        qr_data = {
            "id": hardware_info.get('id'),
            "name": hardware_info.get('name', 'Unknown'),
            "url": f"http://localhost:5000/inventory/item/{hardware_info.get('id')}",
            "serial": hardware_info.get('serial', 'N/A'),
            "category": hardware_info.get('category', 'Serveur'),
            "location": hardware_info.get('location', 'A301'),
            "status": hardware_info.get('status', 'Actif')
        }
        
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Redimensionner le QR code
        qr_size = 150
        qr_image = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Ajouter le QR code à l'étiquette
        qr_x = 20
        qr_y = 50
        label.paste(qr_image, (qr_x, qr_y))
        
        try:
            # Essayer d'utiliser une police système
            font_title = ImageFont.truetype("arial.ttf", 16)
            font_text = ImageFont.truetype("arial.ttf", 12)
            font_small = ImageFont.truetype("arial.ttf", 10)
        except:
            # Utiliser la police par défaut si arial n'est pas disponible
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Ajouter le titre
        title = hardware_info.get('name', 'serveur test')
        draw.text((200, 30), title, fill='black', font=font_title)
        
        # Ajouter les informations à droite du QR code
        info_x = 200
        info_y = 60
        line_height = 20
        
        # Informations générales
        draw.text((info_x, info_y), "Informations générales", fill='#4A90E2', font=font_text)
        info_y += line_height + 5
        
        draw.text((info_x, info_y), f"Nom: {qr_data['name']}", fill='black', font=font_small)
        info_y += line_height
        
        draw.text((info_x, info_y), f"Catégorie: {qr_data['category']}", fill='black', font=font_small)
        info_y += line_height
        
        draw.text((info_x, info_y), f"Emplacement: {qr_data['location']}", fill='black', font=font_small)
        info_y += line_height
        
        draw.text((info_x, info_y), f"Statut: {qr_data['status']}", fill='black', font=font_small)
        info_y += line_height + 10
        
        # Informations techniques
        draw.text((info_x, info_y), "Informations techniques", fill='#4A90E2', font=font_text)
        info_y += line_height + 5
        
        draw.text((info_x, info_y), f"N° de série: {qr_data['serial']}", fill='black', font=font_small)
        info_y += line_height
        
        draw.text((info_x, info_y), f"Date d'achat: {hardware_info.get('purchase_date', '2025-06-06')}", fill='black', font=font_small)
        info_y += line_height
        
        draw.text((info_x, info_y), f"Fin de garantie: {hardware_info.get('warranty_end', '2028-06-06')}", fill='black', font=font_small)
        info_y += line_height
        
        draw.text((info_x, info_y), f"Ajouté le: {hardware_info.get('created_at', '2025-06-19 07:29:22')}", fill='black', font=font_small)
        
        # Ajouter une bordure
        draw.rectangle([(0, 0), (label_width-1, label_height-1)], outline='black', width=2)
        
        # Sauvegarder l'étiquette
        filename = f"label_{hardware_info.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.qr_folder, filename)
        label.save(filepath)
        
        return filename

    def get_qr_info(self, image_data):
        """Lit un QR code à partir d'une image"""
        try:
            # Convertir l'image en format OpenCV
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Initialiser le détecteur de QR code
            qr_detector = cv2.QRCodeDetector()
            
            # Détecter et décoder le QR code
            data, bbox, _ = qr_detector.detectAndDecode(img)
            
            if data:
                try:
                    # Essayer de parser les données JSON
                    qr_info = json.loads(data)
                    return qr_info.get('id')
                except json.JSONDecodeError:
                    # Si ce n'est pas du JSON, essayer d'extraire l'ID de l'URL
                    if '/inventory/item/' in data:
                        return data.split('/')[-1]
                    return data
            
            return None
        except Exception as e:
            print(f"Erreur lors de la lecture du QR code: {e}")
            return None