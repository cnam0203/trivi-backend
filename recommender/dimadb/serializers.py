from rest_framework import serializers
from rest_framework_jwt.settings import api_settings
from .models import Domain, CulturalProduct, Organization, WebActivity, Event, CulturalItem


class DomainSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    class Meta:
        model = Domain
        fields = '__all__'

class OrganizationSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    class Meta:
        model = Organization
        fields = '__all__'

class CulturalProductSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(source='domain.name')
    organization = serializers.CharField(source='organization.legal_name')

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    class Meta:
        model = CulturalProduct
        fields = ('product_id', 'name', 'product_type', 'domain', 'organization', 'created_at')
        # fields = ('product_id', 'name', 'domain__name', 'organization__name', 'create_at')

class EventSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(source='product.domain.name')
    name = serializers.CharField(source='product.name')
    organization = serializers.CharField(source='product.organization.legal_name')
    domain_id = serializers.CharField(source='product.domain.id')
    organization_id = serializers.CharField(source='product.organization.id')
    product_id = serializers.CharField(source='product.product_id')
    created_at = serializers.DateTimeField(source='product.created_at')
    slug = serializers.CharField(source='product.slug')
    description = serializers.CharField(source='product.description')
    source_url = serializers.CharField(source='product.url')
    image_url = serializers.CharField(source='product.image_url')

    class Meta:
        model = Event
        fields = '__all__'

class ItemSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(source='product.domain.name')
    name = serializers.CharField(source='product.name')
    organization = serializers.CharField(source='product.organization.legal_name')
    domain_id = serializers.CharField(source='product.domain.id')
    organization_id = serializers.CharField(source='product.organization.id')
    product_id = serializers.CharField(source='product.product_id')
    created_at = serializers.DateTimeField(source='product.created_at')
    slug = serializers.CharField(source='product.slug')
    description = serializers.CharField(source='product.description')
    source_url = serializers.CharField(source='product.url')
    image_url = serializers.CharField(source='product.image_url')

    class Meta:
        model = CulturalItem
        fields = '__all__'

class WebActivitySerializer(serializers.ModelSerializer):
    activity_type = serializers.CharField(source='activity_type.name')

    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance

    class Meta:
        model = WebActivity
        fields = ('id', 'activity_type', 'visitor', 'page_id', 'session', 'browser', 'created_at')


