from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework import status
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema
from . import serializers, models
from datetime import datetime, timezone, timedelta, time
from content import models as content_models
from datetime import datetime, timezone, timedelta
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SignupUser(APIView):
    @extend_schema(responses=serializers.BitCampUserSerializer)
    def post(self, request, **kwargs):
        serializer = serializers.BitCampUserSerializer(
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            user = serializer.instance
            user.set_password(request.data["password"])
            user.save()
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                "token": token.key
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginUser(APIView):
    @extend_schema(responses=serializers.BitCampUserSerializer)
    def post(self, request, **kwargs):
        user = get_object_or_404(
            models.BitCampUser,
            username=request.data["username"]
        )
        
        if not user.check_password(request.data["password"]):
            return Response(
                {"detail": "Not found."}, 
                status = status.HTTP_401_UNAUTHORIZED
            )
        
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "token" : token.key
        })
        
class CurrentUser(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.BitCampUserSerializer)
    def get(self, request, **kwargs):
        user_data = dict(
            serializers.BitCampUserSerializer(
                instance=request.user
            ).data
        )
        
        user_data.pop("password")
        
        return Response(user_data)

class UpdateUser(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.BitCampUserSerializer)
    def put(self, request, **kwargs):        
        serializer = serializers.BitCampUserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class Discord(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.BitCampUserSerializer)
    def post(self, request, **kwargs):
        if request.data["code"]:
            code = request.data["code"]
        
        # Super robust Discord connection view
        # Todo
        
        return Response(status=status.HTTP_418_IM_A_TEAPOT)

