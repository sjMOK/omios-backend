from rest_framework.serializers import Serializer, IntegerField, BooleanField, CharField, ListField, URLField


class IdResponse(Serializer):
    id = IntegerField()

    class Meta:
        ref_name = None

class IdsResponse(Serializer):
    id = ListField(child=IntegerField())

    class Meta:
        ref_name = None

class UniqueResponse(Serializer):
    is_unique = BooleanField()

    class Meta:
        ref_name = None


class DefaultResponse(Serializer):
    code = IntegerField()
    message = CharField(max_length=7)


class Image(Serializer):
    image = ListField(child=URLField())


def get_response(serializer=IdResponse(), code=200):    
    class Response(DefaultResponse):
        data = serializer
        class Meta:
            ref_name = None
    
    return {'responses': {code: Response}}

def get_ids_response(code=200):
    return get_response(IdsResponse(), code)

def get_paginated_response(serializer, code=200):
    class PaginatedResponse(Serializer):
        class Meta:
            ref_name = None

        count = IntegerField()
        next = URLField(allow_null=True)
        previous = URLField(allow_null=True)
        results = serializer

    return get_response(PaginatedResponse(), code)
