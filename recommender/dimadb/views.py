from rest_framework import permissions, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import date, datetime
from django.forms.models import model_to_dict
from django.db.models import Q, Count, F
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
from django.apps import apps
from .serializers import *
from .models import *
from .content_based_recommender import ContentBasedRecommender

import random
import json
import uuid
import os
import pydash
import urllib3

#
module_dir = os.path.dirname(__file__)
item_detail_file_path = os.path.join(module_dir, 'item_detail.json')
item_list_file_path = os.path.join(module_dir, 'item_list.json')
mapping_file_path = os.path.join(module_dir, 'mapping.json')

def get_json_info(file_path, obj_key):
    json_file = open(file_path)
    json_obj = json.load(json_file)
    json_file.close()
    return pydash.get(json_obj, obj_key)

def assign_object_info(list_attributes, obj):
    new_obj = {}
    
    for attribute in list_attributes:
        attribute_info = list_attributes[attribute]
        value = ''
        
        #Get source value
        if 'default' in attribute_info:
            value = attribute_info['default']
        elif 'source_name' in attribute_info:
            if (pydash.get(obj, attribute_info['source_name'])):
                value = pydash.get(obj, attribute_info['source_name'])
            else:
                continue
        else:
            continue
        #Check data type
        #Assign value
        new_obj[attribute] = value
    return new_obj

@api_view(['GET'])
def home(request):
    try:
        #Initialize KPI reports
        web_activity_report = []
        event_report = []
        product_report = []
        traffics = {}

        #Total number of web activities (interactions)
        web_activities      = len(Interaction.objects.all())             
        #Total number of sessions (a session includes multiple interactions)                   
        sessions            = len(Interaction.objects.values('session_id').distinct())   
        #Total number of web activities by page location   
        pages   = list(Interaction.objects.all().values('page_location').annotate(total=Count('page_location')).order_by('-total'))  
        #Total number of web activities by device categories           
        device_categories   = Interaction.objects.all().values('device_category').annotate(total=Count('device_category'))       
        for category in list(device_categories):                                            
            type = category['device_category']
            traffics[type] = category['total']

        #Web activities report - Total number of web activities by event name
        web_activity_data = Interaction.objects.all().values('event_name').annotate(total=Count('event_name'))
        web_activity_report = [(item['event_name'], item['total']) for item in list(web_activity_data)]
        #Cultural event report  - Total number of cultural events by event type
        event_data = Events.objects.all().values('event_type').annotate(total=Count('event_type'))
        event_report = [(item['event_type'], item['total']) for item in list(event_data)]
        #Cutural product report - Total number of cultural products by product type
        product_data = Products.objects.all().values('product_type').annotate(total=Count('product_type'))
        product_report = [(item['product_type'], item['total']) for item in list(product_data)]

        #Add info for report to generate charts
        reports = [
            {
                'id': 'activity-chart',
                'title': 'Percentage of web activities by event name',
                'data': web_activity_report,
                'type': 'pie',
            },
            {
                'id': 'event-chart',
                'title': 'Percentage of evenement by type',
                'data': event_report,
                'type': 'column'
            },
            {
                'id': 'product-chart',
                'title': 'Percentage of article by type',
                'data': product_report,
                'type': 'column'
            },
        ]
        
        return Response({'reports': reports,
                         'sessions': sessions,
                         'webActivities': web_activities,
                         'traffic': traffics,
                         'pages': pages}, status=status.HTTP_200_OK)

    except Exception as exception:
        return Response({'message': exception})

# Get list of items (all rows) from a table
class ItemList(APIView):
    def get(self, request, item_type):
        try:
            #Read config file
            item_list_info = get_json_info(item_list_file_path, item_type)
            #Get info (model_name of item, list required fields to show, ...)
            model_name = item_list_info['model']
            fields = item_list_info['fields']
            view_detail = item_list_info['view_detail']
            
            Model = apps.get_model(app_label='dimadb', model_name=model_name)
            items = Model.objects.all().values(*fields)
            return Response({
                'items': items,
                'isViewDetail': view_detail,
            }, status=status.HTTP_200_OK)

        except Exception as exception:
            return Response({'message': exception})

