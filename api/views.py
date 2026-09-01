import csv
import io
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile, Item, MaterialList, ListItem
from .serializers import (
    UserSerializer, RegisterSerializer, UserProfileSerializer,
    ItemSerializer, MaterialListSerializer, ListItemSerializer
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class GoogleAuthView(APIView):
    """
    Handles Google OAuth sign-in and token verification.
    Finds or creates a Django User and returns JWT tokens.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        credential = request.data.get('credential')
        email = request.data.get('email')
        name = request.data.get('name', '')
        picture = request.data.get('picture', '')
        role = request.data.get('role', 'electrician')

        # If credential (Google ID Token) provided, verify with Google Tokeninfo
        if credential:
            try:
                verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                req = urllib.request.Request(verify_url, headers={'User-Agent': 'ElectroPlumb-Auth/1.0'})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    email = data.get('email') or email
                    name = data.get('name') or name
                    picture = data.get('picture') or picture
                    email_verified = data.get('email_verified')
                    if email_verified not in [True, 'true', 'True', None]:
                        return Response({"error": "Google email is not verified."}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # If network or token verification failed, only fallback if explicit email passed
                if not email:
                    return Response({"error": f"Failed to verify Google token: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        if not email:
            return Response({"error": "No email provided with Google authentication."}, status=status.HTTP_400_BAD_REQUEST)

        # Look up existing user by email
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            # Create user
            base_username = email.split('@')[0].replace('.', '_').replace('-', '_')
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            first_name = name or base_username.capitalize()
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                password=User.objects.make_random_password()
            )
            UserProfile.objects.create(
                user=user,
                role=role if role in ['electrician', 'plumber'] else 'electrician',
                profile_photo=picture or ''
            )
        else:
            # Ensure user has profile
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if picture and not profile.profile_photo:
                profile.profile_photo = picture
                profile.save()

        # Generate JWT Tokens
        refresh = RefreshToken.for_user(user)
        user_data = UserSerializer(user).data

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_data
        }, status=status.HTTP_200_OK)



class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password updated successfully."})


class ItemListView(generics.ListCreateAPIView):
    serializer_class = ItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Item.objects.all()
        item_type = self.request.query_params.get('item_type')
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        status_param = self.request.query_params.get('status')

        if not self.request.user.is_authenticated or not self.request.user.is_staff:
            # Regular users see active items only
            queryset = queryset.filter(status='active')
        elif status_param and status_param != 'all':
            queryset = queryset.filter(status=status_param)

        if item_type:
            queryset = queryset.filter(item_type=item_type)
        if category:
            queryset = queryset.filter(category__iexact=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(item_code__icontains=search) |
                Q(category__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise permissions.PermissionDenied("Authentication required to add items.")
        serializer.save()


class ItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only admins can modify items.")
        serializer.save()

    def perform_destroy(self, instance):
        if not self.request.user.is_staff:
            raise permissions.PermissionDenied("Only admins can delete items.")
        instance.delete()


class MaterialListViewSet(generics.ListCreateAPIView):
    serializer_class = MaterialListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = MaterialList.objects.filter(user=user)

        list_type = self.request.query_params.get('list_type')
        search = self.request.query_params.get('search')

        if list_type:
            queryset = queryset.filter(list_type=list_type)
        if search:
            queryset = queryset.filter(
                Q(client_name__icontains=search) |
                Q(location__icontains=search) |
                Q(project_name__icontains=search)
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MaterialListDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MaterialListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MaterialList.objects.filter(user=self.request.user)


class DuplicateMaterialListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            original = MaterialList.objects.get(pk=pk, user=request.user)
        except MaterialList.DoesNotExist:
            return Response({"error": "Material list not found."}, status=status.HTTP_404_NOT_FOUND)

        new_list = MaterialList.objects.create(
            user=request.user,
            list_type=original.list_type,
            client_name=f"{original.client_name} (Copy)",
            client_phone=original.client_phone,
            project_name=original.project_name,
            location=original.location,
            date=datetime.now().strftime("%d %B %Y"),
            notes=original.notes
        )

        for item in original.items.all():
            ListItem.objects.create(
                material_list=new_list,
                item=item.item,
                item_name=item.item_name,
                category=item.category,
                unit=item.unit,
                quantity=item.quantity
            )

        serializer = MaterialListSerializer(new_list)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.now().date()

        total_users = User.objects.count()
        total_electrical_items = Item.objects.filter(item_type='electrical').count()
        total_plumbing_items = Item.objects.filter(item_type='plumbing').count()
        total_lists = MaterialList.objects.count()
        electrical_lists = MaterialList.objects.filter(list_type='electrical').count()
        plumbing_lists = MaterialList.objects.filter(list_type='plumbing').count()
        lists_today = MaterialList.objects.filter(created_at__date=today).count()

        recent_users = UserSerializer(User.objects.order_by('-date_joined')[:5], many=True).data

        return Response({
            "total_users": total_users,
            "total_electrical_items": total_electrical_items,
            "total_plumbing_items": total_plumbing_items,
            "total_lists": total_lists,
            "electrical_lists": electrical_lists,
            "plumbing_lists": plumbing_lists,
            "lists_today": lists_today,
            "recent_users": recent_users
        })


class ItemExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def perform_content_negotiation(self, request, force=False):
        return (None, None)

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        format_type = request.query_params.get('format', 'csv').lower()
        item_type = request.query_params.get('item_type')

        queryset = Item.objects.all()
        if item_type and item_type in ['electrical', 'plumbing']:
            queryset = queryset.filter(item_type=item_type)

        if format_type == 'json':
            serializer = ItemSerializer(queryset, many=True)
            response = HttpResponse(json.dumps(serializer.data, indent=2), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="materials_export_{item_type or "all"}.json"'
            return response

        # Default CSV export
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="materials_export_{item_type or "all"}.csv"'

        writer = csv.writer(response)
        writer.writerow(['item_code', 'name', 'item_type', 'category', 'unit', 'description', 'status'])

        for item in queryset:
            writer.writerow([
                item.item_code,
                item.name,
                item.item_type,
                item.category,
                item.unit,
                item.description or '',
                item.status
            ])

        return response


class ItemClearView(APIView):
    """
    Deletes all items in catalog or filtered by item_type ('electrical', 'plumbing', 'all').
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        item_type = request.data.get('item_type')
        if item_type in ['electrical', 'plumbing']:
            count, _ = Item.objects.filter(item_type=item_type).delete()
            return Response({
                "message": f"Successfully cleared all {item_type} catalog materials ({count} items deleted).",
                "deleted_count": count
            }, status=status.HTTP_200_OK)
        else:
            count, _ = Item.objects.all().delete()
            return Response({
                "message": f"Successfully cleared all catalog materials ({count} items deleted).",
                "deleted_count": count
            }, status=status.HTTP_200_OK)



class ItemImportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        items_to_process = []
        created_count = 0
        updated_count = 0
        errors = []

        # Check if CSV file uploaded via form data
        if 'file' in request.FILES:
            csv_file = request.FILES['file']
            if not csv_file.name.endswith('.csv'):
                return Response({"error": "Only CSV files are allowed."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                for row in reader:
                    items_to_process.append(row)
            except Exception as e:
                return Response({"error": f"Failed to parse CSV file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Or JSON array in request body
        elif isinstance(request.data, list):
            items_to_process = request.data
        elif isinstance(request.data.get('items'), list):
            items_to_process = request.data.get('items')
        else:
            return Response({"error": "Provide a CSV file or JSON array of items."}, status=status.HTTP_400_BAD_REQUEST)

        # Process each item
        for idx, row in enumerate(items_to_process, start=1):
            name = row.get('name', '').strip()
            item_code = row.get('item_code', '').strip()
            item_type = row.get('item_type', 'electrical').strip().lower()
            category = row.get('category', 'General').strip()
            unit = row.get('unit', 'Piece').strip()
            description = row.get('description', '').strip()
            status_val = row.get('status', 'active').strip().lower()

            if not name or not item_code:
                errors.append(f"Row {idx}: Missing name or item_code.")
                continue

            if item_type not in ['electrical', 'plumbing']:
                item_type = 'electrical'

            if status_val not in ['active', 'disabled']:
                status_val = 'active'

            item, created = Item.objects.update_or_create(
                item_code=item_code,
                defaults={
                    'name': name,
                    'item_type': item_type,
                    'category': category,
                    'unit': unit,
                    'description': description,
                    'status': status_val,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response({
            "message": "Bulk import completed.",
            "created": created_count,
            "updated": updated_count,
            "errors": errors
        }, status=status.HTTP_200_OK)


class ItemTemplateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="materials_import_template.csv"'

        writer = csv.writer(response)
        writer.writerow(['item_code', 'name', 'item_type', 'category', 'unit', 'description', 'status'])
        writer.writerow(['ELE-SAMPLE-01', 'Sample 1.5mm Wire', 'electrical', 'Wires & Cables', 'Meter', 'Sample electrical wire description', 'active'])
        writer.writerow(['PLM-SAMPLE-01', 'Sample CPVC Pipe 1 inch', 'plumbing', 'Pipes', 'Length', 'Sample CPVC pipe description', 'active'])

        return response

def normalize_google_sheet_url(url):
    """
    Transforms any standard Google Sheet URL or published link into a direct CSV export endpoint.
    """
    url = url.strip()
    if not url:
        return None

    # If already a direct csv export URL
    if 'output=csv' in url or 'format=csv' in url or 'out:csv' in url:
        return url

    # Pattern for /spreadsheets/d/e/2PACX-.../pub
    if '/spreadsheets/d/e/' in url:
        base = url.split('?')[0].rstrip('/')
        if not base.endswith('/pub'):
            base = base + '/pub'
        return f"{base}?output=csv"

    # Pattern for /spreadsheets/d/{ID}/...
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if match:
        sheet_id = match.group(1)
        # Extract gid if present (e.g. gid=123456)
        gid_match = re.search(r'[#&?]gid=([0-9]+)', url)
        gid = gid_match.group(1) if gid_match else '0'
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    return url


class GoogleSheetCatalogSyncView(APIView):
    """
    Synchronizes the item catalog database directly with a live Google Sheet.
    Accepts { "sheet_url": "https://docs.google.com/spreadsheets/d/..." }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        sheet_url = request.data.get('sheet_url', '').strip()
        if not sheet_url:
            return Response({"error": "Please provide a valid Google Sheet URL."}, status=status.HTTP_400_BAD_REQUEST)

        csv_url = normalize_google_sheet_url(sheet_url)
        if not csv_url:
            return Response({"error": "Could not parse Google Sheet URL. Please ensure it is a valid Google Docs Spreadsheet link."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            req = urllib.request.Request(
                csv_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return Response({"error": "Google Sheet not found. Please check the spreadsheet URL."}, status=status.HTTP_400_BAD_REQUEST)
            elif e.code in (401, 403):
                return Response({"error": "Access denied by Google. Please ensure General Access on your Google Sheet is set to 'Anyone with the link can view'."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": f"Failed to fetch from Google Sheets (HTTP {e.code}). Please ensure the sheet is accessible with 'Anyone with the link can view'."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Network error connecting to Google Sheets: {str(e)}. Please check your internet connection and sheet link."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if Google returned HTML login page instead of CSV
        if '<html' in content.lower() or '<!doctype' in content.lower():
            return Response({
                "error": "Google Sheet returned a login page. Please set the spreadsheet sharing permission: Click 'Share' -> 'General access' -> 'Anyone with the link' -> 'Viewer'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Parse CSV content
        try:
            io_string = io.StringIO(content)
            reader = csv.DictReader(io_string)
        except Exception as e:
            return Response({"error": f"Failed to read CSV data from Google Sheet: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
        if not fieldnames:
            return Response({"error": "The Google Sheet appears to be empty or has no header row."}, status=status.HTTP_400_BAD_REQUEST)

        created_count = 0
        updated_count = 0
        errors = []

        for idx, raw_row in enumerate(reader, start=2):
            if not raw_row:
                continue
            # Normalize keys to lowercase
            row = {k.strip().lower(): v.strip() if isinstance(v, str) else '' for k, v in raw_row.items() if k}
            
            # Match fields flexibly
            item_code = row.get('item_code') or row.get('code') or row.get('item code') or row.get('itemcode')
            name = row.get('name') or row.get('item_name') or row.get('item name') or row.get('material') or row.get('material name')
            item_type = (row.get('item_type') or row.get('type') or row.get('trade') or 'electrical').lower()
            category = row.get('category') or row.get('cat') or 'General'
            unit = row.get('unit') or row.get('unit metric') or 'Piece'
            description = row.get('description') or row.get('desc') or ''
            status_val = (row.get('status') or 'active').lower()

            if not name or not item_code:
                # If completely empty row, skip without logging error
                if not any(row.values()):
                    continue
                errors.append(f"Row {idx}: Missing item_code or name.")
                continue

            if item_type not in ['electrical', 'plumbing']:
                item_type = 'electrical'

            if status_val not in ['active', 'disabled']:
                status_val = 'active'

            item, created = Item.objects.update_or_create(
                item_code=item_code,
                defaults={
                    'name': name,
                    'item_type': item_type,
                    'category': category,
                    'unit': unit,
                    'description': description,
                    'status': status_val,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        return Response({
            "message": f"Successfully synchronized with Google Sheets! {created_count} items created, {updated_count} items updated.",
            "created": created_count,
            "updated": updated_count,
            "total_synced": created_count + updated_count,
            "errors": errors
        }, status=status.HTTP_200_OK)


class GoogleSheetPushView(APIView):
    """
    Pushes catalog items from the database directly into a user's Google Sheet
    via a Google Apps Script Web App URL.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)

        webhook_url = request.data.get('webhook_url', '').strip()
        if not webhook_url:
            return Response({"error": "Please provide your Google Apps Script Web App URL."}, status=status.HTTP_400_BAD_REQUEST)

        action = request.data.get('action', 'sync_all') # 'sync_all' | 'add_item'

        payload = {
            'action': action,
            'timestamp': timezone.now().isoformat()
        }

        if action == 'sync_all':
            # Collect all items or filtered items from DB if not supplied
            items_data = request.data.get('items')
            if not items_data:
                item_type = request.data.get('item_type')
                queryset = Item.objects.all()
                if item_type in ['electrical', 'plumbing']:
                    queryset = queryset.filter(item_type=item_type)
                serializer = ItemSerializer(queryset, many=True)
                items_data = serializer.data
            payload['items'] = items_data
            payload['count'] = len(items_data)
        elif action == 'add_item':
            item_data = request.data.get('item')
            if not item_data:
                return Response({"error": "Missing item data to add."}, status=status.HTTP_400_BAD_REQUEST)
            payload['item'] = item_data
        else:
            return Response({"error": f"Invalid action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

        # Dispatch to Google Apps Script Web App
        try:
            json_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=json_bytes,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                resp_text = response.read().decode('utf-8')
                try:
                    resp_json = json.loads(resp_text)
                except Exception:
                    resp_json = {"raw": resp_text}

            return Response({
                "message": f"Successfully pushed data to Google Sheet ({action})!",
                "details": resp_json,
                "count": payload.get('count', 1)
            }, status=status.HTTP_200_OK)

        except urllib.error.HTTPError as e:
            return Response({
                "error": f"Google Apps Script returned HTTP {e.code}. Please ensure your Web App deployment is configured with access set to 'Anyone'."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "error": f"Failed to push to Google Sheet: {str(e)}. Please check your Web App URL."
            }, status=status.HTTP_400_BAD_REQUEST)



