from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# DB for Cultural Product


class Domain(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)
    description = models.CharField(max_length=100)

    # def __str__(self) :
    #     return '{}'.format(self.name)

    class Meta:
        db_table = 'domain'


class Organization(models.Model):
    legal_name = models.CharField(max_length=150, null=True, blank=True)
    alternative_name = models.CharField(max_length=150, null=True)
    website = models.URLField(max_length=300, null=True)
    description = models.CharField(max_length=300, null=True)

    # def __str__(self) :
    #     return '{}'.format(self.legal_name)

    class Meta:
        db_table = 'organization'


class CulturalProduct(models.Model):
    PRODUCT_TYPES = (
        ('item', 'ITEM'),
        ('event', 'EVENT'),
    )

    product_id = models.CharField(max_length=150, primary_key=True)
    name = models.CharField(max_length=150, unique=True)
    slug = models.CharField(max_length=150, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    url = models.URLField(verbose_name='source_url', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    product_type = models.CharField(
        max_length=10, choices=PRODUCT_TYPES, default='event')  # Don't use

    domain = models.ForeignKey(Domain, on_delete=models.RESTRICT)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        db_table = 'culturalproduct'


class CulturalItem(models.Model):
    product = models.OneToOneField(
        CulturalProduct, on_delete=models.CASCADE, primary_key=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'culturalitem'


class Event(models.Model):
    product = models.OneToOneField(
        CulturalProduct, on_delete=models.CASCADE, primary_key=True)
    status = models.CharField(max_length=16)
    start_date = models.DateField()
    end_date = models.DateField()

    # def __str__(self) :
    #     return '{}'.format(self.product.name)

    class Meta:
        db_table = 'event'


class Location(models.Model):
    address = models.CharField(max_length=150, null=True, blank=True)
    address_2 = models.CharField(max_length=150, null=True)
    state = models.CharField(max_length=20)
    city = models.CharField(max_length=150, null=True, blank=True)
    country = models.CharField(max_length=150, null=True, blank=True)
    zip = models.CharField(max_length=20)

    latitude = models.DecimalField(max_digits=11, decimal_places=9)
    longitude = models.DecimalField(max_digits=11, decimal_places=9)

    class Meta:
        db_table = 'location'

    def __str__(self):
        return '{}, {}, {} {}'.format(self.address, self.city, self.state, self.zip)


class Venue(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.CharField(max_length=150, unique=True)

    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'venue'


class TakePlace(models.Model):
    time = models.DateTimeField(null=True)
    weekend = models.BooleanField(verbose_name='is_on_weekend')

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.RESTRICT)

    def __str__(self):
        return '{} at {}'.format(self.event.product.name, self.venue.name)

    class Meta:
        db_table = 'takeplace'

# DB for Web Acitivity


class WebActivityType(models.Model):
    name = models.CharField(max_length=60, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    value = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)


class WebActivity(models.Model):
    page_id = models.CharField(max_length=50, null=True, blank=True)
    session = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    browser = models.CharField(max_length=80, null=True)
    visitor = models.CharField(max_length=20)

    activity_type = models.ForeignKey(
        WebActivityType, on_delete=models.CASCADE)


class ContainProduct(models.Model):
    activity = models.OneToOneField(WebActivity, on_delete=models.CASCADE)
    product = models.ForeignKey(CulturalProduct, on_delete=models.CASCADE)

    def __str__(self):
        return 'Visitor with {} interacted with product {}'.format(self.activity.visitor, self.product.product_id)

    class Meta:
        verbose_name = "Activity - Product"

# DB for Machine Learning Model


class LdaSimilarityVersion(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    n_topics = models.IntegerField(null=True)
    item_type = models.CharField(max_length=150, null=True, blank=True)
    n_products = models.IntegerField(null=True)

    def __str__(self):
        return format(self.created_at)


class LdaSimilarity(models.Model):
    source = models.CharField(max_length=150, null=True, blank=True)
    target = models.CharField(max_length=150, null=True, blank=True)
    item_type = models.CharField(max_length=150, null=True, blank=True)
    similarity = models.DecimalField(max_digits=10, decimal_places=7)
    version = models.CharField(max_length=150, null=True, blank=True)


# Adminstrative Management
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    orgs = models.ManyToManyField(Organization, verbose_name="member")

# Import_info:
class ImportInfo(models.Model):
    id = models.AutoField(primary_key=True)
    table_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# New_event:
class Events(models.Model):
    id = models.AutoField(primary_key=True)
    event_id = models.CharField(max_length=150, unique=True)
    event_name = models.CharField(max_length=150, null=True, blank=True)
    event_title = models.CharField(max_length=150, null=True, blank=True)
    event_type = models.CharField(max_length=150, null=True, blank=True)
    event_price = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    slug = models.CharField(max_length=150, null=True, blank=True)
    lang = models.CharField(max_length=150, null=True, blank=True)
    start_date = models.DateTimeField(null=True)
    end_date = models.DateTimeField(null=True)
    next_date = models.DateTimeField(null=True)
    count_down = models.IntegerField(null=True)
    recurring_freg = models.IntegerField(null=True)
    recurring_count = models.IntegerField(null=True)
    recurring_by_day = models.IntegerField(null=True)
    is_public = models.CharField(max_length=10, choices=(
        ('True', True), ('False', False)), default='True')
    status = models.CharField(max_length=30, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.CharField(max_length=150, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True, null=True)
    modified_by = models.CharField(max_length=150, null=True, blank=True)
    group_id = models.CharField(max_length=30, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# New_event:


class Products(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.CharField(max_length=150, unique=True)
    product_name = models.CharField(max_length=150, null=True, blank=True)
    product_type = models.CharField(max_length=150, null=True, blank=True)
    product_price = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    product_revenue = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    price_type = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=30, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.CharField(max_length=150, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True, null=True)
    modified_by = models.CharField(max_length=150, null=True, blank=True)
    group_id = models.CharField(max_length=30, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Location


class GeoLocation(models.Model):
    id = models.AutoField(primary_key=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    location_name = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=150, null=True, blank=True)
    address2 = models.CharField(max_length=150, null=True, blank=True)
    longitude = models.CharField(max_length=50, null=True, blank=True)
    latitude = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    region = models.CharField(max_length=50, null=True, blank=True)
    zip = models.CharField(max_length=50, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Resource


class Resource(models.Model):
    id = models.AutoField(primary_key=True)
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    resource_name = models.CharField(max_length=150, null=True, blank=True)
    resource_type = models.CharField(max_length=50, null=True, blank=True)
    resource_url = models.CharField(max_length=200)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# PriceType


class PriceType(models.Model):
    id = models.AutoField(primary_key=True)
    price_type_id = models.CharField(max_length=50, null=True, blank=True)
    price_type_name = models.CharField(max_length=50, null=True, blank=True)
    price_type_currency = models.CharField(
        max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# BusinessEntity


class BusinessEntity(models.Model):
    id = models.AutoField(primary_key=True)
    entity_id = models.CharField(max_length=50, null=True, blank=True)
    entity_name = models.CharField(max_length=50, null=True, blank=True)
    slug = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.CharField(max_length=50, null=True, blank=True)
    modified_at = models.DateTimeField(auto_now=True, null=True)
    modified_by = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EntityLocation


class EntityLocation(models.Model):
    id = models.AutoField(primary_key=True)
    entity_id = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EventLocation


class EventLocation(models.Model):
    id = models.AutoField(primary_key=True)
    event_id = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    room = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EntityEventRole


class EntityEventRole(models.Model):
    id = models.AutoField(primary_key=True)
    entity_id = models.CharField(max_length=50, null=True, blank=True)
    event_id = models.CharField(max_length=50, null=True, blank=True)
    role_name = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EventResource


class EventResource(models.Model):
    id = models.AutoField(primary_key=True)
    event_id = models.CharField(max_length=50, null=True, blank=True)
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EntityResource


class EntityResource(models.Model):
    id = models.AutoField(primary_key=True)
    entity_id = models.CharField(max_length=50, null=True, blank=True)
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EventSimilarity


class EventSimilarity(models.Model):
    id = models.AutoField(primary_key=True)
    source_id = models.CharField(max_length=50, null=True, blank=True)
    target_id = models.CharField(max_length=50, null=True, blank=True)
    similarity = models.DecimalField(max_digits=5, decimal_places=2)
    algo = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EntityProductRole


class EntityProductRole(models.Model):
    id = models.AutoField(primary_key=True)
    entity_id = models.CharField(max_length=50, null=True, blank=True)
    product_id = models.CharField(max_length=50, null=True, blank=True)
    role_name = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# ProductResource


class ProductResource(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.CharField(max_length=50, null=True, blank=True)
    resource_id = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# ProductSimilarity


class ProductSimilarity(models.Model):
    id = models.AutoField(primary_key=True)
    source_id = models.CharField(max_length=50, null=True, blank=True)
    target_id = models.CharField(max_length=50, null=True, blank=True)
    similarity = models.DecimalField(max_digits=5, decimal_places=2)
    algo = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EventProduct


class EventProduct(models.Model):
    id = models.AutoField(primary_key=True)
    event_id = models.CharField(max_length=50, null=True, blank=True)
    product_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# WebActivityType


class ActivityType(models.Model):
    id = models.AutoField(primary_key=True)
    activity_type_id = models.CharField(max_length=50, null=True, blank=True)
    activity_type_name = models.CharField(max_length=50, null=True, blank=True)
    score = models.IntegerField(null=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# WebActivity


class WebActivities(models.Model):
    id = models.AutoField(primary_key=True)
    activity_id = models.CharField(max_length=50, null=True, blank=True)
    activity_type_id = models.ForeignKey(
        ActivityType, on_delete=models.CASCADE)
    activity_duration = models.IntegerField(null=True)
    activity_description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Event Preference


class EventPreference(models.Model):
    id = models.AutoField(primary_key=True)
    preference_id = models.CharField(max_length=50, null=True, blank=True)
    preference_type = models.CharField(max_length=50, null=True, blank=True)
    preference_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    event_id = models.CharField(max_length=50, null=True, blank=True)
    activity_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Product Preferene


class ProductPreference(models.Model):
    id = models.AutoField(primary_key=True)
    preference_id = models.CharField(max_length=50, null=True, blank=True)
    preference_type = models.CharField(max_length=50, null=True, blank=True)
    preference_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    product_id = models.CharField(max_length=50, null=True, blank=True)
    activity_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)


# Session
class Session(models.Model):
    id = models.AutoField(primary_key=True)
    visit_id = models.CharField(max_length=50, null=True, blank=True)
    visit_date = models.DateField(null=True, blank=True)
    visit_start_time = models.DateTimeField(null=True, blank=True)
    visit_end_time = models.DateTimeField(null=True, blank=True)
    visit_number = models.CharField(max_length=50, null=True, blank=True)
    visit_duration = models.IntegerField(null=True)
    operating_system = models.CharField(max_length=150, null=True, blank=True)
    device_category = models.CharField(max_length=150, null=True, blank=True)
    device_brand = models.CharField(max_length=150, null=True, blank=True)
    browser = models.CharField(max_length=150, null=True, blank=True)
    page_title = models.CharField(max_length=150, null=True, blank=True)
    page_location = models.CharField(max_length=150, null=True, blank=True)
    event_name = models.CharField(max_length=150, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    customer_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)
    
class SessionLocation(models.Model):
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)


# Customer
class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    customer_id = models.CharField(max_length=50, null=True, blank=True)
    ip_address = models.CharField(max_length=50, null=True, blank=True)
    contact_id = models.CharField(max_length=50, null=True, blank=True)
    profile_id = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Profile


class ProfileCustomer(models.Model):
    id = models.AutoField(primary_key=True)
    profile_id = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    age = models.IntegerField(null=True)
    gender = models.CharField(max_length=10, choices=(
        ('male', 'male'), ('female', 'female')), default='event')
    import_id = models.CharField(max_length=30, null=True, blank=True)


# Journey
class Journey(models.Model):
    id = models.AutoField(primary_key=True)
    journey_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Interaction


class Interaction(models.Model):
    id = models.AutoField(primary_key=True)
    interaction_id = models.CharField(max_length=50, null=True, blank=True)
    session_id = models.CharField(max_length=50, null=True, blank=True)
    journey_id = models.CharField(max_length=50, null=True, blank=True)
    customer_id = models.CharField(max_length=50, null=True, blank=True)
    visit_date = models.DateField(null=True, blank=True)
    operating_system = models.CharField(max_length=150, null=True, blank=True)
    device_category = models.CharField(max_length=150, null=True, blank=True)
    device_brand = models.CharField(max_length=150, null=True, blank=True)
    browser = models.CharField(max_length=150, null=True, blank=True)
    page_id = models.CharField(max_length=50, null=True, blank=True)
    page_title = models.CharField(max_length=150, null=True, blank=True)
    page_location = models.CharField(max_length=150, null=True, blank=True)
    event_name = models.CharField(max_length=150, null=True, blank=True)
    activity_id = models.CharField(max_length=50, null=True, blank=True)
    interaction_number = models.IntegerField(null=True, blank=True)
    is_entrance = models.CharField(
        max_length=10, choices=(('True', True), ('False', False)), null=True, blank=True)
    is_exit = models.CharField(max_length=10, choices=(
        ('True', True), ('False', False)), null=True, blank=True)    
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)
    
class InteractionLocation(models.Model):
    id = models.AutoField(primary_key=True)
    interaction_id = models.CharField(max_length=50, null=True, blank=True)
    location_id = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# WebPage


class WebPage(models.Model):
    id = models.AutoField(primary_key=True)
    page_id = models.CharField(max_length=50, null=True, blank=True)
    url = models.CharField(max_length=200)
    page_path = models.CharField(max_length=200)
    page_title = models.CharField(max_length=150, null=True, blank=True)
    search_keyword = models.CharField(max_length=150, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# Contact


class Contact(models.Model):
    id = models.AutoField(primary_key=True)
    contact_id = models.CharField(max_length=50, null=True, blank=True)
    contact_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=50, null=True, blank=True)
    phone1 = models.CharField(max_length=50, null=True, blank=True)
    phone2 = models.CharField(max_length=50, null=True, blank=True)
    url = models.CharField(max_length=50, null=True, blank=True)
    business_hour = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)

# EntityContactPoint


class EntityContactPoint(models.Model):
    id = models.AutoField(primary_key=True)
    entity_id = models.CharField(max_length=50, null=True, blank=True)
    contact_id = models.CharField(max_length=50, null=True, blank=True)
    contact_role = models.CharField(max_length=50, null=True, blank=True)
    import_id = models.CharField(max_length=30, null=True, blank=True)
