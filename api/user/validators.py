from difflib import SequenceMatcher
from rest_framework.serializers import ValidationError

class PasswordSimilarityValidator:
    def __init__(self, max_similarity=0.5):
        self.max_similarity = max_similarity

    def validate(self, password, username, email):
        if SequenceMatcher(a=password, b=username).quick_ratio() >= self.max_similarity:
            raise ValidationError('The similarity between password and username is too large.')
        elif SequenceMatcher(a=password, b=email).quick_ratio() >= self.max_similarity:
            raise ValidationError('The similarity between password and email is too large.')
                        