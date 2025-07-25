import json
import hashlib

from .base import OCREngine
from .microsoft_ocr import MicrosoftOCR
from .google_ocr import GoogleOCR
from .gpt_ocr import GPTOCR
from .paddle_ocr import PaddleOCREngine
from .manga_ocr.engine import MangaOCREngine
from .pororo.engine import PororoOCREngine
from .doctr_ocr import DocTROCR
from .gemini_ocr import GeminiOCR
from .easy_ocr import EasyOCREngine
from huggingface_hub import snapshot_download


from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path


# Fonction utilitaire pour charger le traducteur local à la demande
def get_local_translator(model_path=None):
    if not model_path:
        raise ValueError("Aucun chemin de modèle local HuggingFace n'a été fourni à get_local_translator.")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(str(model_path), local_files_only=True)
    return pipeline('translation', model=model, tokenizer=tokenizer, device=-1)

# SUPPRESSION DU TEST MANUEL

from PySide6 import QtWidgets

# --- TEST MINIMAL DE TRADUCTION LOCALE ---
if __name__ == "__main__":
    print("[TEST] Test minimal du pipeline de traduction HuggingFace local...")
    translator = get_local_translator()
    print(f"[TEST] Type pipeline: {type(translator)}")
    # Codes de langue NLLB-200: voir https://huggingface.co/facebook/nllb-200-distilled-600M#languages
    src = "fra_Latn"
    tgt = "eng_Latn"
    test_text = "Bonjour, comment vas-tu ?"
    try:
        result = translator(test_text, src_lang=src, tgt_lang=tgt, max_length=128)
        print(f"[TEST] Résultat pipeline: {result}")
        if result and isinstance(result, list) and 'translation_text' in result[0]:
            print(f"[TEST] Traduction: {result[0]['translation_text']}")
        else:
            print(f"[TEST] Format inattendu: {result}")
    except Exception as e:
        print(f"[TEST][CRITICAL] Erreur lors de la traduction: {e}")
from app.ui.dayu_widgets.label import MLabel
from app.ui.dayu_widgets.check_box import MCheckBox
from app.ui.dayu_widgets.spin_box import MSpinBox

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