#Get item detail (detail of a row) from a table
class ItemDetail(APIView):
    # Get info
    def get(self, request, item_type, pk, format=None):
        try:
            #Read config file
            item_detail_info = get_json_info(item_detail_file_path, item_type)
            #Get info (model_name of item, list of attributes of items, ...)
            model_name = item_detail_info['model_name']
            list_attributes = item_detail_info['list_attributes']
            list_foreign_attributes = item_detail_info['list_foreign_attributes']
            #Query item info from config info above
            item_form = create_item_form(model_name, pk, list_attributes, list_foreign_attributes)
            return Response(item_form)
        except Exception as exception:
            return Response({'message': exception})
    # Update info
    def put(self, request, item_type, pk, format=None):
        try:
            item_form = json.loads(request.body)
            update_item_info(item_form)
            return Response({'message': 'Update successfully'}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'message': exception})
    # Delete info
    def delete(self, request, item_type, pk, format=None):
        try:
            item_form = json.loads(request.body)
            delete_item_info(item_form)
            return Response({'message': 'Delete successfully'}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'message': exception})
    # New info
    def post(self, request, item_type, pk, format=None):
        try:
            item_form = json.loads(request.body)
            update_item_info(item_form)
            return Response({'message': 'Create successfully'}, status=status.HTTP_200_OK)
        except Exception as exception:
            return Response({'message': exception})
        
def get_model_object(model_name, pk):
    if (pk != 'form'):
        try:
            Model = apps.get_model(app_label='dimadb', model_name=model_name)
            event = Model.objects.get(id=pk)
            return model_to_dict(event)
        except Model.DoesNotExist:
            return {}
    else:
        return {}

def create_item_form(model_name, pk, list_attributes, list_foreign_tables):
    form_attributes = {}
    Model = apps.get_model(app_label='dimadb', model_name=model_name)
    obj = get_model_object(model_name, pk)

    #List attributes consists field names in primary table
    for attribute in list_attributes:
        form_attributes[attribute] = {}
        attribute_type = Model._meta.get_field(attribute).get_internal_type()   #Data type of field
        attribute_choices = Model._meta.get_field(attribute).choices            #If field has enum type => get selections
        # Assign value for each field of item
        if (attribute in obj.keys()):
            form_attributes[attribute]['value'] = obj[attribute]
        else:
            form_attributes[attribute]['value'] = ''
        # Assign data type for each field of item
        if (attribute_choices != None):
            form_attributes[attribute]['type'] = 'select'
            form_attributes[attribute]['choices'] = [
                value for (value, name) in attribute_choices]
        else:
            if (attribute_type == 'IntegerField'):
                form_attributes[attribute]['type'] = 'integer'
            elif (attribute_type == 'DecimalField'):
                form_attributes[attribute]['type'] = 'decimal'
            elif (attribute_type == 'TextField'):
                form_attributes[attribute]['type'] = 'textarea'
            elif (attribute_type == 'DateTimeField' or attribute_type == 'DateField'):
                if form_attributes[attribute]['value'] == '' or form_attributes[attribute]['value'] is None:
                    form_attributes[attribute]['value'] = ''
                else:
                    form_attributes[attribute]['value'] = form_attributes[attribute]['value'].strftime(
                        "%Y-%m-%d")
                form_attributes[attribute]['type'] = 'date'
            else:
                form_attributes[attribute]['type'] = 'text'

    #List foreign tables consists info of name, field names of foreign tables that hold additional of item
    for foreign_table in list_foreign_tables:
        #Get config info
        name = foreign_table['name']
        foreign_table_name = foreign_table['foreign_table']
        connected_table_name = foreign_table['connected_table']
        connected_field1 = foreign_table['connected_field1']
        connected_field2 = foreign_table['connected_field2']
        list_foreign_attributes = foreign_table['list_attributes']
        list_connected_attributes = foreign_table['list_connected_attributes']
        #Get array of foreign objects in foreign table
        form_attributes[name] = {}
        form_attributes[name]['type'] = 'array'
        form_attributes[name]['value'] = get_list_foreign_objects(foreign_table, obj)
        #Create form info for foreign table
        element_attributes = create_item_form(foreign_table_name, 'form', list_foreign_attributes, [])
        element_attributes['connectedAttributes'] = create_item_form(connected_table_name, 'form', list_connected_attributes, [])
        element_attributes['connectedAttributes']['connected_field1'] = connected_field1
        element_attributes['connectedAttributes']['connected_field2'] = connected_field2
        form_attributes[name]['elementAttributes'] = element_attributes

    form_info = {
        'type': 'object',
        'id': uuid.uuid4(),
        'attributes': form_attributes,
        'removed': False,
        'status': 'new' if pk == 'form' else 'created',
        'name': model_name
    }

    return form_info

def get_item_info(obj):
    new_obj = {}
    for attribute in obj.keys():
        if attribute != 'id':
            if obj[attribute]['type'] == 'array':
                next
            else:
                if obj[attribute]['type'] == 'integer' or obj[attribute]['type'] == 'decimal':
                    if obj[attribute]['value'] == '':
                        new_obj[attribute] = 0
                    else:
                        new_obj[attribute] = obj[attribute]['value']
                elif obj[attribute]['type'] == 'date' or obj[attribute]['type'] == 'datetime':
                    if obj[attribute]['value'] == '':
                        new_obj[attribute] = None
                    else:
                        new_obj[attribute] = obj[attribute]['value']
                else:
                    new_obj[attribute] = obj[attribute]['value']
    return new_obj

