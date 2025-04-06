import qrcode
from PIL import Image
import os
import cv2
import numpy as np
from datetime import datetime

class QRCodeService:
    def __init__(self, static_folder):
        self.qr_folder = os.path.join(static_folder, 'qr_codes')
        if not os.path.exists(self.qr_folder):
            os.makedirs(self.qr_folder)

    def generate_qr_code(self, hardware_id, info):
        """Génère un QR code pour un équipement"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Créer l'URL pour accéder aux détails de l'équipement
        data = f"http://localhost:5000/inventory/hardware/{hardware_id}"
        qr.add_data(data)
        qr.make(fit=True)

        # Créer l'image QR
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Ajouter les informations sous le QR code
        # Créer une nouvelle image plus grande pour accueillir le QR code et le texte
        final_img = Image.new('RGB', (qr_image.pixel_size, qr_image.pixel_size + 50), 'white')
        final_img.paste(qr_image, (0, 0))
        
        # Sauvegarder l'image
        filename = f"qr_{hardware_id}_{datetime.now().strftime('%Y%m%d')}.png"
        filepath = os.path.join(self.qr_folder, filename)
        final_img.save(filepath)
        
        return filename

    def get_qr_info(self, image_data):
        """Lit un QR code à partir d'une image"""
        # Convertir l'image en format OpenCV
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Initialiser le détecteur de QR code
        qr_detector = cv2.QRCodeDetector()
        
        # Détecter et décoder le QR code
        data, bbox, _ = qr_detector.detectAndDecode(img)
        
        if data:
            # Extraire l'ID de l'équipement de l'URL
            hardware_id = data.split('/')[-1]
            return hardware_id
        
        return None

    def generate_qr_label(self, hardware_info):
        """Génère une étiquette avec QR code pour l'impression"""
        # Créer une image plus grande pour l'étiquette
        label_width = 400
        label_height = 200
        label = Image.new('RGB', (label_width, label_height), 'white')
        
        # Générer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )
        qr.add_data(f"http://localhost:5000/inventory/hardware/{hardware_info['id']}")
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Ajouter le QR code à gauche de l'étiquette
        label.paste(qr_image, (10, 10))
        
        # Sauvegarder l'étiquette
        filename = f"label_{hardware_info['id']}_{datetime.now().strftime('%Y%m%d')}.png"
        filepath = os.path.join(self.qr_folder, filename)
        label.save(filepath)
        
        return filename