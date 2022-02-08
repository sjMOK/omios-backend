from difflib import SequenceMatcher
from rest_framework.serializers import ValidationError

class PasswordSimilarityValidator:
    def __init__(self, max_similarity=0.7):
        self.max_similarity = max_similarity

    def validate(self, password, username):
        if SequenceMatcher(a=password.lower(), b=username.lower()).quick_ratio() >= self.max_similarity:
            raise ValidationError('The similarity between password and username is too large.')
