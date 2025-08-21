from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Supplier, Location, Item, Stock, MedicalSupply,
    Pharmaceutical, Equipment, SterileSupply, StockTransaction
)
from .serializers import (
    SupplierSerializer, LocationSerializer, ItemListSerializer, ItemDetailSerializer,
    ItemCreateSerializer, StockListSerializer, StockDetailSerializer, StockCreateSerializer,
    MedicalSupplySerializer, MedicalSupplyCreateSerializer, PharmaceuticalSerializer,
    PharmaceuticalCreateSerializer, EquipmentSerializer, EquipmentCreateSerializer,
    SterileSupplySerializer, SterileSupplyCreateSerializer, StockTransactionSerializer,
    StockTransactionCreateSerializer, LowStockReportSerializer, ExpiringItemsReportSerializer,
    InventoryValueReportSerializer
)

class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        suppliers = Supplier.objects.all().order_by('name')
        serializer = SupplierSerializer(suppliers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SupplierSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SupplierDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        serializer = SupplierSerializer(supplier)
        return Response(serializer.data)
    
    def put(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        serializer = SupplierSerializer(supplier, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        if supplier.item_set.exists():
            return Response(
                {'error': 'Cannot delete supplier with associated items'},
                status=status.HTTP_400_BAD_REQUEST
            )
        supplier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LocationListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        locations = Location.objects.all().order_by('name')
        serializer = LocationSerializer(locations, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LocationDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        serializer = LocationSerializer(location)
        return Response(serializer.data)
    
    def put(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        serializer = LocationSerializer(location, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        location = get_object_or_404(Location, pk=pk)
        if location.stock_set.exists():
            return Response(
                {'error': 'Cannot delete location with stock records'},
                status=status.HTTP_400_BAD_REQUEST
            )
        location.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        items = Item.objects.select_related('supplier').prefetch_related('stock_records')
        
        category = request.query_params.get('category')
        status_filter = request.query_params.get('status', 'ACTIVE')
        search = request.query_params.get('search')
        low_stock = request.query_params.get('low_stock')
        
        if category:
            items = items.filter(category=category)
        if status_filter:
            items = items.filter(status=status_filter)
        if search:
            items = items.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )
        if low_stock:
            items = items.filter(
                stock_records__quantity__lt=F('reorder_level')
            ).distinct()
        
        serializer = ItemListSerializer(items, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = ItemCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ItemDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        item = get_object_or_404(Item.objects.select_related('supplier').prefetch_related('stock_records'), pk=pk)
        serializer = ItemDetailSerializer(item)
        return Response(serializer.data)
    
    def put(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        serializer = ItemCreateSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        if item.stock_records.exists():
            return Response(
                {'error': 'Cannot delete item with stock records'},
                status=status.HTTP_400_BAD_REQUEST
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class StockListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        stocks = Stock.objects.select_related('item', 'location').filter(quantity__gt=0)
        
        item_id = request.query_params.get('item')
        location_id = request.query_params.get('location')
        expired = request.query_params.get('expired')
        expiring_days = request.query_params.get('expiring_days')
        
        if item_id:
            stocks = stocks.filter(item_id=item_id)
        if location_id:
            stocks = stocks.filter(location_id=location_id)
        if expired == 'true':
            stocks = stocks.filter(expiry_date__lt=timezone.now().date())
        if expiring_days:
            try:
                days = int(expiring_days)
                cutoff_date = timezone.now().date() + timedelta(days=days)
                stocks = stocks.filter(
                    expiry_date__lte=cutoff_date,
                    expiry_date__gte=timezone.now().date()
                )
            except ValueError:
                pass
        
        serializer = StockListSerializer(stocks, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = StockCreateSerializer(data=request.data)
        if serializer.is_valid():
            stock = serializer.save()
            
            StockTransaction.objects.create(
                item=stock.item,
                location=stock.location,
                transaction_type='IN',
                quantity=stock.quantity,
                unit_cost=stock.item.unit_cost,
                reference_number=f"STOCK-IN-{stock.id}",
                notes="Initial stock entry",
                created_by=f"{request.user.first_name} {request.user.last_name}" if hasattr(request.user, 'first_name') else str(request.user)
            )
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        stock = get_object_or_404(Stock.objects.select_related('item', 'location'), pk=pk)
        serializer = StockDetailSerializer(stock)
        return Response(serializer.data)
    
    def put(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        old_quantity = stock.quantity
        
        serializer = StockCreateSerializer(stock, data=request.data)
        if serializer.is_valid():
            updated_stock = serializer.save()
            
            quantity_diff = updated_stock.quantity - old_quantity
            if quantity_diff != 0:
                StockTransaction.objects.create(
                    item=updated_stock.item,
                    location=updated_stock.location,
                    transaction_type='ADJUSTMENT',
                    quantity=quantity_diff,
                    reference_number=f"ADJ-{updated_stock.id}",
                    notes=f"Stock adjustment from {old_quantity} to {updated_stock.quantity}",
                    created_by=f"{request.user.first_name} {request.user.last_name}" if hasattr(request.user, 'first_name') else str(request.user)
                )
            
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        stock = get_object_or_404(Stock, pk=pk)
        
        if stock.quantity > 0:
            StockTransaction.objects.create(
                item=stock.item,
                location=stock.location,
                transaction_type='OUT',
                quantity=-stock.quantity,
                reference_number=f"STOCK-DEL-{stock.id}",
                notes="Stock record deleted",
                created_by=f"{request.user.first_name} {request.user.last_name}" if hasattr(request.user, 'first_name') else str(request.user)
            )
        
        stock.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MedicalSupplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        supplies = MedicalSupply.objects.select_related('supplier').prefetch_related('stock_records')
        serializer = MedicalSupplySerializer(supplies, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = MedicalSupplyCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PharmaceuticalListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        pharmaceuticals = Pharmaceutical.objects.select_related('supplier').prefetch_related('stock_records')
        controlled_only = request.query_params.get('controlled_only')
        
        if controlled_only == 'true':
            pharmaceuticals = pharmaceuticals.exclude(controlled_schedule='')
        
        serializer = PharmaceuticalSerializer(pharmaceuticals, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = PharmaceuticalCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EquipmentListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        equipment = Equipment.objects.select_related('supplier').prefetch_related('stock_records')
        needs_maintenance = request.query_params.get('needs_maintenance')
        
        if needs_maintenance == 'true':
            equipment = [e for e in equipment if e.needs_maintenance]
            serializer = EquipmentSerializer(equipment, many=True)
        else:
            serializer = EquipmentSerializer(equipment, many=True)
        
        return Response(serializer.data)
    
    def post(self, request):
        serializer = EquipmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SterileSupplyListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        supplies = SterileSupply.objects.select_related('supplier').prefetch_related('stock_records')
        non_sterile = request.query_params.get('non_sterile')
        
        if non_sterile == 'true':
            supplies = [s for s in supplies if not s.is_sterile]
            serializer = SterileSupplySerializer(supplies, many=True)
        else:
            serializer = SterileSupplySerializer(supplies, many=True)
        
        return Response(serializer.data)
    
    def post(self, request):
        serializer = SterileSupplyCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StockTransactionListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = StockTransaction.objects.select_related('item', 'location').order_by('-created_at')
        
        item_id = request.query_params.get('item')
        location_id = request.query_params.get('location')
        transaction_type = request.query_params.get('type')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if item_id:
            transactions = transactions.filter(item_id=item_id)
        if location_id:
            transactions = transactions.filter(location_id=location_id)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if date_from:
            transactions = transactions.filter(created_at__date__gte=date_from)
        if date_to:
            transactions = transactions.filter(created_at__date__lte=date_to)
        
        serializer = StockTransactionSerializer(transactions[:100], many=True)
        return Response(serializer.data)

class LowStockReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        low_stock_items = []
        
        items = Item.objects.select_related('supplier').prefetch_related('stock_records').filter(status='ACTIVE')
        
        for item in items:
            total_stock = item.stock_records.aggregate(total=Sum('quantity'))['total'] or 0
            
            if total_stock <= item.reorder_level:
                low_stock_items.append({
                    'item_id': item.id,
                    'item_name': item.name,
                    'sku': item.sku,
                    'current_stock': total_stock,
                    'reorder_level': item.reorder_level,
                    'reorder_quantity': item.reorder_quantity,
                    'supplier_name': item.supplier.name,
                    'category': item.get_category_display()
                })
        
        serializer = LowStockReportSerializer(low_stock_items, many=True)
        return Response(serializer.data)

class ExpiringItemsReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        cutoff_date = timezone.now().date() + timedelta(days=days)
        
        expiring_stocks = Stock.objects.select_related('item', 'location').filter(
            expiry_date__lte=cutoff_date,
            expiry_date__gte=timezone.now().date(),
            quantity__gt=0
        ).order_by('expiry_date')
        
        expiring_items = []
        for stock in expiring_stocks:
            expiring_items.append({
                'item_id': stock.item.id,
                'item_name': stock.item.name,
                'location_name': stock.location.name,
                'quantity': stock.quantity,
                'expiry_date': stock.expiry_date,
                'days_until_expiry': stock.days_until_expiry,
                'lot_number': stock.lot_number or ''
            })
        
        serializer = ExpiringItemsReportSerializer(expiring_items, many=True)
        return Response(serializer.data)

class InventoryValueReportView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        categories = Item.CATEGORY_CHOICES
        inventory_values = []
        
        for category_code, category_name in categories:
            items = Item.objects.filter(category=category_code, status='ACTIVE')
            total_items = items.count()
            
            total_quantity = 0
            total_value = 0
            
            for item in items:
                item_stock = item.stock_records.aggregate(total=Sum('quantity'))['total'] or 0
                total_quantity += item_stock
                total_value += item_stock * float(item.unit_cost)
            
            inventory_values.append({
                'category': category_name,
                'total_items': total_items,
                'total_quantity': total_quantity,
                'total_value': total_value
            })
        
        serializer = InventoryValueReportSerializer(inventory_values, many=True)
        return Response(serializer.data)
