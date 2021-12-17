from django.http import HttpResponseRedirect
from rest_framework import permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import DomainSerializer, CulturalProductSerializer, WebActivitySerializer, EventSerializer, OrganizationSerializer, ItemSerializer
from .models import CulturalProduct, Event, CulturalItem, WebActivity, WebActivityType, TakePlace, Domain, Organization
import json
from datetime import datetime

@api_view(['GET'])
def home(request):
    # Retrieve a brief infomation from the database
    activities = WebActivity.objects.filter(activity_type__name='view').order_by('created_at')[:5]
    products = CulturalProduct.objects.filter(domain__name='Visual Arts and Crafts').order_by('name')[:5]

    # Set up date for charts
    activity_data = list()
    domain_data = list()
    cultural_data = list()

    for web_activity_type in WebActivityType.objects.all():
        data = [web_activity_type.name, web_activity_type.webactivity_set.count()]
        activity_data.append(data)

    for domain in Domain.objects.all():
        data = [domain.name, domain.culturalproduct_set.count()]
        domain_data.append(data)

    reports = [
        {
            'id': 'activity-chart',
            'title': 'Total records for web activity',
            'data': activity_data,
            'type': 'pie',
        },
        {
            'id': 'domain-chart',
            'title': 'Total products in each domain',
            'data': domain_data,
            'type': 'column'
        },
    ]
    return Response(reports, status=status.HTTP_201_CREATED)

class DomainList(APIView):
    """
    Create a new user. It's called 'UserList' because normally we'd have a get
    method here too, for retrieving a list of all User objects.
    """

    # permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        snippets = Domain.objects.all()
        serializer = DomainSerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = DomainSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CulturalProductList(APIView):
    """
    Create a new user. It's called 'UserList' because normally we'd have a get
    method here too, for retrieving a list of all User objects.
    """

    # permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        snippets = CulturalProduct.objects.all()
        serializer = CulturalProductSerializer(snippets, many=True)
        return Response(serializer.data)


class CulturalProductDetail(APIView):
    def get_object(self, type, pk):
        try:
            if (type == 'event'):   
                return Event.objects.get(product_id=pk)
            else:
                return CulturalItem.objects.get(product_id=pk)
        except Event.DoesNotExist:
            return None 
        except CulturalItem.DoesNotExist:
            return None

    def get(self, request, type, pk, format=None):
        snippet = self.get_object(type, pk)
        print
        if (snippet):
            if (type == 'event'):
                product_serializer = EventSerializer(snippet)
            else:
                product_serializer = ItemSerializer(snippet)
            product = product_serializer.data
        else:
            product = {}
        
        list_domains = Domain.objects.all()
        list_organizations = Organization.objects.all()
        domain_serializer = DomainSerializer(list_domains, many=True)
        organization_serializer = OrganizationSerializer(list_organizations, many=True)

        return Response({
            'product': product,
            'domains': domain_serializer.data,
            'organizations': organization_serializer.data
        })
    
    def put(self, request, type, pk, format=None):
        try:
            data = json.loads(request.body)
            domain = Domain.objects.get(id=data['domain'])
            organization = Organization.objects.get(id=data['organization'])
            CulturalProduct.objects.filter(product_id=pk).update(name=data['name'], slug=data['slug'],
                                description=data['description'], image_url=data['image_url'],
                                url=data['source_url'], product_type=data['product_type'],
                                domain=domain, organization=organization)
            product = CulturalProduct.objects.get(product_id=pk)

            if (data['product_type'] == 'event'):
                Event.objects.filter(product=product).update(status=data['status'],
                                start_date=data['startDate'], end_date=data['endDate'])
            else:
                CulturalItem.objects.filter(product=product).update(price=data['price'])
    
        except Exception as e:
            return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_201_CREATED)

    def delete(self, request, type, pk, format=None):
        try:
            product = CulturalProduct.objects.get(product_id=pk)
            if (type == 'event'):
                event = Event.objects.get(product=product)
                event.delete()
            else:
                item = CulturalItem.objects.get(product=product)
                item.delete()
            product.delete()
        except Exception as e:
            return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_201_CREATED)

    def post(self, request, type, format=None):
        try:
            data = json.loads(request.body)
            domain = Domain.objects.get(id=data['domain'])
            organization = Organization.objects.get(id=data['organization'])
            product = CulturalProduct(product_id='1234', name=data['name'], slug=data['slug'],
                                description=data['description'], image_url=data['image_url'],
                                url=data['source_url'], product_type=data['product_type'], created_at=datetime.now(),
                                domain=domain, organization=organization)
            product.save()

            if (data['product_type'] == 'event'):
                event = Event(product=product, status=data['status'],
                                start_date=data['startDate'], end_date=data['endDate'])
                event.save()
            else:
                item = CulturalItem(product=product, price=data['price'])
                item.save()
    
        except Exception as e:
            return Response({'message': e}, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_201_CREATED)

class WebActivityList(APIView):
    """
    Create a new user. It's called 'UserList' because normally we'd have a get
    method here too, for retrieving a list of all User objects.
    """

    # permission_classes = (permissions.AllowAny,)

    def get(self, request, format=None):
        snippets = WebActivity.objects.all()
        serializer = WebActivitySerializer(snippets, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        print(request.data['anh'])
        return Response({}, status=status.HTTP_201_CREATED)
        # serializer = CulturalProductSerializer(data=request.data)
        # if serializer.is_valid():
        #     print(serializer.)
        #     serializer.save()
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
