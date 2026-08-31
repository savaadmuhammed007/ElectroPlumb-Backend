from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, GoogleAuthView, UserProfileView, ChangePasswordView,
    ItemListView, ItemDetailView,
    MaterialListViewSet, MaterialListDetailView, DuplicateMaterialListView,
    AdminStatsView, ItemExportView, ItemImportView, ItemTemplateView,
    GoogleSheetCatalogSyncView, GoogleSheetPushView, ItemClearView
)

urlpatterns = [
    # Auth Endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/google/', GoogleAuthView.as_view(), name='google_auth'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('profile/', UserProfileView.as_view(), name='profile'),

    # Item Catalog Endpoints
    path('items/', ItemListView.as_view(), name='item_list'),
    path('items/<int:pk>/', ItemDetailView.as_view(), name='item_detail'),

    # Admin Item Import / Export / Google Sheets Sync Endpoints
    path('admin/items/export/', ItemExportView.as_view(), name='item_export'),
    path('admin/items/import/', ItemImportView.as_view(), name='item_import'),
    path('admin/items/template/', ItemTemplateView.as_view(), name='item_template'),
    path('admin/items/clear/', ItemClearView.as_view(), name='item_clear'),
    path('admin/items/google-sheet-sync/', GoogleSheetCatalogSyncView.as_view(), name='google_sheet_sync'),
    path('admin/items/google-sheet-push/', GoogleSheetPushView.as_view(), name='google_sheet_push'),

    # Material List Endpoints
    path('lists/', MaterialListViewSet.as_view(), name='material_lists'),
    path('lists/<int:pk>/', MaterialListDetailView.as_view(), name='material_list_detail'),
    path('lists/<int:pk>/duplicate/', DuplicateMaterialListView.as_view(), name='material_list_duplicate'),

    # Admin Stats Endpoint
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
]
