from django.contrib import admin
from applications.models import Application, Enrollment, Payment, TutorWallet, Invoice
# Register your models here.

admin.site.register(Application)
admin.site.register(Enrollment)
admin.site.register(Payment)
admin.site.register(TutorWallet)
admin.site.register(Invoice)

