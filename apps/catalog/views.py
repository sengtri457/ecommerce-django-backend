from django.db.models import Q
from rest_framework import viewsets, generics
from rest_framework.response import Response
from apps.catalog.models import Category, Product
from apps.catalog.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    pagination_class = None

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_field = 'slug'

    def get_queryset(self):
        qs = Product.objects.filter(is_active=True).select_related('category').prefetch_related('variants', 'images')

        # Filter by department
        dept = self.request.query_params.get('department')
        if dept and dept != 'all':
            qs = qs.filter(department=dept)

        # Filter by audience
        audience = self.request.query_params.get('audience')
        if audience and audience != 'all':
            qs = qs.filter(audience=audience)

        # Filter by category slug
        category_slug = self.request.query_params.get('category')
        if category_slug and category_slug != 'all':
            qs = qs.filter(Q(category__slug=category_slug) | Q(category__parent__slug=category_slug))

        # Filter by subcategory
        subcat = self.request.query_params.get('subcategory')
        if subcat and subcat != 'all':
            qs = qs.filter(subcategory=subcat)

        # Search term
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search) | Q(fabric__icontains=search))

        # Sorting
        sort = self.request.query_params.get('sort')
        if sort == 'price_asc':
            qs = qs.order_by('base_price')
        elif sort == 'price_desc':
            qs = qs.order_by('-base_price')
        elif sort == 'newest':
            qs = qs.order_by('-created_at')

        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_object(self):
        # Support lookup by either slug or integer ID
        lookup_value = self.kwargs[self.lookup_field]
        queryset = self.get_queryset()
        if lookup_value.isdigit():
            obj = queryset.filter(id=int(lookup_value)).first()
            if obj:
                return obj
        return queryset.filter(slug=lookup_value).first() or super().get_object()
