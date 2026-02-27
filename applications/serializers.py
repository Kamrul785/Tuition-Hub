from rest_framework import serializers
from .models import Application, Enrollment, Topic, Assignment, Review, Payment, TutorWallet, Invoice

class ApplicationSerializer(serializers.ModelSerializer):
    applicant_email = serializers.ReadOnlyField(source="applicant.email")
    tuition_title = serializers.ReadOnlyField(source="tuition.title")

    class Meta:
        model = Application
        fields = ["id", "tuition", "tuition_title", "applicant_email", "status", "applied_at"]
        read_only_fields = ["id", "tuition_title", "applicant_email", "status", "applied_at"]


class EnrollmentSerializer(serializers.ModelSerializer):
    student_email = serializers.ReadOnlyField(source="student.email")
    tuition_title = serializers.ReadOnlyField(source="tuition.title")
    is_paid = serializers.ReadOnlyField(source="tuition.is_paid")
    price = serializers.ReadOnlyField(source="tuition.price")

    class Meta:
        model = Enrollment
        fields = ["id", "tuition", "tuition_title", "student_email", "payment_verified", "is_paid", "price", "enrolled_at"]
        read_only_fields = ["id", "tuition_title", "student_email", "is_paid", "price", "enrolled_at"]


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'enrollment', 'title', 'description', 'completed']
        read_only_fields = ['id', 'enrollment']


class AssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assignment
        fields = ['id', 'enrollment', 'title', 'description', 'due_date']
        read_only_fields = ['id', 'enrollment']
        

class ReviewSerializer(serializers.ModelSerializer):
    student_email = serializers.ReadOnlyField(source="student.email")
    tuition_title = serializers.ReadOnlyField(source="tuition.title")

    class Meta:
        model = Review
        fields = ["id", "tuition", "tuition_title", "student_email", "rating", "comment", "created_at"]
        read_only_fields = ["id", "student_email", "tuition_title", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    student_email = serializers.ReadOnlyField(source="student.email")
    tutor_email = serializers.ReadOnlyField(source="tutor.email")
    tuition_title = serializers.ReadOnlyField(source="enrollment.tuition.title")

    class Meta:
        model = Payment
        fields = ["id", "enrollment", "student", "student_email", "tutor", "tutor_email", "tuition_title", "amount", "status", "transaction_id", "payment_gateway", "payment_date", "created_at"]
        read_only_fields = ["id", "student_email", "tutor_email", "tuition_title", "payment_date", "created_at"]


class TutorWalletSerializer(serializers.ModelSerializer):
    tutor_email = serializers.ReadOnlyField(source="tutor.email")

    class Meta:
        model = TutorWallet
        fields = ["id", "tutor", "tutor_email", "total_earned", "available_balance", "pending_balance", "total_withdrawn", "created_at", "updated_at"]
        read_only_fields = ["id", "tutor_email", "total_earned", "available_balance", "pending_balance", "total_withdrawn", "created_at", "updated_at"]


class InvoiceSerializer(serializers.ModelSerializer):
    student_email = serializers.ReadOnlyField(source="payment.student.email")
    tutor_email = serializers.ReadOnlyField(source="payment.tutor.email")
    amount = serializers.ReadOnlyField(source="payment.amount")
    tuition_title = serializers.ReadOnlyField(source="payment.enrollment.tuition.title")

    class Meta:
        model = Invoice
        fields = ["id", "payment", "student_email", "tutor_email", "tuition_title", "amount", "invoice_number", "issued_date", "pdf_url"]
        read_only_fields = ["id", "student_email", "tutor_email", "tuition_title", "amount", "issued_date"]