def update_item_info(form_info, connected_field1_id=None):
    status = form_info['status']
    obj_id = form_info['attributes']['id']['value']
    obj_info = get_item_info(form_info['attributes'])
    modelName = form_info['name']
    Model = apps.get_model(app_label='dimadb', model_name=modelName)

    if (status == 'new'):
        new_obj = Model(**obj_info)
        new_obj.save()
        update_list_foreign_objects(form_info['attributes'], new_obj.id)
        if ('connectedAttributes' in form_info.keys()):
            connected_field2_id = new_obj.id
            create_connected_object(form_info['connectedAttributes'], connected_field1_id, connected_field2_id)
    elif (status == 'created'):
        Model.objects.filter(id=obj_id).update(**obj_info)
        updated_obj = Model.objects.get(id=obj_id)
        update_list_foreign_objects(form_info['attributes'], updated_obj.id)
        if ('connectedAttributes' in form_info.keys()):
            update_item_info(form_info['connectedAttributes'])
    else:
        delete_item_info(form_info)

def delete_item_info(form_info):
    obj_id = form_info['attributes']['id']['value']
    if (id != ''):
        model_name = form_info['name']
        Model = apps.get_model(app_label='dimadb', model_name=model_name)
        Model.objects.filter(id=obj_id).delete()
        delete_list_foreign_objects(form_info['attributes'])
        if ('connectedAttributes' in form_info.keys()):
            delete_item_info(form_info['connectedAttributes'])

def get_list_foreign_objects(foreign_table, obj):
    foreign_forms = []
    if obj:
        #Get config info
        foreign_table_name = foreign_table['foreign_table']
        connected_table_name = foreign_table['connected_table']
        connected_field1 = foreign_table['connected_field1']
        connected_field2 = foreign_table['connected_field2']
        list_foreign_attributes = foreign_table['list_attributes']
        list_connected_attributes = foreign_table['list_connected_attributes']

        #Get connected model objects to query connected id
        ConnectedModel = apps.get_model(app_label='dimadb', model_name=connected_table_name)
        filter_params = {connected_field1: obj['id']}
        connected_objects = list(ConnectedModel.objects.filter(**filter_params))
        connected_objects = [model_to_dict(obj) for obj in connected_objects]

        #For each connected object (row) in connected table, query and create form for that connected object + foreign object
        for connected_obj in connected_objects:
            connected_form = create_item_form(connected_table_name, connected_obj['id'], list_connected_attributes, [])
            foreign_form = create_item_form(foreign_table_name, connected_obj[connected_field2], list_foreign_attributes, [])
            foreign_form['connectedAttributes'] = connected_form
            foreign_form['connectedAttributes']['connected_field1'] = connected_field1
            foreign_form['connectedAttributes']['connected_field2'] = connected_field2

            foreign_forms.append(foreign_form)

    return foreign_forms

def update_list_foreign_objects(obj, connected_field1_id=None):
    for attribute in obj.keys():
        if attribute != 'id':
            if obj[attribute]['type'] == 'array':
                list_values = obj[attribute]['value']
                for value in list_values:
                    update_item_info(value, connected_field1_id)

def delete_list_foreign_objects(obj, objId=None):
    for attribute in obj.keys():
        if attribute != 'id':
            if obj[attribute]['type'] == 'array':
                list_values = obj[attribute]['value']
                for value in list_values:
                    delete_item_info(value)

def create_connected_object(form_info, connected_field1_id, connected_field2_id):
    connected_field1 = form_info['connected_field1']
    connected_field2 = form_info['connected_field2']
    model_name = form_info['name']
    
    obj_info = get_item_info(form_info['attributes'])
    obj_info[connected_field1] = connected_field1_id
    obj_info[connected_field2] = connected_field2_id
    
    Model = apps.get_model(app_label='dimadb', model_name=model_name)
    obj = Model(**obj_info)
    obj.save()

