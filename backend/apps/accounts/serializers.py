from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'phone', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone',
            'zipcode', 'street', 'number',
            'complement', 'city', 'state',
            'is_admin', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'is_admin', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

# ── NOVO: serializer para admin gerenciar usuários ──
class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'name', 'phone',
            'zipcode', 'street', 'number',
            'complement', 'city', 'state',
            'is_admin', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'created_at']