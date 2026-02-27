from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Application, Enrollment, Topic, Assignment, Review, Payment, TutorWallet, Invoice
from .serializers import ApplicationSerializer, EnrollmentSerializer, TopicSerializer, AssignmentSerializer, ReviewSerializer, PaymentSerializer, TutorWalletSerializer, InvoiceSerializer
from tuition.models import Tuition
from tuition.views import IsTutor
from tuition.paginations import DefaultPagination
from applications.permissions import IsTutorOrReadOnly
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
# Create your views here.

class IsUser(permissions.BasePermission):
    """Only users (students) can apply"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "User"

class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    queryset = Application.objects.all() 
    pagination_class = DefaultPagination    
    def get_permissions(self):
        if self.action == "create":
            return [IsUser()]
        return [permissions.IsAuthenticated()]
    

    def perform_create(self, serializer):
        tuition_id = self.request.data.get("tuition")
        tuition = Tuition.objects.get(id=tuition_id)
        serializer.save(applicant=self.request.user, tuition=tuition)

    def get_queryset(self):
        user = self.request.user
        if user.role == "Tutor":
            return Application.objects.filter(tuition__tutor=user)
        elif user.role == "User":
            return Application.objects.filter(applicant=user)
        return Application.objects.none()
    
    @action(detail=True, methods=["post"], permission_classes=[IsTutor])
    
    def select(self, request, pk=None):
        """
        Tutor accepts an applicant. 
        """
        application = self.get_object()
        tuition = application.tuition

        if tuition.tutor != request.user:
            return Response({"detail": "You do not own this tuition."}, status=status.HTTP_403_FORBIDDEN)

        if application.status != Application.STATUS_PENDING:
            return Response({"detail": "Application already processed."}, status=status.HTTP_400_BAD_REQUEST)

        if Enrollment.objects.filter(tuition=tuition, student=application.applicant).exists():
            return Response(
                {"detail": "Applicant already enrolled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        application.status = Application.STATUS_ACCEPTED
        application.save()
        
        enrollment = Enrollment(tuition=tuition, student=application.applicant)
        enrollment.save()
        
        serializer = EnrollmentSerializer(enrollment, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    queryset = Enrollment.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.role == "User":
            return Enrollment.objects.filter(student=user)
        elif user.role == "Tutor":
            return Enrollment.objects.filter(tuition__tutor=user)
        return Enrollment.objects.none()
    
    @action(detail=True, methods=["get"])
    def progress(self, request, pk=None):
        enrollment = self.get_object()
        topics = Topic.objects.filter(enrollment=enrollment)
        assignments = Assignment.objects.filter(enrollment=enrollment)

        return Response({
            "enrollment_id": enrollment.id,
            "tuition_title": enrollment.tuition.title,
            "student_email": enrollment.student.email,
            "topics": TopicSerializer(topics, many=True).data,
            "assignments": AssignmentSerializer(assignments, many=True).data,
        })
        
class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsTutorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role == "Tutor":
            return Topic.objects.filter(enrollment__tuition__tutor=user)
        elif user.role == "User":
            return Topic.objects.filter(enrollment__student=user)
        return Topic.objects.none()

    def perform_create(self, serializer):
        enrollment_id = self.kwargs["enrollment_pk"]
        enrollment = Enrollment.objects.get(id=enrollment_id)
        if self.request.user == enrollment.tuition.tutor:
            serializer.save(enrollment=enrollment)
        else:
            raise PermissionDenied("Only tutor can add topics.")

class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = [IsTutorOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        if user.role == "Tutor":
            return Assignment.objects.filter(enrollment__tuition__tutor=user)
        elif user.role == "User":
            return Assignment.objects.filter(enrollment__student=user)
        return Assignment.objects.none()

    def perform_create(self, serializer):
        enrollment_id = self.kwargs["enrollment_pk"]
        enrollment = Enrollment.objects.get(id=enrollment_id)
        if self.request.user == enrollment.tuition.tutor:
            serializer.save(enrollment=enrollment)
        else:
            raise PermissionDenied("Only tutor can add assignments.")
        

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Review.objects.all()
    
    def get_queryset(self):
        return Review.objects.all()

    def perform_create(self, serializer):
        tuition = serializer.validated_data.get("tuition")
        if tuition is None:
            raise ValidationError({"tuition": "This field is required."})

        enrolled = Enrollment.objects.filter(tuition=tuition, student=self.request.user).exists()
        if not enrolled:
            raise PermissionDenied("You can only review a tuition you are enrolled in.")

        if Review.objects.filter(tuition=tuition, student=self.request.user).exists():
            raise ValidationError("You have already reviewed this tuition.")

        serializer.save(student=self.request.user, tuition=tuition)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == "User":
            return Payment.objects.filter(student=user)
        elif user.role == "Tutor":
            return Payment.objects.filter(tutor=user)
        return Payment.objects.none()

    @action(detail=False, methods=["get"])
    def my_payments(self, request):
        """Get current user's payment history"""
        payments = self.get_queryset()
        page = self.paginate_queryset(payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)


class TutorWalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TutorWalletSerializer
    queryset = TutorWallet.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "Tutor":
            return TutorWallet.objects.filter(tutor=user)
        return TutorWallet.objects.none()

    @action(detail=False, methods=["get"])
    def my_wallet(self, request):
        """Get current tutor's wallet balance"""
        try:
            wallet = TutorWallet.objects.get(tutor=request.user)
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        except TutorWallet.DoesNotExist:
            return Response(
                {"detail": "Wallet not found. Only tutors have wallets."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"])
    def earnings(self, request):
        """Get tutor's earnings from completed payments"""
        try:
            wallet = TutorWallet.objects.get(tutor=request.user)
            payments = Payment.objects.filter(tutor=request.user, status=Payment.PAYMENT_STATUS_COMPLETED)
            return Response({
                "total_earned": wallet.total_earned,
                "available_balance": wallet.available_balance,
                "pending_balance": wallet.pending_balance,
                "payments_count": payments.count(),
                "recent_payments": PaymentSerializer(payments[:10], many=True).data
            })
        except TutorWallet.DoesNotExist:
            return Response(
                {"detail": "Wallet not found."},
                status=status.HTTP_404_NOT_FOUND
            )


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == "User":
            return Invoice.objects.filter(payment__student=user)
        elif user.role == "Tutor":
            return Invoice.objects.filter(payment__tutor=user)
        return Invoice.objects.none()

    @action(detail=False, methods=["get"])
    def my_invoices(self, request):
        """Get current user's invoices"""
        invoices = self.get_queryset()
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)