def mapping_data(data, template):
    total = 0
    count = 0 
    try:
        if isinstance(data, list):
            total = len(data)
            
            import_info = ImportInfo(table_name=template['model_name'])
            import_info.save()
            import_info_id = import_info.id
            
            for obj in data:
                obj_info = assign_object_info(template['listAttributes'], obj)
                if obj_info:
                    count += 1
                    obj['import_id'] = import_info_id
                    Model = apps.get_model(app_label='dimadb', model_name=template['model_name'])
                    new_obj = Model(**obj_info)
                    new_obj.save()
                    new_obj_id = new_obj.id
                    
                    if ('list_foreign_attributes' in template):
                        for foreign_table in template['list_foreign_attributes']:
                            foreign_table_name = foreign_table['foreign_table']
                            connected_table_name = foreign_table['connected_table']
                            connected_field1 = foreign_table['connected_field1']
                            connected_field2 = foreign_table['connected_field2']
                            sources = foreign_table['sources']

                            for source in sources:
                                foreign_objs = []
                                if 'array' not in source:
                                    foreign_objs.append(obj)
                                else:
                                    if (pydash.get(obj, source['array'])):
                                        foreign_objs = pydash.get(obj, source['array'])
                                    
                                for foreign_obj in foreign_objs:
                                    foreign_obj_info = assign_object_info(source['listAttributes'], foreign_obj)
                                    if (foreign_obj_info):
                                        foreign_obj_info['import_id'] = import_info_id
                                        ForeignModel = apps.get_model(app_label='dimadb', model_name=foreign_table_name)
                                        new_foreign_obj = ForeignModel(**foreign_obj_info)
                                        new_foreign_obj.save()
                                        new_foreign_obj_id = new_foreign_obj.id

                                        if 'listConnectedAttributes' in source:
                                            connected_obj_info = assign_object_info(source['listConnectedAttributes'], foreign_obj)
                                            connected_obj_info[connected_field1] = new_obj_id
                                            connected_obj_info[connected_field2] = new_foreign_obj_id
                                            connected_obj_info['import_id'] = import_info_id
                                            ConnectedModel = apps.get_model(app_label='dimadb', model_name=connected_table_name)
                                            new_connected_obj = ConnectedModel(**connected_obj_info)
                                            new_connected_obj.save()
                     
                    if ('list_connected_attributes' in template):
                        for connected_table in template['list_connected_attributes']:
                            connected_table_name = connected_table['connected_table']
                            connected_field = connected_table['connected_field']
                            sources = connected_table['sources']

                            for source in sources:
                                connected_objs = []
                                if 'array' not in source:
                                    connected_objs.append(obj)
                                else:
                                    if (pydash.get(obj, source['array'])):
                                        connected_objs = pydash.get(obj, source['array'])
                                    
                                for connected_obj in connected_objs:
                                    connected_obj_info = assign_object_info(source['listAttributes'], connected_obj)
                                    if (connected_obj_info):
                                        connected_obj_info[connected_field] = new_obj_id
                                        connected_obj_info['import_id'] = import_info_id
                                        ConnectedModel = apps.get_model(app_label='dimadb', model_name=connected_table_name)
                                        new_connected_obj = ConnectedModel(**connected_obj_info)
                                        new_connected_obj.save()                              
            return {'message': 'Import successfully' + '.\n' + 'Import ' + str(count) + '/' + str(total) + 'object(s).'}
        else:
            return {'message': 'Wrong json format'}
    except Exception as error:
        return {'message': error + '.\n' + 'Import ' + str(count) + '/' + str(total) + 'object(s).'}

def reformated_data(json_data, item_type, template_type):
    try:
        reformated_json_data = []
        #Each item type & each template type => reformat differently
        if (item_type == 'web-activity' and template_type == 'default'):
            list_required_attributes = ['event_date', 'events', 'event_name', 'device', 'geo']
            list_required_event_params = ['ga_session_id', 'page_title', 'page_location']
            for obj in json_data:
                new_obj = {}
                for attribute in list_required_attributes:
                    if attribute == 'event_date':
                        date = pydash.get(obj, attribute)
                        format_date = date[:4] + '-' + date[4:6] + '-' + date[6:8]
                        new_obj[attribute] = format_date
                    else:
                        new_obj[attribute] = pydash.get(obj, attribute)
                
                for param in obj['event_params']:
                    key = param['key']
                    values = param['value']
                    if (key in list_required_event_params):
                        for value in values:
                            if values[value] != None:
                                new_obj[key] = values[value]
                            else:
                                continue
                reformated_json_data.append(new_obj)
        return reformated_json_data
    except Exception as exception:
        return exception                       
        
@api_view(['POST'])
def import_json_file(request, item_type):
    try:
        #Get config
        template_type = request.POST.get('template')
        files = request.FILES.getlist('files[]')
        file = files[0]
        json_data = json.load(file)
        
        if (template_type is None):
            template_type = 'default'
        
        #Get template configuration info    
        template = get_json_info(mapping_file_path, item_type + '.' + template_type)
        is_reformat = template['is_reformat']
        
        #Check reformat
        if is_reformat:
            json_data = reformated_data(json_data, item_type, template_type)
        
        #Mapping and saving in database
        mapping_result = mapping_data(json_data, template)    
        return Response(mapping_result, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['GET'])
