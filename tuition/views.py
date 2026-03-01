from django.shortcuts import render
from tuition.serializers import TuitionSerializer
from tuition.models import Tuition
from applications.models import Enrollment
from applications.models import Payment
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from tuition.filters import TuitionFilter
from tuition.paginations import DefaultPagination
from sslcommerz_lib import SSLCOMMERZ
from rest_framework.response import Response
from django.conf import settings as django_settings
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
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
    
    # Get enrollment
    try:
        enrollment = Enrollment.objects.get(id=enrollment_id, student=user)
    except Enrollment.DoesNotExist:
        return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)
    
    tran_id = f"txn_{enrollment_id}"
    
    # Create Payment record 
    payment, created = Payment.objects.get_or_create(
        enrollment=enrollment,
        defaults={
            'student': user,
            'tutor': enrollment.tuition.tutor,
            'amount': amount,
            'status': Payment.PAYMENT_STATUS_PENDING,
            'transaction_id': tran_id,
            'payment_gateway': 'sslcommerz',
        }
    )
    
    settings = { 'store_id': 'tuiti699b02e4e33f5', 'store_pass': 'tuiti699b02e4e33f5@ssl', 'issandbox': True }
    sslcz = SSLCOMMERZ(settings)
    post_body = {}
    post_body['total_amount'] = amount      
    post_body['currency'] = "BDT"
    post_body['tran_id'] = tran_id
    post_body['success_url'] = f"{django_settings.BACKEND_URL}/api/v1/payment/success/"
    post_body['fail_url'] = f"{django_settings.BACKEND_URL}/api/v1/payment/fail/"
    post_body['cancel_url'] = f"{django_settings.BACKEND_URL}/api/v1/payment/cancel/"
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
        logger.info(f"Payment initiated: {tran_id}")
        return Response({
            "payment_url": response.get("GatewayPageURL"),
            "transaction_id": tran_id
        })
    else:
        logger.error(f"Payment initiation failed: {tran_id}")
        return Response({"error": "Payment initiation failed"}, status=status.HTTP_400_BAD_REQUEST)
    

@api_view(['POST', 'GET'])
@permission_classes([permissions.AllowAny])  # Allow unauthenticated access (SSLCommerz redirects here)
def payment_success(request):
    """
    SSLCommerz redirects here after successful payment.
    This endpoint is called by SSLCommerz (server-to-server), not by frontend.
    """
    from applications.models import TutorWallet
    
    try:
        tran_id = request.POST.get("tran_id")
        
        if not tran_id:
            return Response(
                {"error": "Transaction ID missing"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            enrollment_id = tran_id.split("_")[1]
        except IndexError:
            return Response(
                {"error": "Invalid transaction ID format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get enrollment
        try:
            enrollment = Enrollment.objects.get(id=enrollment_id)
        except Enrollment.DoesNotExist:
            logger.error(f"Enrollment {enrollment_id} not found")
            return Response(
                {"error": "Enrollment not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            payment = Payment.objects.get(transaction_id=tran_id)
            payment.status = Payment.PAYMENT_STATUS_COMPLETED
            payment.payment_date = timezone.now()
            payment.save()
            
            # Credit tutor wallet
            # wallet, _ = TutorWallet.objects.get_or_create(tutor=enrollment.tuition.tutor)
            # wallet.total_earned += payment.amount
            # wallet.available_balance += payment.amount
            # wallet.save()
            # logger.info(f"Wallet credited: {payment.amount} for tutor {enrollment.tuition.tutor.email}")
            
        except Payment.DoesNotExist:
            logger.warning(f"Payment record not found for {tran_id}")
        
       
        enrollment.payment_verified = True
        enrollment.save()
        
        logger.info(f"Payment successful for enrollment {enrollment_id}")
        
   
        success_url = f"{django_settings.FRONTEND_URL}/dashboard/my-enrollments/{enrollment_id}"
        return redirect(success_url)
        
    except Exception as e:
        logger.error(f"Payment success error: {str(e)}")
        return Response(
            {"error": "Failed to process payment"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST', 'GET'])
@permission_classes([permissions.AllowAny])
def payment_fail(request):
    """
    SSLCommerz redirects here if payment fails.
    """
    try:
        tran_id = request.POST.get("tran_id")
        
        if tran_id:
            Payment.objects.filter(transaction_id=tran_id).update(
                status=Payment.PAYMENT_STATUS_FAILED
            )
            logger.warning(f"Payment failed: {tran_id}")
        
        return redirect(f"{django_settings.FRONTEND_URL}/dashboard/payment/fail/")
        
    except Exception as e:
        logger.error(f"Payment fail error: {str(e)}")
        return HttpResponseRedirect(f"{django_settings.FRONTEND_URL}/dashboard/payment/fail/")
    

@api_view(['POST', 'GET'])
@permission_classes([permissions.AllowAny])
def payment_cancel(request):
    """
    SSLCommerz redirects here if payment is cancelled by user.
    """
    try:
        tran_id = request.POST.get("tran_id")
        
        if tran_id:
            Payment.objects.filter(transaction_id=tran_id).update(
                status=Payment.PAYMENT_STATUS_FAILED
            )
            logger.warning(f"Payment cancelled: {tran_id}")
        
        return redirect(f"{django_settings.FRONTEND_URL}/dashboard/my-enrollments/")
        
    except Exception as e:
        logger.error(f"Payment cancel error: {str(e)}")
        return HttpResponseRedirect(f"{django_settings.FRONTEND_URL}/dashboard/my-enrollments/")