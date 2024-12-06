from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from authentication.models import CustomUser, OTP
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import random
import requests

class LoginSerializer(serializers.Serializer):
    permission_classes = []
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)
        if email is None:
            raise serializers.ValidationError('An email address is required to log in.')
        if password is None:
            raise serializers.ValidationError('A password is required to log in.')
        user = authenticate(username=email, password=password)
        if user is None:
            raise AuthenticationFailed('No user found with this email and password.')
        if not user.is_active:
            raise AuthenticationFailed('This user has been deactivated.')
        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return {
            'email': user.email,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }


class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        if len(value) != 13:
            raise serializers.ValidationError(_('Invalid phone number.'))
        try:
            if not CustomUser.objects.filter(phone_number=value, role='customer').exists():
                # If the phone number is not associated with any customer account create a new account
                CustomUser.objects.create(phone_number=value, role='customer')
        except:
            raise serializers.ValidationError(_('Phone number already exists.'))
        return value
        
    def send_otp(self):
        phone_number = self.validated_data['phone_number']
        # Generate a 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        # Save the OTP in the database
        OTP.objects.create(phone_number=phone_number, otp=otp_code)

        if not settings.DEBUG:
            # Send OTP using the Fast2SMS API
            response = requests.get(
                'https://www.fast2sms.com/dev/bulkV2',
                params={
                    'authorization': settings.FAST2SMS_API_KEY,  # Replace with your actual API key from settings
                    'variables_values': otp_code,
                    'route': 'otp',
                    'numbers': phone_number[3:]
                }, headers={
                    'Cache-Control': 'no-cache'
                }
            )
            # print(response.json())
            if response.status_code != 200:
                raise serializers.ValidationError("Failed to send OTP. Please try again later.")
        return otp_code


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        phone_number = data.get('phone_number')
        otp = data.get('otp')

        try:
            otp_record = OTP.objects.get(phone_number=phone_number, otp=otp, is_verified=False)
        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP or phone number.")

        if otp_record.is_expired():
            raise serializers.ValidationError("OTP has expired.")

        # Mark the OTP as verified
        otp_record.is_verified = True
        otp_record.save()

        return data

    def create_tokens(self):
        phone_number = self.validated_data['phone_number']
        user = CustomUser.objects.get(phone_number=phone_number, role='customer')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'phone_number', 'role']
    
    def get_name(self, obj):
        "Return the name of the user"
        return obj.get_full_name()