class NewEnroll(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.EnrollmentSerializer)
    def post(self, request, **kwargs):
        logger.info("NewEnroll view called")
        serializer = serializers.EnrollmentSerializer(
            data=request.data,
            context={"user": request.user},
            partial=True
        )
        serializer.user = request.user.id
        
        logger.info("SERIALIZER CREATED")
        

        if serializer.is_valid():
            logger.info("SERIALIZER IS VALID")
            
            try:
                # Load Enrollments related to the user that has status Pending and change their status to Cancelled - this will prevent failed payment page from showing up when user tries to enroll in a new service on Payze.io.
                logger.info("Loading user's pending enrollments")
                pending_enrollments = models.Enrollment.objects.filter(
                    user_id=request.user.id,
                    status='Pending'
                )
                logger.info(f"Found {len(pending_enrollments)} pending enrollments")
                for enrollment in pending_enrollments:
                    logger.info(f"Enrollment {enrollment.id} status changed to Cancelled")
                    enrollment.status = 'Cancelled'
                    enrollment.save()
                logger.info("User's pending enrollments status changed to Cancelled")
                
                newEnrollment = serializer.save()
                logger.info("Saving enrollment successful")
                
            except Exception as e:
                logger.error("Error saving enrollment")
                logger.error(e)
                return Response({"error": "Error saving enrollment"}, status=status.HTTP_400_BAD_REQUEST)
            
            service = newEnrollment.service_id

            # Ensure service is not None
            if service is not None:
                # Instead of using create_payze_subscription, I need to implement new logic to create a Payment on payze.io API. To do this I need to send a POST request to https://payze.io/v2/api/payment with the following payload blueprint:
                # {
                #     "source": "Card",
                #     "amount": "1",
                #     "currency": "GEL",
                #     "language": "KA",
                #     "token": "8191CBB4E5E34E7F8FBEC1F0C",
                #     "cardPayment": {
                #         "tokenizeCard": true
                #     },
                #     "hooks": {
                #         "webhookGateway": "https://platform.bitcamp.ge",
                #         "successRedirectGateway": "https://platform.bitcamp.ge/success",
                #         "errorRedirectGateway": "https://platform.bitcamp.ge/error"
                #     },
                #     "metadata": {
                #         "extraAttributes": [
                #             { "key": "kids", "value": "kids 50" },
                #             { "key": "email", "value": "oto@bitcamp.ge" }
                #         ]
                #     }
                # } 
                # The response will be a JSON object with the following blueprint:
                # {
                #   "data": {
                #     "payment": {
                #       "id": 530285,
                #       "requesterId": 544545,
                #       "transactionId": "AEA6A00C7F2D4FB6A655478C4",
                #       "type": "AddCard",
                #       "source": "Card",
                #       "amount": 1,
                #       "currency": "GEL",
                #       "status": "Draft",
                #       "cardPayment": {
                #         "preauthorize": false,
                #         "googlePay": false,
                #         "applePay": false,
                #         "cardMask": null,
                #         "cardExpiration": null,
                #         "merchantId": null,
                #         "terminalId": null,
                #         "token": "AEA6A00C7F2D4FB6A655478C4",
                #         "rrn": null,
                #         "processingVendorId": null,
                #         "processingVendor": null,
                #         "cardOwnerEntityType": null
                #       },
                #       "walletPayment": null,
                #       "hooks": {
                #         "webhookGateway": "https://platform.bitcamp.ge",
                #         "successRedirectGateway": "https://platform.bitcamp.ge/success",
                #         "errorRedirectGateway": "https://platform.bitcamp.ge/error"
                #       },
                #       "language": "KA",
                #       "idempotencyKey": null,
                #       "metadata": {
                #         "channel": null,
                #         "order": null,
                #         "extraAttributes": [
                #           {
                #             "key": "kids",
                #             "value": "kids 50",
                #             "description": null
                #           },
                #           {
                #             "key": "email",
                #             "value": "oto@bitcamp.ge",
                #             "description": null
                #           }
                #         ]
                #       },
                #       "shareLink": null,
                #       "network": null,
                #       "blockedAmount": null,
                #       "capturedAmount": null,
                #       "refundedAmount": null,
                #       "reversedAmount": null,
                #       "settledBalanceAmount": null,
                #       "crossCurrencySettlement": null,
                #       "settled": null,
                #       "rejectReason": null,
                #       "fee": null,
                #       "channel": null,
                #       "payer": null,
                #       "receipt": null,
                #       "sandBox": false,
                #       "capturedDate": null,
                #       "blockedDate": null,
                #       "settledDate": null,
                #       "refundedDate": null,
                #       "reverseDate": null,
                #       "rejectedDate": null,
                #       "createdDate": "2024-01-13T00:39:06.2258218Z",
                #       "paymentUrl": "https://paygate.payze.io/pay/AEA6A00C7F2D4FB6A655478C4",
                #       "version": 1,
                #       "lastModifiedDate": "2024-01-13T00:39:06.225822Z"
                #     }
                #   },
                #   "status": {
                #     "message": null,
                #     "errors": null,
                #     "type": null
                #   }
                # }  
                # After receiving the response, I need to save new Payment using models.Payment model. The Payment model has the following fields:  
                #    enrollment which is a ForeignKey to Enrollment model
                # amount should be the same as the amount in the request payload
                # status should be the same as the status in the response
                # payze_transactionId should be the same as the transactionId in the response
                # cardMask should be the same as the cardMask in the response
                # token should be the same as the token in the response
                # paymentUrl should be the same as the paymentUrl in the response
                # Let's start implementing the Payment creation request to payze.io API:
                
                logger.info(f"Creating Payze payment - Enrollment: {newEnrollment.id}")
                
                payload = {
                    "source": "Card",
                    # Object of type Decimal is not JSON serializable
                    "amount": service.price.__str__(),
                    "currency": "GEL",
                    "language": "KA",
                    "cardPayment": {
                        "tokenizeCard": True
                    },
                    "hooks": {
                        "webhookGateway": "https://platform.bitcamp.ge/payments/payze_hook",
                        "successRedirectGateway": f"https://platform.bitcamp.ge/enrollments/{newEnrollment.id}/check-payze-subscription-status",
                        "errorRedirectGateway": f"https://platform.bitcamp.ge/enrollments/{newEnrollment.id}/check-payze-subscription-status"
                    },
                    "metadata": {
                        "extraAttributes": [
                            { "key": "service", "value": service.title },
                            { "key": "email", "value": newEnrollment.user.email }
                        ]
                    }
                }
                headers = {
                    "Accept": "application/*+json",
                    "Content-Type": "application/json",
                    "Authorization": settings.PAYZE_API_KEY
                }
                
                logger.info("Sending Payze payment request")
                try:
                    logger.info("Service price:")
                    logger.info(service.price.__str__())
                    payze_response = requests.put(
                        'https://payze.io/v2/api/payment',
                        json=payload,
                        headers=headers
                    )
                    logger.info("Payze payment request sent successfully")
                except Exception as e:
                    logger.error("Error sending Payze payment request")
                    logger.error(e)
                    return Response({"error": "Error sending Payze payment request"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Implement error handling for the request:
                if payze_response.status_code == 200:
                    logger.info("Payze payment response received successfully")
                    
                    # Process successful response by creating a Payment object
                    payze_data = payze_response.json()
                    try:
                        payment = models.Payment.objects.create(
                            enrollment=newEnrollment,
                            amount=payze_data['data']['payment']['amount'],
                            status=payze_data['data']['payment']['status'],
                            payze_transactionId=payze_data['data']['payment']['transactionId'],
                            payze_paymentId=payze_data['data']['payment']['id'],
                            # ERROR:  null value in column "cardMask" violates not-null constraint. Let's check the response and see if cardMask is null and if so, let's set it to empty string
                            cardMask=payze_data['data']['payment']['cardPayment']['cardMask'] if payze_data['data']['payment']['cardPayment']['cardMask'] is not None else "",
                            token=payze_data['data']['payment']['cardPayment']['token'],
                            paymentUrl=payze_data['data']['payment']['paymentUrl']
                        )
                        # Save the Payment object
                        logger.info("Saving Payze payment")
                        payment.save()
                        logger.info("Saving Payze payment successful")
                        
                        # Return the Payment object
                        # TypeError(Object of type Payment is not JSON serializable)
                        
                        return Response(payze_data, status=status.HTTP_201_CREATED)
                    except Exception as e:
                        logger.error("Error saving Payze payment response")
                        logger.error(e)
                        return Response({"error": "Error saving Payze payment response"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Handle errors from Payze
                    logger.error("Error receiving Payze payment response")  
                    logger.error(payze_response.status_code)
                    logger.error(payze_response.json())
                    return Response(payze_response.json(), status=payze_response.status_code)

            # Handle the case where service or payze_product_id is not available
            return Response({"error": "Service or Payze product ID not available"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def create_payze_subscription(self, user, payze_product_id):
        payload = {
            "productId": payze_product_id,
            "hookUrl": "http://localhost:3000/dashboard",  # Your server for webhooks
            "email": user.email,  # User's email
            "phone": user.phone_number,  # User's phone number
            "callback": "http://localhost:3000/dashboard",  # Callback URL after successful payment
            "callbackError": "http://localhost:3000/dashboard/error",  # Callback URL after failed payment
            "sendEmails": False  # Set based on your preference
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": settings.PAYZE_API_KEY  # Your Payze API Key
        }
        response = requests.post(
            'https://payze.io/v2/api/subscription',
            json=payload,
            headers=headers
        )
        return response

    
class MyEnrolls(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.EnrollmentSerializer)
    def get(self, request, **kwargs):
        enrollments = models.Enrollment.objects.filter(
            user_id=request.user.id
        ).prefetch_related('payments')  # Use prefetch_related for better performance
        serializer = serializers.EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateEnroll(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.EnrollmentSerializer)
    def put(self, request, id, **kwargs):
        enrollment = get_object_or_404(
            models.Enrollment,
            id=id
        )
        
        serializer = serializers.EnrollmentSerializer(
            enrollment,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckPayzeSubscriptionStatusView(APIView):

    def get(self, request, id, **kwargs):
        logger.info(f"CheckPayzeSubscriptionStatusView called with id {id}")
        try:
            enrollment = models.Enrollment.objects.get(id=id)
            updated_payments = self.check_payments_statuses_by_enrollment(enrollment.id)
            # Here I need to check the status of the payments related to the enrollment. Status check should be performed by looping through related payments and checking the status of each payment. If at least one payment is Captured within the last 30 days, then the enrollment status should be set to Active.
            for payment in updated_payments:
                if payment.status == 'Captured':
                    # Payment model has a field called created_at which is a DateTimeField. I need to check if the payment was created within the last 30 days. If so, then I need to set the enrollment status to Active.
                    # TypeError: can't compare offset-naive and offset-aware datetimes - I need to make the datetime object aware of the timezone
                    # How do I make a datetime object timezone aware?
                    
                    
                    if payment.created_at > datetime.now(timezone.utc) - timedelta(days=30): 
                        enrollment.status = 'Active'
                        enrollment.save()
                        logger.info(f"Enrollment {enrollment.id} status set to Active")
                        break
            
            serializer = serializers.PaymentSerializer(updated_payments, many=True)
            
            # Here I need to redirect user to a frontend URL with a different domain.
            return HttpResponseRedirect('https://www.bitcamp.ge/dashboard?payment=success')
        except models.Enrollment.DoesNotExist:
            return Response({"error": "Enrollment not found"}, status=status.HTTP_404_NOT_FOUND)

        

    def check_payments_statuses_by_enrollment(self, enrollment_id):
        logger.info(f"check_payments_statuses_by_enrollment called with enrollment_id {enrollment_id}")
        # In this function I would like to check the status of the payments related to the enrollment. Status check should be performed by looping through related payments and checking the status of each payment. If all payments are Captured, then the enrollment status should be set to Active. 
        # 
        # If any of the payments is not Captured, then the enrollment status should be checked on payze.io by transactionId and updated accordingly.
        
        # Here we should load all payments related to the enrollment
        payments = models.Payment.objects.filter(enrollment_id=enrollment_id)
        logger.info(f"Found {len(payments)} payments related to enrollment {enrollment_id}")
        
        # Updared payments
        updated_payments = []
        
        # Loop through payments and check the status of each payment
        for payment in payments:
            logger.info(f"Payment {payment.title} - Checking payment status here: {payment.status}")
            logger.info(f"Payment Payze transaction ID: {payment.payze_transactionId}")
            if True:
                url = f"https://payze.io/v2/api/payment/query/token-based?$filter=id eq {payment.payze_paymentId}"
                logger.info(f"Payze API URL with transaction filter: {url}")
                headers = {
                    "accept": "application/json",
                    "Authorization": settings.PAYZE_API_KEY
                }
                logger.info(f"Payment {payment.title} - Checking payment status via Payze API")
                response = requests.get(url, headers=headers)
                logger.info(f"Checking payment status via Payze API - {response.status_code}")
                if response.status_code == 200:
                    logger.info(f"Payment {payment.title} - Payment status check successful - {response.status_code}")
                    returned_payments = response.json()
                    
                    logger.info(len(returned_payments['data']['value']))
                    
                    logger.info(returned_payments['data']['value'][0]['id'])
                    
                    if len(returned_payments['data']['value']) > 0 and returned_payments['data']['value'][0]['status'] == 'Captured':
                        logger.info(f"Payment {payment.title} - Updating payment status to Captured")
                        payment.status = returned_payments['data']['value'][0]['status']
                        payment.cardMask = returned_payments['data']['value'][0]['cardPayment']['cardMask']
                        payment.save()
                        updated_payments.append(payment)
                        logger.info(f"Payment {payment.title} - Updated successfully")
                        
        logger.info(f"Number of payments updated successfully {len(updated_payments)} ")
        return updated_payments
        
class NewKidsProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.KidsProfileSerializer)
    def post(self, request, **kwargs):
        serializer = serializers.KidsProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class GetKidsProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.KidsProfileSerializer)
    def get(self, request, **kwargs):
        profiles = models.KidsProfile.objects.filter(user=request.user)
        serializer = serializers.KidsProfileSerializer(profiles, many=True)
        return Response(serializer.data)

class DeleteKidsProfile(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.KidsProfileSerializer)
    def delete(self, request, **kwargs):
        profile_id = request.query_params.get("id")
        if not profile_id:
            return Response({"error": "Profile ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            profile = models.KidsProfile.objects.get(id=profile_id, user=request.user)
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except models.KidsProfile.DoesNotExist:
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
class QueryEnrollments(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @extend_schema(responses=serializers.EnrollmentSerializer)
    def get(self, request, **kwargs):
        user = models.BitCampUser.objects.get(id=request.user.id)

        if user.is_superuser:
            date_str = request.GET.get("date", None)
            if date_str:
                date_obj = parse_date(date_str)
                if date_obj is None:
                    return Response({"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)
                
                datetime_obj = datetime.combine(date_obj, time.min)

                users_after_date = models.Enrollment.objects.filter(last_payment__lt=datetime_obj)
                print(datetime_obj)
                
                serializer = serializers.EnrollmentSerializer(users_after_date, many=True)
                return Response(serializer.data)
            else:
                return Response({"error": "Date parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

@staff_member_required
def ManualTransaction(request, enrollment_id):
    enrollment = models.Enrollment.objects.get(id=enrollment_id)
    if enrollment is None:
        return HttpResponseRedirect(reverse("admin:index"))
    
    service = enrollment.service_id
    last_payment = models.Payment.objects.filter(enrollment = enrollment_id).latest("created_at")
    
    payload = {
        "source": "Card",
        # Object of type Decimal is not JSON serializable
        "amount": service.price.__str__(),
        "currency": "GEL",
        "language": "KA",
        "token": last_payment.token.__str__(),
        "hooks": {
            "webhookGateway": "https://platform.bitcamp.ge/payments/payze_hook",
            "successRedirectGateway": f"https://platform.bitcamp.ge/enrollments/{enrollment.id}/check-payze-subscription-status",
            "errorRedirectGateway": f"https://platform.bitcamp.ge/enrollments/{enrollment.id}/check-payze-subscription-status"
        },
        "metadata": {
            "extraAttributes": [
                { "key": "service", "value": service.title },
                { "key": "email", "value": enrollment.user.email }
            ]
        }
    }
    headers = {
        "Accept": "application/*+json",
        "Content-Type": "application/json",
        "Authorization": settings.PAYZE_API_KEY,
        "User-Agent": "python-app/v1"
    }
    
    
    response = requests.put('https://payze.io/v2/api/payment', json=payload, headers=headers)
    
    # Access the response body as JSON
    response_data = response.text
    print(f"Response Data: {response_data}")
    
    
    
    if response.status_code == 200:
        logger.info("Request sent and response received successfully from Payze")
        
        payze_data = response.json()
        payment = models.Payment.objects.create(
            enrollment=enrollment,
            amount=payze_data['data']['payment']['amount'],
            status=payze_data['data']['payment']['status'],
            payze_transactionId=payze_data['data']['payment']['transactionId'],
            payze_paymentId=payze_data['data']['payment']['id'],
            # ERROR:  null value in column "cardMask" violates not-null constraint. Let's check the response and see if cardMask is null and if so, let's set it to empty string
            cardMask=payze_data['data']['payment']['cardPayment']['cardMask'] if payze_data['data']['payment']['cardPayment']['cardMask'] is not None else "",
            token=payze_data['data']['payment']['cardPayment']['token'],
        )
        
        # Save the Payment object
        logger.info("Saving Payze payment")
        payment.save()
        logger.info("Saving Payze payment successful")
        
        
        return HttpResponseRedirect(reverse("admin:accounts_enrollment_change", args=[enrollment_id]), status=status.HTTP_201_CREATED)
    else:
        return HttpResponseRedirect(reverse("admin:accounts_enrollment_change", args=[enrollment_id]), status=status.HTTP_400_BAD_REQUEST)