def get_mapping_templates(request, item_type):
    try:
        list_templates = []
        json_file = open(mapping_file_path)
        json_obj = json.load(json_file)
        json_file.close()
        list_templates = [key for key in json_obj[item_type]]
        return Response({'listTemplates': list_templates}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['POST'])
def import_api(request):
    try:
        request_body = json.loads(request.body)
        item_type = request_body['itemType']
        url = request_body['url']
        bearer_token = request_body['bearerToken']
        template_type = request_body['template']
        # Get Data
        http = urllib3.PoolManager()
        header = {
            'Accept': '*/*'
        }
        if (bearer_token != ''):
            header['Authorization'] = 'Bearer ' + bearer_token
                 
        response = http.request('GET', url, headers=header)
        response_body = json.loads(response.data)
        response_data = response_body['data']
        # Import
        mapping_template = get_json_info(mapping_file_path, item_type + '.' + template_type)
        mapping_result = mapping_data(response_data, mapping_template)
        
        return Response(mapping_result, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['GET'])
def get_import_info(request, item_type):
    try:
        tables = {
            "event": "events",
            "article": "products",
            "web-activity": "interaction"
        }
        
        snippets = ImportInfo.objects.filter(table_name=tables[item_type])
        serializer = ImportInfoSerializer(snippets, many=True)
        return Response({'items': serializer.data}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['DELETE'])
