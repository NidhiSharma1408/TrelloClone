import time, string,random
from django.http import Http404
from django.template import loader
from django.shortcuts import render
from django.core.mail import send_mail
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User,UserProfile,OtpModel
from .serializers import UserSerializer,MyTokenObtainPairSerializer, UserProfileSerializer
from .permissions import IsAdminUser,IsLoggedInUserOrAdmin
from rest_framework import filters


# To get custom tokens for a User; To be used in Password Reset

def get_tokens_for_user(user,request):
    refresh = RefreshToken.for_user(user)
    if user.profile.picture:
        picture = 'http://' + request.META['HTTP_HOST'] + user.profile.picture.url
    else:
        picture = None
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        "id" : user.profile.id,
        'email' : user.email,
        "name" : user.profile.name,
        "picture": picture
    }

#function for sending otp mail
def send_otp_email(email, body,subject):
    # print(password)
    OtpModel.objects.filter(otp_email__iexact = email).delete()
    # letters = string.ascii_lowercase+string.digits+string.ascii_uppercase
    # otp = ''.join(random.choice(letters) for i in range(6))
    otp = random.randint(100000,999999)
    time_of_creation = int(time.time())
    context = {
        'otp' : otp,
        'body': body,
    }
    html_content = loader.render_to_string('userauth/otp_mail.html', context)
    mail_body = f"{body} {otp}.\n This OTP will be valid for 5 minutes." 
    send_mail(subject, mail_body,'info.the.flow.app@gmail.com',[email,], html_message = html_content, fail_silently = False) 
    OtpModel.objects.create(otp=otp, otp_email = email, time_created = time_of_creation)
    return None


def otp_delete(request_email):
    try:
        otp = OtpModel.objects.get(otp_email=request_email)
    except:
        return 2 
    if int(time.time()) - otp.time_created < 60:
        return 0
    if int(time.time()) - otp.time_created > 300:
        otp.delete()
        return 1
    

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend,filters.SearchFilter]
    filterset_fields = ["email",'profile__name']
    search_fields = ["email",'profile__name']
    def create(self, request):
        data = request.data
        print(data)
        try:
            email = data["email"]
        except:
            return Response({"detail": "Please provide an email to create account."},status=status.HTTP_400_BAD_REQUEST) 
        try:
            User.objects.get(email__iexact=email)
        except:
            serializer = UserSerializer(data=data,context={"request":request})
            if serializer.is_valid():
                serializer.save()
                send_otp_email(email, 
                body = 
                    f"""Congratulations!!! You have successfully created your account on The Flow App.
                        Please verify your email to use your account.
                        Your OTP for registering your Account with The Flow App is""",
                subject= f"Email Verification OTP for The Flow App"
                )
                return Response({"detail" : "An OTP has been sent to your provided email."})
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail" : "User with this email already exists"},status = status.HTTP_226_IM_USED)
    def get_permissions(self):
        permission_classes = []
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action == 'retrieve' or self.action == 'update' or self.action == 'partial_update':
            permission_classes = [IsLoggedInUserOrAdmin]
        elif self.action == 'list' or self.action == 'destroy':
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]
    

class OTPVerificationView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        print(request.data)
        otp = request.data.get("otp","")
        email = request.data.get("email", "")
        current_time = int(time.time())
        try:
            query = OtpModel.objects.get(otp_email__iexact = email)
        except:
            raise Http404
        otpmodel_email      = query.otp_email 
        otpmodel_otp        = query.otp
        otp_creation_time   = query.time_created
        if (email == otpmodel_email and otp == otpmodel_otp and (current_time - otp_creation_time < 300)):
            user  =  User.objects.get(email__iexact = email)
            user.is_active = True
            user.save()
            OtpModel.objects.filter(otp_email__iexact = email).delete()
            mail_body = "Congratulations!!! You have successfully registered and verified your acoount on The Flow App."
            context = {'body':mail_body}
            html_content = loader.render_to_string('userauth/info_mail.html', context)
            send_mail("Account Verification Successful", mail_body,'info.the.flow.app@gmail.com',[email,], html_message = html_content, fail_silently = False) 
            return Response(get_tokens_for_user(user,request),status = status.HTTP_202_ACCEPTED)
        return Response(status = status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        request_email = request.data.get("email","")
        try:
            user = User.objects.get(email__iexact = request_email)
        except: 
            return Response({"detail" : "No such account exists"},status = status.HTTP_400_BAD_REQUEST)
        if otp_delete(request_email) == 0:
            return Response({"detail":"OTP was sent less than a minute ago."},status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            send_otp_email(request_email, body = f"You have not verified your email {request_email} yet. This email will let you change your password and Verify your email in a single step. Your OTP for the same is",
            subject= "Verify email and change password OTP for The Flow App")
            return Response({"detail" : "User is registered but not verified. An OTP for verification has been sent to email."}, status = status.HTTP_308_PERMANENT_REDIRECT)
        send_otp_email(request_email, body = "OTP for resetting your password of your The Flow App account is",subject="Password Change OTP for The Flow App") 
        return Response({"detail" : "OTP has been sent to your provided email."}, status = status.HTTP_200_OK)


class PasswordResetOTPConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self,request):
        coming_data = request.data
        request_otp   = coming_data.get("otp",None)
        request_email = coming_data.get("email",None)
        current_time = int(time.time())
        if request_email is not None:
            try:
                otpmodel = OtpModel.objects.get(otp_email__iexact = request_email)
                user = User.objects.get(email__iexact = request_email)
            except:
                raise Http404
            if otpmodel.otp_email == request_email and otpmodel.otp == request_otp and (current_time - otpmodel.time_created <300):
                OtpModel.objects.filter(otp_email__iexact = request_email).delete()
                return Response(get_tokens_for_user(user,request))
            return Response(status = status.HTTP_400_BAD_REQUEST)
        return Response(status = status.HTTP_400_BAD_REQUEST)


class OTPResend(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email",None)
        try:
            User.objects.get(email__iexact = email)
        except:
            return Response({"detail" : "No account with this email found"},status = status.HTTP_400_BAD_REQUEST)
        if otp_delete(email) == 0:
            return Response({"detail":"OTP was sent less than a minute ago."},status=status.HTTP_403_FORBIDDEN)
        send_otp_email(email, body = "Your New OTP is ",subject="New OTP for The Flow App")
        return Response({"detail" : "An OTP has been sent to provided Email"}, status = status.HTTP_202_ACCEPTED)