class OCRFactory:
    """Factory for creating appropriate OCR engines based on settings."""
    
    _engines = {}  # Cache of created engines

    LLM_ENGINE_IDENTIFIERS = {
        "GPT": GPTOCR,
        "Gemini": GeminiOCR,
    }
    
    @classmethod
    def create_engine(cls, settings, source_lang_english: str, ocr_model: str) -> OCREngine:
        """
        Create or retrieve an appropriate OCR engine based on settings.
        
        Args:
            settings: Settings object with OCR configuration
            source_lang_english: Source language in English
            ocr_model: OCR model to use
            
        Returns:
            Appropriate OCR engine instance
        """
        # Create a cache key based on model and language
        cache_key = cls._create_cache_key(ocr_model, source_lang_english, settings)
        
        # Return cached engine if available
        if cache_key in cls._engines:
            return cls._engines[cache_key]
        
        # Create engine based on model or language
        engine = cls._create_new_engine(settings, source_lang_english, ocr_model)
        cls._engines[cache_key] = engine
        return engine
    
    @classmethod
    def _create_cache_key(cls, ocr_key: str,
                        source_lang: str,
                        settings) -> str:
        """
        Build a cache key for all ocr engines.

        - Always includes per-ocr credentials (if available),
          so changing any API key, URL, region, etc. triggers a new engine.
        - For LLM engines, also includes all LLM-specific settings
          (temperature, top_p, context, etc.).
        - The cache key is a hash of these dynamic values, combined with
          the ocr key and source language.
        - If no dynamic values are found, falls back to a simple key
          based on ocr and source language.
        """
        base = f"{ocr_key}_{source_lang}"

        # Gather any dynamic bits we care about:
        extras = {}

        # Always grab credentials for this service (if any)
        creds = settings.get_credentials(ocr_key)
        if creds:
            extras["credentials"] = creds

        # The LLM OCR engines currently don't use the settings in the LLMs tab
        # so exclude this for now

        # # If it's an LLM, also grab the llm settings
        # is_llm = any(identifier in ocr_key
        #              for identifier in cls.LLM_ENGINE_IDENTIFIERS)
        # if is_llm:
        #     extras["llm"] = settings.get_llm_settings()

        if not extras:
            return base

        # Otherwise, hash the combined extras dict
        extras_json = json.dumps(
            extras,
            sort_keys=True,
            separators=(",", ":"),
            default=str
        )
        digest = hashlib.sha256(extras_json.encode("utf-8")).hexdigest()

        # Append the fingerprint
        return f"{base}_{digest}"
    
    @classmethod
    def _create_new_engine(cls, settings, source_lang_english: str, ocr_model: str) -> OCREngine:
        """Create a new OCR engine instance based on model and language."""
        
        # Model-specific factory functions
        general = {
            'Microsoft OCR': cls._create_microsoft_ocr,
            'Google Cloud Vision': cls._create_google_ocr,
            'GPT-4.1-mini': lambda s: cls._create_gpt_ocr(s, ocr_model),
            'Gemini-2.0-Flash': lambda s: cls._create_gemini_ocr(s, ocr_model),
            'EasyOCR': cls._create_easy_ocr
        }
        
        # Language-specific factory functions (for Default model)
        language_factories = {
            'Japanese': cls._create_manga_ocr,
            'Korean': cls._create_pororo_ocr,
            'Chinese': cls._create_paddle_ocr,
            'Russian': lambda s: cls._create_gpt_ocr(s, 'GPT-4.1-mini')
        }
        
        # Check if we have a specific model factory
        if ocr_model in general:
            return general[ocr_model](settings)
        
        # For Default, use language-specific engines
        if ocr_model == 'Default' and source_lang_english in language_factories:
            return language_factories[source_lang_english](settings)
        
        # Fallback to doctr for any other language
        return cls._create_doctr_ocr(settings)
    
    @staticmethod
    def _create_microsoft_ocr(settings) -> OCREngine:
        credentials = settings.get_credentials(settings.ui.tr("Microsoft Azure"))
        engine = MicrosoftOCR()
        engine.initialize(
            api_key=credentials['api_key_ocr'],
            endpoint=credentials['endpoint']
        )
        return engine
    
    @staticmethod
    def _create_google_ocr(settings) -> OCREngine:
        credentials = settings.get_credentials(settings.ui.tr("Google Cloud"))
        engine = GoogleOCR()
        engine.initialize(api_key=credentials['api_key'])
        return engine
    
    @staticmethod
    def _create_gpt_ocr(settings, model) -> OCREngine:
        credentials = settings.get_credentials(settings.ui.tr("Open AI GPT"))
        api_key = credentials.get('api_key', '')
        engine = GPTOCR()
        engine.initialize(api_key=api_key, model=model)
        return engine
    
    @staticmethod
    def _create_manga_ocr(settings) -> OCREngine:
        device = 'cuda' if settings.is_gpu_enabled() else 'cpu'
        engine = MangaOCREngine()
        engine.initialize(device=device)
        return engine
    
    @staticmethod
    def _create_pororo_ocr(settings) -> OCREngine:
        engine = PororoOCREngine()
        engine.initialize()
        return engine
    
    @staticmethod
    def _create_paddle_ocr(settings) -> OCREngine:
        engine = PaddleOCREngine()
        engine.initialize()
        return engine
    
    @staticmethod
    def _create_doctr_ocr(settings) -> OCREngine:
        device = 'cuda' if settings.is_gpu_enabled() else 'cpu'
        engine = DocTROCR()
        engine.initialize(device=device)
        return engine
    
    @staticmethod
    def _create_gemini_ocr(settings, model) -> OCREngine:
        engine = GeminiOCR()
        engine.initialize(settings, model)
        return engine

    @staticmethod
    def _create_easy_ocr(settings) -> OCREngine:
        # Utilise EasyOCR sur CPU par défaut
        # Convertit le nom de langue UI en code ISO (ex: 'Français' -> 'fr')
        lang_name = settings.get_language() if hasattr(settings, 'get_language') else 'English'
        # Utilise le mapping de l'application si disponible
        lang_map = getattr(settings, 'lang_mapping', None)
        if lang_map and lang_name in lang_map:
            lang_code = lang_map[lang_name]
        else:
            # Fallback: quelques cas courants
            fallback = {
                'English': 'en', 'Français': 'fr', '日本語': 'ja', '한국어': 'ko',
                '简体中文': 'ch_sim', '繁體中文': 'ch_tra', 'Español': 'es', 'Deutsch': 'de',
                'Italiano': 'it', 'русский': 'ru', 'Nederlands': 'nl', 'Türkçe': 'tr'
            }
            lang_code = fallback.get(lang_name, 'en')
        use_gpu = settings.is_gpu_enabled() if hasattr(settings, 'is_gpu_enabled') else False
        engine = EasyOCREngine()
        engine.initialize(languages=[lang_code], use_gpu=use_gpu)
        return engine