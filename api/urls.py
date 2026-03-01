from django.urls import path,include
from rest_framework_nested import routers
from tuition.views import TuitionViewSet, initiate_payment, payment_success, payment_fail, payment_cancel
from applications.views import ApplicationViewSet, EnrollmentViewSet, TopicViewSet, AssignmentViewSet, ReviewViewSet, PaymentViewSet, TutorWalletViewSet, InvoiceViewSet

router = routers.DefaultRouter()
router.register('tuitions',TuitionViewSet, basename='tuitions')
router.register("applications", ApplicationViewSet, basename="applications")
router.register("enrollments", EnrollmentViewSet, basename="enrollments")
router.register("payments", PaymentViewSet, basename="payments")
router.register("wallet", TutorWalletViewSet, basename="wallet")
router.register("invoices", InvoiceViewSet, basename="invoices")

enrollment_router = routers.NestedDefaultRouter(router, "enrollments", lookup="enrollment")
enrollment_router.register('topics', TopicViewSet, basename='enrollment-topics')
enrollment_router.register('assignments', AssignmentViewSet, basename='enrollment-assignments')

router.register('reviews',ReviewViewSet,basename='reviews')

urlpatterns = [
    path('',include(router.urls)),
    path('',include(enrollment_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('payment/initiate/', initiate_payment, name='initiate-payment'),
    path('payment/success/', payment_success, name='payment-success'),
    path('payment/fail/', payment_fail, name='payment-fail'),
    path('payment/cancel/', payment_cancel, name='payment-cancel'),
]
