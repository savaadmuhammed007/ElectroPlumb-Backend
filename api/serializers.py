from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Item, MaterialList, ListItem

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'whatsapp', 'business_name', 'address', 'city', 'state', 'pin_code', 'profile_photo', 'about']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        if profile_data:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, default='electrician')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'password', 'confirm_password', 'phone', 'role']

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError({"email": "Email already in use."})
        return data

    def create(self, validated_data):
        phone = validated_data.pop('phone', '')
        role = validated_data.pop('role', 'electrician')
        validated_data.pop('confirm_password')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '')
        )

        # Check if username/email contains admin to set staff role if desired
        if role == 'admin' or 'admin' in user.username.lower():
            user.is_staff = True
            user.save()

        UserProfile.objects.create(
            user=user,
            role=role if role in ['electrician', 'plumber', 'admin'] else 'electrician',
            phone=phone
        )
        return user


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'item_code', 'item_type', 'category', 'unit', 'description', 'status', 'created_at', 'updated_at']


class ListItemSerializer(serializers.ModelSerializer):
    item_details = ItemSerializer(source='item', read_only=True)

    class Meta:
        model = ListItem
        fields = ['id', 'item', 'item_name', 'category', 'unit', 'quantity', 'item_details']


class MaterialListSerializer(serializers.ModelSerializer):
    items = ListItemSerializer(many=True, required=False)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = MaterialList
        fields = [
            'id', 'user', 'user_name', 'list_type', 'client_name', 'client_phone',
            'project_name', 'location', 'date', 'notes', 'created_at', 'updated_at', 'items'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        material_list = MaterialList.objects.create(**validated_data)

        for item_data in items_data:
            ListItem.objects.create(material_list=material_list, **item_data)

        return material_list

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                ListItem.objects.create(material_list=instance, **item_data)

        return instance
