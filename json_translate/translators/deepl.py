# -*- coding: utf-8 -*-
import os
import time
import json
import re
from urllib import request, parse
from .base import BaseTranslator
from settings import DEEPL_API_ENDPOINT


class DeepLTranslator(BaseTranslator):
    """DeepL translator class."""

    def translate_string(self, text: str) -> str:
        """Translate a specific string.
        ...
        """
        if not isinstance(text, str):
            return text
    
        cached_result = self.cached.get(text)
        if cached_result:
            self.log_translation(
                input_text=text,
                result=f"{cached_result} (cached)",
            )
            return cached_result

        # Identify variables surrounded by curly brackets
        variables = re.findall(r'\{.*?\}', text)
        for i, var in enumerate(variables):
            placeholder = f"UNIQUE_PLACEHOLDER_{i}_END"
            text = text.replace(var, placeholder)

        # Replace special characters with placeholders
        text = text.replace('®', 'REGISTERED_SIGN_PLACEHOLDER')
        text = text.replace('™', 'TRADEMARK_SIGN_PLACEHOLDER')
    
        time.sleep(self.sleep)
    
        data = {
            "target_lang": self.target_locale,
            "auth_key": os.environ.get("DEEPL_AUTH_KEY"),
            "text": text,
            "preserve_formatting": "1",
        }
    
        if self.source_locale is not None:
            data["source_lang"] = self.source_locale
    
        if self.glossary is not None:
            data["glossary_id"] = self.glossary
    
        data = parse.urlencode(data).encode()
    
        req = request.Request(DEEPL_API_ENDPOINT, data=data)
        response = request.urlopen(req)  # nosec
    
        if response.status != 200:
            self.log_translation(
                input_text=text,
                result=f"response status: {response.status}",
                status=self.Status.error,
            )
            return text
    
        response_data = json.loads(response.read())
    
        if "translations" not in response_data:
            self.log_translation(
                input_text=text,
                result=f"response empty: {response_data}",
                status=self.Status.error,
            )
            return text
    
        if len(response_data["translations"]) > 1:
            self.log_translation(
                input_text=text,
                result=f"more than 1 translation: {response_data['translations']})",
                status=self.Status.warning,
            )
    
        self.log_translation(
            input_text=text,
            result=response_data["translations"][0]["text"],
            status=self.Status.success,
        )
    
        dec_text = self.decode_text(
            text=response_data["translations"][0]["text"],
        )
    
        # Replace placeholders with original variables
        for i, var in enumerate(variables):
            placeholder = f"UNIQUE_PLACEHOLDER_{i}_END"
            dec_text = dec_text.replace(placeholder, var)

        # Replace special character placeholders back to original characters
        dec_text = dec_text.replace('REGISTERED_SIGN_PLACEHOLDER', '®')
        dec_text = dec_text.replace('TRADEMARK_SIGN_PLACEHOLDER', '™')
    
        self.cached[text] = dec_text
    
        return dec_text
