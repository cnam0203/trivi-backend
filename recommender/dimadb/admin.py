from django.contrib import admin

from dimadb.models import Domain, CulturalProduct, LdaSimilarity, WebActivityType, Location, Venue, WebActivity, LdaSimilarityVersion

# Register your models here.
admin.site.register(Domain)
admin.site.register(LdaSimilarityVersion)

@admin.register(CulturalProduct)
class CulturalProductAdmin(admin.ModelAdmin):
    model = CulturalProduct
    list_display = ['name', 'domain','description']
    list_filter = ['domain']
    ordering = ['name']

@admin.register(LdaSimilarity)
class LdaSimilarityAdmin(admin.ModelAdmin):
    model = LdaSimilarity
    list_display = ['source', 'target', 'similarity']
    list_filter = ['source', 'target']

@admin.register(WebActivityType)
class WebActivityType(admin.ModelAdmin):
    model = WebActivityType
    list_display = ['name', 'value']
    ordering = ['name']

@admin.register(WebActivity)
class WebActivityType(admin.ModelAdmin):
    model = WebActivity
    ordering = ['created_at']

@admin.register(Location)
class Location(admin.ModelAdmin):
    model = Location
    list_display = ['address', 'city', 'state', 'country', 'zip', 'latitude', 'longitude']

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    model = Venue
    list_display = ['name', 'get_location', 'rating']

    @admin.display(description='Location')
    def get_location(self, obj):
        return '{}'.format(obj.location)