def delete_multiple_items(request, item_type, pk):
    try:
        tables = {
            "event": ["events", "geolocation", "eventlocation", "resource", "eventresource", "businessentity", "entityeventrole"],
            "article": ["products", "resource", "productresource", "businessentity", "entityproductrole"],
            "web-activity": ["interaction", "geolocation", "interactionlocation", "eventpreference", "productpreference"]
        }
        
        for table in tables[item_type]:
            Model = apps.get_model(app_label='dimadb', model_name=table)
            Model.objects.filter(import_id=pk).delete()
        
        ImportInfo.objects.filter(id=pk).delete()    
        return Response({}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
def generate_recommend_api(level, item_type, recommend_type, quantity, domain, item_id):
    api = 'http://localhost:8000/dimadb/get-recommendation/?'
    
    api += 'level=' + level
    api += '&itemType=' + item_type
    api += '&quantity=' + quantity

    if (recommend_type):
        api += '&recommendType=' + recommend_type
    if (domain):
        api += '&domain=' + domain
    if (item_id):
        api += '&item=' + item_id
        
    return api  
    
def get_upcoming(table_name, sort_field, display_fields, quantity=1, domain=None):
    Model = apps.get_model(app_label='dimadb', model_name=table_name)
    list_recommend_items = []
    filter_params = {}
    
    if (sort_field != ''):
        today = datetime.today()
        sort_field_name = sort_field + '__gte'
        filter_params[sort_field_name] = today
    
    if (domain is not None):
        if (table_name == 'events'):
            filter_params['event_type'] = domain
        elif (table_name == 'products'):
            filter_params['product_type'] = domain
        
    list_objs = Model.objects.filter(Q(**filter_params)).order_by(sort_field)
    list_objs = list(list_objs)
    new_quantity = int(quantity)
    new_display_fields = list(display_fields)
    
    for i in range(0, new_quantity):
        if (i < len(list_objs)):
            obj = model_to_dict(list_objs[i])
            recommend_item = {}
            for field in new_display_fields:
                recommend_item[field] = obj[field]
            list_recommend_items.append(recommend_item)
        
    return list_recommend_items

def get_most_popular(table_name, sort_field, display_fields, quantity=1, domain=None):
    Model = apps.get_model(app_label='dimadb', model_name=table_name)
    list_recommend_items = [] 
    filter_params = {}
    
    if (sort_field != ''):
        today = datetime.today()
        sort_field_name = sort_field + '__gte'
        filter_params[sort_field_name] = today
    
    if (domain is not None):
        if (table_name == 'events'):
            filter_params['event_type'] = domain
        elif (table_name == 'products'):
            filter_params['product_type'] = domain
        
    list_objs = Model.objects.filter(Q(**filter_params))
    list_objs = [model_to_dict[obj] for obj in list(list_objs)]
    list_new_objs = []
    
    for obj in list_objs:
        score = 0
        list_item_activities = []
        
        if (table_name == 'events'):
            list_item_activities = EventPreference.objects.filter(event_id=obj['event_id'])
        elif (table_name == 'products'):
            list_item_activities = ProductPreference.objects.filter(product_id=obj['product_id'])
        
        for item_activity in list(list_item_activities):
            item_activity = model_to_dict(item_activity)
            try:
                activity = Interaction.objects.get(id=item_activity['activity_id'])
                activity_type = model_to_dict(activity)
                activity_type = activity_type['event_name']
                try:
                    activity_weight = WebActivityType.objects.get(name=activity_type)
                    score = score + model_to_dict(activity_weight)['value']
                except:
                    pass
            except:
                pass
        
        obj['score'] = score
        list_new_objs.append(obj)
    
    list_new_objs = sorted(list_new_objs, key=lambda d: d['score'], reverse=True)
    new_quantity = int(quantity)
    new_display_fields = list(display_fields)
    
    for i in range(0, new_quantity):
        if (i < len(list_new_objs)):
            obj = list_new_objs[i]
            recommend_item = {}
            for field in new_display_fields:
                recommend_item[field] = obj[field]
            list_recommend_items.append(recommend_item)
        
    return list_recommend_items
    
def get_similar(table_name, sort_field, display_fields, quantity=1, item_id=None):
    Model = apps.get_model(app_label='dimadb', model_name=table_name)
    list_similar = ContentBasedRecommender.recommend_items_by_items(table_name=table_name, items_id=item_id)
    new_quantity = int(quantity)
    new_display_fields = list(display_fields)
    list_recommend_items = []
    
    for i in range(0, new_quantity):
        if (i < len(list_similar)):
            similar_obj = list_similar[i]
            obj = Model.objects.get(id=similar_obj['id'])
            obj = model_to_dict(obj)
            obj['similarity'] = similar_obj['similarity']
            recommend_item = {}
            for field in new_display_fields:
                recommend_item[field] = obj[field]
            list_recommend_items.append(recommend_item)
            
    return list_recommend_items
      
def get_recommend_items(level, item_type, recommend_type, quantity, domain, item_id):
    list_recommend_items = []
    display_fields = {
        'Upcomming': {
            'events': ['id', 'event_id', 'event_name', 'event_title', 'next_date', 'description'] 
        }, 
        'Most popular': {
            'events': ['id', 'event_id', 'event_name', 'event_title', 'score', 'description'],
            'products': ['id', 'product_id', 'product_name', 'score', 'description']
        },
        'Similar': {
            'events': ['id', 'event_id', 'event_name', 'event_title', 'next_date', 'similarity', 'description'],
            'products': ['id', 'product_id', 'product_name', 'similarity', 'description'],
        }
    }
    
    if (level == 'General'):
        if (recommend_type == 'Upcomming'):
            if (item_type == 'events'):
                list_recommend_items = get_upcoming(table_name=item_type, sort_field='next_date', display_fields=display_fields[recommend_type][item_type], quantity=quantity)
        if (recommend_type == 'Most popular'):
            if (item_type == 'events'):
                list_recommend_items = get_most_popular(table_name=item_type, sort_field='next_date', display_fields=display_fields[recommend_type][item_type], quantity=quantity)
            elif (item_type == 'products'):
                list_recommend_items = get_most_popular(table_name=item_type, sort_field='', display_fields=display_fields[recommend_type][item_type], quantity=quantity)
    elif (level == 'Domain'):
        if (recommend_type == 'Upcomming'):
            if (item_type == 'events'):
                list_recommend_items = get_upcoming(table_name=item_type, sort_field='next_date', display_fields=display_fields[recommend_type][item_type], quantity=quantity, domain=domain)
        if (recommend_type == 'Most popular'):
            if (item_type == 'events'):
                list_recommend_items = get_most_popular(table_name=item_type, sort_field='next_date', display_fields=display_fields[recommend_type][item_type], quantity=quantity, domain=domain)
            elif (item_type == 'products'):
                list_recommend_items = get_most_popular(table_name=item_type, sort_field='', display_fields=display_fields[recommend_type][item_type], quantity=quantity, domain=domain)
    else:
        if (item_type == 'events'):
            list_recommend_items = get_similar(table_name=item_type, sort_field='next_date', display_fields=display_fields['Similar'][item_type], quantity=quantity, item=item_id)
        elif (item_type == 'products'):
            list_recommend_items = get_similar(table_name=item_type, sort_field='', display_fields=display_fields['Similar'][item_type], quantity=quantity, item=item_id)

    return list_recommend_items

@api_view(['GET'])
@authentication_classes([])
@permission_classes([])
def get_recommendation(request):
    try:
        level = request.GET.get('level', None)
        item_type = request.GET.get('itemType', None)
        recommend_type = request.GET.get('recommendType', None)
        quantity = request.GET.get('quantity', None)
        domain = request.GET.get('domain', None)
        item_id = request.GET.get('item', None)
        list_recommend_items = get_recommend_items(level, item_type, recommend_type, quantity, domain, item_id)
        return Response({'items': list_recommend_items}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['POST'])
def get_recommend_api(request):
    try:
        body = json.loads(request.body)
        level = body['level']
        item_type = body['itemType']
        recommend_type = body['recommendType']
        quantity = body['quantity']
        domain = body['domain']
        item_id = body['item']
        
        api = generate_recommend_api(level, item_type, recommend_type, quantity, domain, item_id)
        list_recommend_items = get_recommend_items(level, item_type, recommend_type, quantity, domain, item_id)
        
        return Response({'items': list_recommend_items, 'api': api}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})

