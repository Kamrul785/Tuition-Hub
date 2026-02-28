from django.shortcuts import render
from tuition.serializers import TuitionSerializer
from tuition.models import Tuition
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from tuition.filters import TuitionFilter
from tuition.paginations import DefaultPagination
from rest_framework.decorators import api_view
from sslcommerz_lib import SSLCOMMERZ
from rest_framework.response import Response
# Create your views here.

class IsTutor(permissions.BasePermission):
    """Only tutors can create/update/delete tuition posts"""
    def has_permission(self, request, view):
        if view.action in ['list', 'retrieve']:
            return True
        return request.user.is_authenticated and request.user.role == 'Tutor' or request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        if view.action in ["put", "patch", "destroy"]:
            return obj.tutor == request.user
        return True

class TuitionViewSet(ModelViewSet):
    serializer_class = TuitionSerializer
    queryset = Tuition.objects.all()
    permission_classes = [IsTutor]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TuitionFilter
    pagination_class = DefaultPagination
    search_fields = ['title', 'description', 'subject', 'class_level']
    ordering_fields = ['created_at', 'class_level']
    
    def perform_create(self, serializer):
        serializer.save(tutor=self.request.user)
        
        
        
@api_view(['POST'])
def initiate_payment(request):
    user = request.user
    amount = request.data.get("amount")
    enrollment_id = request.data.get("enrollment_id")
    settings = { 'store_id': 'tuiti699b02e4e33f5', 'store_pass': 'tuiti699b02e4e33f5@ssl', 'issandbox': True }
    sslcz = SSLCOMMERZ(settings)
    post_body = {}
    post_body['total_amount'] = amount      
    post_body['currency'] = "BDT"
    post_body['tran_id'] = f"txn_{enrollment_id}"
    post_body['success_url'] = "http://localhost:5173/payment/success/"
    post_body['fail_url'] = "http://localhost:5173/payment/fail/"
    post_body['cancel_url'] = "http://localhost:5173/dashboard/my-enrollments"
    post_body['emi_option'] = 0
    post_body['cus_name'] = f"{user.first_name} {user.last_name}"
    post_body['cus_email'] = user.email
    post_body['cus_phone'] = user.phone_number
    post_body['cus_add1'] = user.address
    post_body['cus_city'] = "Dhaka"
    post_body['cus_country'] = "Bangladesh"
    post_body['shipping_method'] = "NO"
    post_body['multi_card_name'] = ""
    post_body['num_of_item'] = 1
    post_body['product_name'] = "Educational Services"
    post_body['product_category'] = "Education"
    post_body['product_profile'] = "general"

    response = sslcz.createSession(post_body) # API response
    if response.get("status") == "SUCCESS":
        return Response({"payment_url": response.get("GatewayPageURL")})
    else:
        return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)
    