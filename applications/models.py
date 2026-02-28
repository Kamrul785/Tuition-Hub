from django.db import models
from django.db import models
from django.conf import settings
from tuition.models import Tuition
# Create your models here.

class Application(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    tuition = models.ForeignKey(
        Tuition, 
        on_delete=models.CASCADE, 
        related_name="applications"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="applications"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tuition", "applicant")  

    def __str__(self):
        return f"{self.applicant.email} : {self.tuition.title} ({self.status})"


class Enrollment(models.Model):
    
    tuition = models.ForeignKey(
        Tuition, 
        on_delete=models.CASCADE, 
        related_name="enrollments"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="enrollments"
    )
    payment_verified = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tuition", "student")
    
    def __str__(self):
        return f"{self.student.email} enrolled in {self.tuition.title}"


class Topic(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.CASCADE, 
        related_name="topics"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({'Completed' if self.completed else 'Pending'})"


class Assignment(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, 
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
    
    
class Review(models.Model):
    tuition = models.ForeignKey(
        Tuition,
        on_delete=models.CASCADE,
        related_name = 'reviews'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="reviews"
    )
    rating = models.IntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ("tuition", "student") 

    def __str__(self):
        return f"{self.student.email}: {self.tuition.title} ({self.rating};{self.comment})"


class Payment(models.Model):
    PAYMENT_STATUS_PENDING = "PENDING"
    PAYMENT_STATUS_COMPLETED = "COMPLETED"
    PAYMENT_STATUS_FAILED = "FAILED"
    PAYMENT_STATUS_REFUNDED = "REFUNDED"
    
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_STATUS_PENDING, "Pending"),
        (PAYMENT_STATUS_COMPLETED, "Completed"),
        (PAYMENT_STATUS_FAILED, "Failed"),
        (PAYMENT_STATUS_REFUNDED, "Refunded"),
    ]
    
    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="payment"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_payments"
    )
    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tutor_payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_STATUS_PENDING
    )
    transaction_id = models.CharField(max_length=255, unique=True)
    payment_gateway = models.CharField(max_length=50, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment: {self.student.email} -> {self.tutor.email} ({self.status})"


class TutorWallet(models.Model):
    tutor = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    available_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wallet: {self.tutor.email} - Available: {self.available_balance}"


class Invoice(models.Model):
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name="invoice"
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    pdf_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"Invoice: {self.invoice_number}"