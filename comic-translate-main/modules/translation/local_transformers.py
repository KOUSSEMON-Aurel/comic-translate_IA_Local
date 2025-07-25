from typing import Any
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import psutil
import os
import time

from .base import TraditionalTranslation
from ..utils.textblock import TextBlock


def limiter_ressources(cpu_limit=80, ram_limit_gb=4):
    """Met en pause le programme si les limites de CPU/RAM sont dépassées."""
    try:
        process = psutil.Process(os.getpid())
        ram_used_gb = process.memory_info().rss / (1024 ** 3)
        cpu = process.cpu_percent(interval=0.1)

        if cpu > cpu_limit or ram_used_gb > ram_limit_gb:
            print(f"[WARNING] Limite de ressources atteinte (CPU: {cpu:.1f}%, RAM: {ram_used_gb:.2f} Go). Pause de 2s...")
            time.sleep(2)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        # Le processus a peut-être déjà été tué
        pass


class LocalTransformersTranslation(TraditionalTranslation):
    def __init__(self):
        self.translator = None
        self.source_lang = None
        self.target_lang = None
        self.model_name = None

    def initialize(self, settings: Any, source_lang: str, target_lang: str) -> None:
        self.source_lang = source_lang
        self.target_lang = target_lang
        # Priorité au champ local_transformers_model dans settings ou credentials
        model_name = None
        if hasattr(settings, 'local_transformers_model') and settings.local_transformers_model:
            model_name = settings.local_transformers_model
        elif hasattr(settings, 'get_credentials'):
            creds = settings.get_credentials('Custom')
            if creds and 'local_transformers_model' in creds and creds['local_transformers_model']:
                model_name = creds['local_transformers_model']
        # FORCÉ : chemin local du modèle
        self.model_name = r"C:/Users/Aurel_Dexgun/Downloads/models/nllb-200-distilled-600M"
        print(f"[DEBUG] Chemin du modèle utilisé pour la traduction locale : {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self.device = torch.device('cpu')
        self.model = self.model.to(self.device)
        self.translator = pipeline('translation', model=self.model, tokenizer=self.tokenizer, device=-1)

    def _nllb_lang_code(self, lang: str) -> str:
        # Mapping minimal pour NLLB (à étendre selon besoin)
        mapping = {
            'en': 'eng_Latn', 'fr': 'fra_Latn', 'es': 'spa_Latn', 'de': 'deu_Latn',
            'it': 'ita_Latn', 'ja': 'jpn_Jpan', 'ko': 'kor_Hang', 'zh': 'zho_Hans',
            'ru': 'rus_Cyrl', 'nl': 'nld_Latn', 'tr': 'tur_Latn',
        }
        return mapping.get(lang, lang)

    def translate(self, blk_list: list[TextBlock]) -> list[TextBlock]:
        print("[DEBUG] Début de la traduction locale (HuggingFace)")
        src_code = self.get_language_code(self.source_lang)
        tgt_code = self.get_language_code(self.target_lang)
        nllb_src = self._nllb_lang_code(src_code)
        nllb_tgt = self._nllb_lang_code(tgt_code)
        print(f"[DEBUG] Langues : source={self.source_lang} ({src_code} -> {nllb_src}), cible={self.target_lang} ({tgt_code} -> {nllb_tgt})")
        try:
            for i, blk in enumerate(blk_list):
                # --- AJOUT : Contrôle des ressources avant chaque opération lourde ---
                limiter_ressources()
                
                text = self.preprocess_text(blk.text, src_code)
                print(f"[DEBUG] Bloc {i} : texte à traduire = {repr(text)}")
                try:
                    process = psutil.Process(os.getpid())
                    ram_before_gb = process.memory_info().rss / (1024 ** 3)
                    print(f"[INFO] RAM avant traduction du bloc {i}: {ram_before_gb:.2f} Go")
                    
                    print(f"[DEBUG] Avant appel pipeline HuggingFace pour bloc {i}")
                    result = self.translator(text, src_lang=nllb_src, tgt_lang=nllb_tgt, max_length=512)
                    print(f"[DEBUG] Après appel pipeline HuggingFace pour bloc {i} : {result}")
                    
                    ram_after_gb = process.memory_info().rss / (1024 ** 3)
                    print(f"[INFO] RAM après traduction du bloc {i}: {ram_after_gb:.2f} Go")
                    
                    blk.translation = result[0]['translation_text']
                    print(f"[DEBUG] Bloc {i} : traduction = {repr(blk.translation)}")
                except Exception as e:
                    ram_on_fail_gb = psutil.Process(os.getpid()).memory_info().rss / (1024 ** 3)
                    print(f"[CRITICAL] Erreur lors de la traduction du bloc {i}. RAM: {ram_on_fail_gb:.2f} Go. Erreur: {e}")
                    blk.translation = f"[Erreur traduction: {e}]"

            print("[DEBUG] Traduction locale terminée")
        except Exception as e:
            print(f"[CRITICAL] Erreur globale dans la traduction locale : {e}")
        print("[DEBUG] Fin de la méthode translate")
        return blk_list 