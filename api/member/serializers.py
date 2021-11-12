from django.db.models import fields
from rest_framework import serializers
from .models import Shopper, Member, Wholesaler

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['username', 'password']


class ShopperSerializer(serializers.ModelSerializer):
    member = MemberSerializer()

    class Meta:
        model = Shopper
        fields = '__all__'

    def create(self, validated_data):
        member_data = validated_data.pop('member')
        member = Member.objects.create_user(**member_data)
        shopper = Shopper.objects.create(member=member, **validated_data)
        return shopper


class WholesalerSerializer(serializers.ModelSerializer):
    member = MemberSerializer()

    class Meta:
        model = Wholesaler
        fields = '__all__'

    def create(self, validated_data):
        member_data = validated_data.pop('member')
        member = Member.objects.create_user(**member_data)
        wholesaler = Wholesaler.objects.create(member=member, **validated_data)
        return wholesaler

