from nlp_deck_manager.processors.base import NoteProcessor, ProcessorPipeline
from nlp_deck_manager.processors.custom_loader import load_processor_from_file
from nlp_deck_manager.processors.cached_info import CachedLemmaInfoProcessor
from nlp_deck_manager.processors.german import GermanFiveExamplesPlaceholderProcessor, GermanVanillaMorphologyProcessor
from nlp_deck_manager.processors.japanese import JapaneseVanillaFieldsProcessor
from nlp_deck_manager.processors.translation_vanilla import TranslationPlaceholderProcessor

__all__ = [
    "NoteProcessor",
    "ProcessorPipeline",
    "load_processor_from_file",
    "CachedLemmaInfoProcessor",
    "GermanFiveExamplesPlaceholderProcessor",
    "GermanVanillaMorphologyProcessor",
    "JapaneseVanillaFieldsProcessor",
    "TranslationPlaceholderProcessor",
]
