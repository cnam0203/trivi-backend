from django.db import models
from django.contrib.auth.models import User

# Create your models here.

# DB for Cultural Product
class Domain(models.Model):
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=100)

    # def __str__(self) :
    #     return '{}'.format(self.name)

    class Meta:
        db_table = 'domain'

class Organization(models.Model):
    legal_name = models.CharField(max_length=150)
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
    description = models.TextField()
    created_at = models.DateTimeField()
    url = models.URLField(verbose_name='source_url', null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default='event') # Don't use

    domain = models.ForeignKey(Domain, on_delete=models.RESTRICT)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        db_table = 'culturalproduct'

class CulturalItem(models.Model):
    product = models.OneToOneField(CulturalProduct, on_delete=models.CASCADE, primary_key=True)
    price = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'culturalitem'

class Event(models.Model):
    product = models.OneToOneField(CulturalProduct, on_delete=models.CASCADE, primary_key=True)
    status = models.CharField(max_length=16)
    start_date = models.DateField()
    end_date = models.DateField()

    # def __str__(self) :
    #     return '{}'.format(self.product.name)

    class Meta:
        db_table = 'event'

class Location(models.Model):
    address = models.CharField(max_length=150)
    address_2 = models.CharField(max_length=150, null=True)
    state = models.CharField(max_length=20)
    city = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    zip = models.CharField(max_length=20)

    latitude = models.DecimalField(max_digits=11, decimal_places=9)
    longitude = models.DecimalField(max_digits=11, decimal_places=9)

    class Meta:
        db_table = 'location'

    def __str__(self) :
        return '{}, {}, {} {}'.format(self.address, self.city, self.state, self.zip)

class Venue(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.CharField(max_length=150, unique=True)

    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'venue'

class TakePlace(models.Model):
    time = models.DateTimeField()
    weekend = models.BooleanField(verbose_name='is_on_weekend')

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.RESTRICT)

    def __str__(self):
        return '{} at {}'.format(self.event.product.name, self.venue.name)

    class Meta:
        db_table = 'takeplace'

# DB for Web Acitivity
class WebActivityType(models.Model):
    name = models.CharField(max_length=60)
    description = models.TextField()
    value = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self) :
        return '{}'.format(self.name)

class WebActivity(models.Model):
    page_id = models.CharField(max_length=50)
    session = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    browser = models.CharField(max_length=80, null=True)
    visitor = models.CharField(max_length=20)

    activity_type = models.ForeignKey(WebActivityType, on_delete=models.CASCADE)

class ContainProduct(models.Model):
    activity = models.OneToOneField(WebActivity, on_delete=models.CASCADE)
    product = models.ForeignKey(CulturalProduct, on_delete=models.CASCADE)

    def __str__(self):
        return 'Visitor with {} interacted with product {}'.format(self.activity.visitor, self.product.product_id)

    class Meta:
        verbose_name = "Activity - Product"

# DB for Machine Learning Model
class LdaSimilarityVersion(models.Model):
    created_at = models.DateTimeField()
    n_topics = models.IntegerField()
    n_products = models.IntegerField()

    def __str__(self):
        return 'Version on {}'.format(self.created_at)

class LdaSimilarity(models.Model):
    source = models.ForeignKey(CulturalProduct, on_delete=models.CASCADE, related_name='source_product')
    target = models.ForeignKey(CulturalProduct, on_delete=models.CASCADE, related_name='target_product')

    similarity = models.DecimalField(max_digits=10, decimal_places=7)
    version = models.ForeignKey(LdaSimilarityVersion, on_delete=models.CASCADE)

    
# Adminstrative Management
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    orgs = models.ManyToManyField(Organization, verbose_name="member")