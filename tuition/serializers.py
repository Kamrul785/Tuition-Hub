from rest_framework import serializers
from .models import Tuition

class TuitionSerializer(serializers.ModelSerializer):
    tutor_email = serializers.ReadOnlyField(source = "tutor.email")
    class Meta:
        model = Tuition
        fields = ['id','title', 'description','subject','class_level','availability','is_paid','price','tutor','tutor_email','created_at','updated_at']
        read_only_fields =['id','tutor','created_at', 'updated_at']
