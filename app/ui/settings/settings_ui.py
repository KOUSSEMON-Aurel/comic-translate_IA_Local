from PySide6 import QtWidgets
from app.ui.dayu_widgets.label import MLabel
from app.ui.dayu_widgets.check_box import MCheckBox
from app.ui.dayu_widgets.spin_box import MSpinBox
from PySide6.QtGui import QFontDatabase
import os

class SettingsTextRenderingWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        # Checkbox majuscule
        self.uppercase_checkbox = MCheckBox(self.tr("Render Text in UpperCase"))
        layout.addWidget(self.uppercase_checkbox)

        # Marge intérieure
        margin_layout = QtWidgets.QHBoxLayout()
        margin_label = MLabel(self.tr("Marge intérieure (px):"))
        self.margin_spinbox = MSpinBox().small()
        self.margin_spinbox.setFixedWidth(60)
        self.margin_spinbox.setMaximum(50)
        self.margin_spinbox.setValue(10) # Valeur par défaut
        margin_layout.addWidget(margin_label)
        margin_layout.addWidget(self.margin_spinbox)
        margin_layout.addStretch()
        layout.addLayout(margin_layout)

        # --- Correction : chargement des polices valides uniquement ---
        font_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'fonts'))
        font_files = [f for f in os.listdir(font_folder_path) if f.endswith((".ttf", ".ttc", ".otf", ".woff", ".woff2"))]
        font_families = set()
        for font_file in font_files:
            font_path = os.path.join(font_folder_path, font_file)
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    font_families.update(families)
                else:
                    print(f"[WARNING] Police non valide ou sans nom de famille : {font_file}")
            else:
                print(f"[WARNING] Impossible de charger la police : {font_file}")
        # Fallback si aucune police valide trouvée
        if not font_families:
            font_families.add("Roboto")
        # ... ici tu peux créer la combo box ou la logique d'utilisation des polices ...