@api_view(['POST'])
def train_similar_recommend(request):
    try:
        body = json.loads(request.body)
        item_type = body['itemType']
        
        #Training
        ContentBasedRecommender.train_items_by_items(table_name=item_type)
        #Get similarity recommendation training info
        similar_train_info = get_similar_train_info()
        return Response({'similarTrainInfo': similar_train_info}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})   
        
@api_view(['GET'])
def get_recommend_info(request):
    try:
        event_snippets = Events.objects.all()
        event_serializer = EventSerializer(event_snippets, many=True)
        
        article_snippets = Products.objects.all()
        article_serializer = ArticleSerializer(article_snippets, many=True)
        
        event_types = Events.objects.values('event_type').distinct()
        article_types = Products.objects.values('product_type').distinct()
        
        event_types = [item['event_type'] for item in list(event_types)]
        article_types = [item['product_type'] for item in list(article_types)]
         
        return Response({'events': event_serializer.data, 
                         'products': article_serializer.data,
                         'eventTypes': event_types,
                         'articleTypes': article_types}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
def get_similar_train_info():
    try:
        list_item_types = [{'name': 'Événement', 'value': 'events'},
                           {'name': 'Article', 'value': 'products'}]
        
        for item_type in list_item_types:
            if (LdaSimilarityVersion.objects.filter(item_type=item_type['value']).exists()):
                obj = LdaSimilarityVersion.objects.filter(item_type=item_type['value']).latest('created_at')
                item_type['latest_training_at'] = str(obj)
                item_type['number_trained_items'] = model_to_dict(obj)['n_products']
            else:
                item_type['latest_training_at'] = ''
                item_type['number_trained_items'] = 0
        
        return list_item_types
    except Exception as error:
        return Response({'message': error})
        
@api_view(['GET'])
def get_configure_info(request):
    try:
        similar_train_info = get_similar_train_info()
        
        web_activity_types = Interaction.objects.values('event_name').distinct()
        web_activity_types = [item['event_name'] for item in list(web_activity_types)]
        existed_web_activity_types = WebActivityType.objects.values('name').distinct()
        existed_web_activity_types = [item['name'] for item in list(existed_web_activity_types)]
        
        web_activity_types = web_activity_types + existed_web_activity_types
        web_activity_types = list(dict.fromkeys(web_activity_types))
        
        web_activities_info = {}
        for activity_type in web_activity_types:
            try:
                activity_type_obj = WebActivityType.objects.get(name=activity_type)
                activity_type_obj = model_to_dict(activity_type_obj)
                web_activities_info[type] = activity_type_obj['value']
            except:
                web_activities_info[type] = 0
        
        return Response({'similarTrainInfo': similar_train_info, 'webActivityInfo': web_activities_info}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['POST'])
def update_activity_weight(request):
    try:
        body = json.loads(request.body)
        web_activity_types = body['webActivityInfo']
        
        for type in web_activity_types:
            try:
                WebActivityType.objects.filter(name=type).update(value=web_activity_types[type])
            except:
                new_activity_type = WebActivityType(name=type, value=web_activity_types[type])
                new_activity_type.save()
        
        return Response({}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})
    
