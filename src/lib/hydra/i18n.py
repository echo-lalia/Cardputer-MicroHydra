"""Internationalization.

This module implements a lightweight internationalization class,
which can be used to implement translations in MicroHydra.
"""

import json

from .config import Config
from .utils import get_instance


class I18n:
    """Internationalization class.

    args:
    - translations:
        A json string defining a list of dicts,
        where each dict is formatted like `{'lang':'translation', ...}`.
        Example:
        '''[
        {"en": "Loading...", "zh": "加载中...", "ja": "読み込み中..."},
        {"en": "Files", "zh": "文件", "ja": "ファイル"}
        ]'''
    """

    def __init__(self, translations, key='en'):
        """Initialize the I18n class.

        Translations are provided with the 'translations' parameter,
        and will be processed into a single dictionary.
        'key' selects the language to use as the dictionary key,
        and the values of that dictionary are based on the language set in 'config.json'.
        """
        # extract lang from config
        config = get_instance(Config)
        self.lang = config['language']

        # extract and prune target translations into one dict
        self.translations = {item[key]:item.get(self.lang, item[key]) for item in json.loads(translations)}

    def __getitem__(self, text):
        """Get the translation for the given text, defaulting to the given text."""
        return self.translations.get(text, text)
