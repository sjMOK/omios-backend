from rest_framework.serializers import *


class IdResponse(Serializer):
    id = IntegerField()

    class Meta:
        ref_name = None


class UniqueResponse(Serializer):
    is_unique = BooleanField()

    class Meta:
        ref_name = None


class DefaultResponse(Serializer):
    code = IntegerField()
    message = CharField(max_length=7)


def get_response(json=IdResponse, code=200):    
    class Response(DefaultResponse):
        data = json()
        class Meta:
            ref_name = None
    
    return {'responses': {code: Response}}