@api_view(['GET'])
def get_reports(request):
    try: 
        start_date = request.GET.get('startDate', date.today())
        end_date = request.GET.get('endDate', date.today())
        group_type = request.GET.get('groupBy', 'daily')
        
        reports = []
        # Session:
        if (group_type == 'none'):
            web_activities = [{'type': 'all', 'sum': Interaction.objects.filter(visit_date__range=[start_date, end_date]).values('session_id').distinct().count()}]
        elif (group_type == 'daily'):
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(day=F('visit_date')).annotate(sum=Count('session_id', distinct=True))
        elif (group_type == 'weekly'):
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(week=TruncWeek('visit_date')).values('week').annotate(sum=Count('session_id', distinct=True))
        elif (group_type == 'monthly'):
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(month=TruncMonth('visit_date')).values('month').annotate(sum=Count('session_id', distinct=True))
        else:
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(year=TruncYear('visit_date')).values('year').annotate(sum=Count('session_id', distinct=True))        
        reports.append(create_report('session_report', 'The total number of web_activities', web_activities, 'column', group_type == 'none'))
        
        # Web_activities:
        if (group_type == 'none'):
            web_activities = [{'type': 'all', 'sum': Interaction.objects.filter(visit_date__range=[start_date, end_date]).all().count()}]
        elif (group_type == 'daily'):
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(day=F('visit_date')).annotate(sum=Count('id'))
        elif (group_type == 'weekly'):
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(week=TruncWeek('visit_date')).values('week').annotate(sum=Count('id'))
        elif (group_type == 'monthly'):
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(month=TruncMonth('visit_date')).values('month').annotate(sum=Count('id'))
        else:
            web_activities = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(year=TruncYear('visit_date')).values('year').annotate(sum=Count('id'))        
        reports.append(create_report('web_activities_report', 'The total number of web activities', web_activities, 'column', group_type == 'none'))
        
        # Web Activities device_category:
        if (group_type == 'none'):
            web_activities_device = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(type=F('device_category')).annotate(sum=Count('id'))
        elif (group_type == 'daily'):
            web_activities_device = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(day=F('visit_date'), type=F('device_category')).annotate(sum=Count('id'))
        elif (group_type == 'weekly'):
            web_activities_device = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(week=TruncWeek('visit_date')).values('week', type=F('device_category')).annotate(sum=Count('id'))
        elif (group_type == 'monthly'):
            web_activities_device = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(month=TruncMonth('visit_date')).values('month', type=F('device_category')).annotate(sum=Count('id'))
        else:
            web_activities_device = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(year=TruncYear('visit_date')).values('year', type=F('device_category')).annotate(sum=Count('id'))        
        reports.append(create_report('session_device_report', 'The total number of web activities by device category', web_activities_device, 'column', group_type == 'none'))
        
        # Web Activities browser:
        if (group_type == 'none'):
            web_activities_browser = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(type=F('browser')).annotate(sum=Count('id'))
        elif (group_type == 'daily'):
            web_activities_browser = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(day=F('visit_date'), type=F('browser')).annotate(sum=Count('id'))
        elif (group_type == 'weekly'):
            web_activities_browser = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(week=TruncWeek('visit_date')).values('week', type=F('browser')).annotate(sum=Count('id'))
        elif (group_type == 'monthly'):
            web_activities_browser = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(month=TruncMonth('visit_date')).values('month', type=F('browser')).annotate(sum=Count('id'))
        else:
            web_activities_browser = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(year=TruncYear('visit_date')).values('year', type=F('browser')).annotate(sum=Count('id'))        
        reports.append(create_report('session_browser_report', 'The total number of web activities by browser', web_activities_browser, 'column', group_type == 'none'))
        
        # Web Activities os:
        if (group_type == 'none'):
            web_activities_os = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(type=F('operating_system')).annotate(sum=Count('id'))
        elif (group_type == 'daily'):
            web_activities_os = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(day=F('visit_date'), type=F('operating_system')).annotate(sum=Count('id'))
        elif (group_type == 'weekly'):
            web_activities_os = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(week=TruncWeek('visit_date')).values('week', type=F('operating_system')).annotate(sum=Count('id'))
        elif (group_type == 'monthly'):
            web_activities_os = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(month=TruncMonth('visit_date')).values('month', type=F('operating_system')).annotate(sum=Count('id'))
        else:
            web_activities_os = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(year=TruncYear('visit_date')).values('year', type=F('operating_system')).annotate(sum=Count('id'))        
        reports.append(create_report('session_os_report', 'The total number of web activities by operating system', web_activities_os, 'column', group_type == 'none'))
        
        # Web Activities type:
        if (group_type == 'none'):
            web_activities_type = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(type=F('event_name')).annotate(sum=Count('id'))
        elif (group_type == 'daily'):
            web_activities_type = Interaction.objects.filter(visit_date__range=[start_date, end_date]).values(day=F('visit_date'), type=F('event_name')).annotate(sum=Count('id'))
        elif (group_type == 'weekly'):
            web_activities_type = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(week=TruncWeek('visit_date')).values('week', type=F('event_name')).annotate(sum=Count('id'))
        elif (group_type == 'monthly'):
            web_activities_type = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(month=TruncMonth('visit_date')).values('month', type=F('event_name')).annotate(sum=Count('id'))
        else:
            web_activities_type = Interaction.objects.filter(visit_date__range=[start_date, end_date]).annotate(year=TruncYear('visit_date')).values('year', type=F('event_name')).annotate(sum=Count('id'))        
        reports.append(create_report('session_activity_report', 'The total number of web activities by type', web_activities_type, 'column', group_type == 'none'))
        
        return Response({'reports': reports}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({'message': error})

def create_report(name, title, data, chart_type, is_change):
    return {
        'name': name,
        'title': title,
        'data': data,
        'type': chart_type,
        'isChange': is_change,
        'random': name + str(random.randint(0,1000)),
    }
