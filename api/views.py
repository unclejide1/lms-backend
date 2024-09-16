from django.shortcuts import redirect
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Q, F, Count, Sum, Max
from django.db import transaction
from django.contrib.auth.hashers import check_password
from django.db.models.functions import ExtractMonth
from django.core.files.uploadedfile import InMemoryUploadedFile

# Restframework
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

# Others
from decimal import Decimal
import json
import random
import stripe
import requests
from datetime import datetime, timedelta
from distutils.util import strtobool

# Serializers
from api import serializer as api_serializers

# Models
from api.models import Certificate, CompletedLesson, Country, EnrolledCourse, Note, Teacher, Category, Course, Variant, VariantItem, Cart, CartOrder, CartOrderItem, Review, Notification, Coupon, Wishlist, Question_Answer, Question_Answer_Message
from userauths.models import Profile, User


stripe.api_key = settings.STRIPE_SECRET_KEY
PAYPAL_CLIENT_ID = settings.PAYPAL_CLIENT_ID
PAYPAL_SECRET_ID = settings.PAYPAL_SECRET_ID


# Course API Views
class CategoryListView(generics.ListAPIView):
    serializer_class = api_serializers.CategorySerializer
    queryset = Category.objects.filter(active=True)
    permission_classes = [AllowAny]

class CourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]
    queryset = Course.objects.filter(platform_status="Published", teacher_course_status="Published")

class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        slug = self.kwargs['slug']
        return Course.objects.get(slug=slug, platform_status="Published", teacher_course_status="Published")

class CartAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.CartSerializer
    queryset = Cart.objects.all()
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() method to handle the case where user_id is not present
        
        print("user_id =======", user_id)

        if user_id is not None:
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(Q(user=user, cart_id=cart_id) | Q(user=user))
        else:
            queryset = Cart.objects.filter(cart_id=cart_id)
        
        return queryset

    def create(self, request, *args, **kwargs):
        payload = request.data
        
        course_id = payload['course_id']
        user_id = payload['user']
        price = payload['price']
        country_name = payload['country']
        cart_id = payload['cart_id']
        
        course = Course.objects.filter(id=course_id, platform_status="Published", teacher_course_status="Published").first()

        if user_id != "undefined":
            user = User.objects.filter(id=user_id).first()
        else:
            user = None
        print("user_id =======", user_id)
        print("user =======", user)
        
        try:
            country_obj = Country.objects.filter(name=country_name).first()
            country = country_obj.name
        except:
            country_obj = None
            country = "United States"

        print("country ========", country)
        if country_obj:
            tax_rate = country_obj.tax_rate / 100
        else:
            tax_rate = 0

        cart = Cart.objects.filter(cart_id=cart_id, course=course).first()

        if cart:
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id

            cart.total = Decimal(cart.price) + cart.tax_fee
            cart.save()

            return Response({"message": "Cart updated successfully"}, status=status.HTTP_200_OK)
        else:
            cart = Cart()
            cart.course = course
            cart.user = user
            cart.price = price
            cart.tax_fee = Decimal(price) * Decimal(tax_rate)
            cart.country = country
            cart.cart_id = cart_id

            cart.total = Decimal(cart.price) + cart.tax_fee
            cart.save()

            return Response( {"message": "Cart Created Successfully"}, status=status.HTTP_201_CREATED)

class CartListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CartSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() method to handle the case where user_id is not present
        user = User.objects.filter(id=user_id).first()

        queryset = Cart.objects.filter(Q(cart_id=cart_id) | Q(user=user))
        
        return queryset

class CartStatsAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartSerializer
    lookup_field = 'cart_id'
    permission_classes = [AllowAny]

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        user_id = self.kwargs.get('user_id')  # Use get() to handle cases where 'user_id' is not present

        if user_id is not None:
            user = User.objects.get(id=user_id)
            queryset = Cart.objects.filter(cart_id=cart_id, user=user)
        else:
            queryset = Cart.objects.filter(cart_id=cart_id)
        return queryset

    def get(self, request, *args, **kwargs):
        # Get the queryset of cart items based on 'cart_id' and 'user_id' (if provided)
        queryset = self.get_queryset()

        # Initialize sums for various cart item attributes
        total_price = 0.0
        total_tax = 0.0
        total_total = 0.0

        # Iterate over the queryset of cart items to calculate cumulative sums
        for cart_item in queryset:
            # Calculate the cumulative shipping, tax, service_fee, and total values
            total_price += float(self.calculate_price(cart_item))
            total_tax += float(self.calculate_tax(cart_item))
            total_total += round(float(self.calculate_total(cart_item)), 2)

        # Create a data dictionary to store the cumulative values
        data = {
            'price': round(total_price, 2),
            'tax': total_tax,
            'total': total_total,
        }

        # Return the data in the response
        return Response(data)

    def calculate_price(self, cart_item):
        # Implement your shipping calculation logic here for a single cart item
        # Example: Calculate based on weight, destination, etc.
        return cart_item.price

    def calculate_tax(self, cart_item):
        # Implement your tax calculation logic here for a single cart item
        # Example: Calculate based on tax rate, product type, etc.
        return cart_item.tax_fee

    def calculate_total(self, cart_item):
        # Implement your total calculation logic here for a single cart item
        # Example: Sum of sub_total, shipping, tax, and service_fee
        return cart_item.total
    
class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.CartSerializer
    lookup_field = 'cart_id'  

    def get_object(self):
        cart_id = self.kwargs['cart_id']
        item_id = self.kwargs['item_id']
        
        cart = Cart.objects.get(cart_id=cart_id, id=item_id)
        return cart
    
class CreateOrderAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    queryset = CartOrder.objects.all()
    permission_classes = (AllowAny,)

    def create(self, request, *args, **kwargs):
        payload = request.data

        full_name = payload['full_name']
        email = payload['email']
        country = payload['country']
        cart_id = payload['cart_id']
        user_id = payload['user_id']
        print("user_id ============", user_id)
        if user_id != 0:
            user = User.objects.filter(id=user_id).first()
        else:
            user = None

        cart_items = Cart.objects.filter(cart_id=cart_id)

        total_price = Decimal(0.0)
        total_tax = Decimal(0.0)
        total_initial_total = Decimal(0.0)
        total_total = Decimal(0.0)

        with transaction.atomic():

            order = CartOrder.objects.create(
                student=user,
                payment_status="Processing",
                full_name=full_name,
                email=email,
                country=country
            )

            for c in cart_items:
                CartOrderItem.objects.create(
                    order=order,
                    course=c.course,
                    price=c.price,
                    tax_fee=c.tax_fee,
                    total=c.total,
                    initial_total=c.total,
                    teacher=c.course.teacher
                )

                total_price += Decimal(c.price)
                total_tax += Decimal(c.tax_fee)
                total_initial_total += Decimal(c.total)
                total_total += Decimal(c.total)

                order.teachers.add(c.course.teacher)

            order.sub_total=total_price
            order.tax_fee=total_tax
            order.initial_total=total_initial_total
            order.total=total_total
            order.save()

        return Response( {"message": "Order Created Successfully", 'order_oid':order.oid}, status=status.HTTP_201_CREATED)

class CheckoutAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]
    lookup_field = 'order_oid'  

    def get_object(self):
        order_oid = self.kwargs['order_oid']
        return CartOrder.objects.get(oid=order_oid)
    
class CouponApplyAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        payload = request.data

        order_oid = payload['order_oid']
        coupon_code = payload['coupon_code']

        order = CartOrder.objects.get(oid=order_oid)
        coupon = Coupon.objects.filter(code__iexact=coupon_code, active=True).first()
        
        if coupon:
            order_items = CartOrderItem.objects.filter(order=order, teacher=coupon.teacher)
            if order_items:
                for i in order_items:
                    if not coupon in i.coupon.all():
                        discount = i.total * coupon.discount / 100
                        
                        i.total -= discount
                        i.price -= discount
                        i.coupon.add(coupon)
                        i.coupon.add(coupon)
                        i.saved += discount
                        i.applied_coupon = True

                        order.coupons.add(coupon)
                        order.total -= discount
                        order.sub_total -= discount
                        order.saved += discount

                        i.save()
                        order.save()
                        coupon.used_by.add(order.student)
                        return Response( {"message": "Coupon Activated"}, status=status.HTTP_200_OK)
                    else:
                        return Response( {"message": "Coupon Already Activated"}, status=status.HTTP_200_OK)
            return Response( {"message": "Order Item Does Not Exists"}, status=status.HTTP_200_OK)
        else:
            return Response( {"message": "Coupon Does Not Exists"}, status=status.HTTP_404_NOT_FOUND)

class StripeCheckoutAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer

    def create(self, request, *args, **kwargs):
        order_oid = self.kwargs['order_oid']
        order = CartOrder.objects.filter(oid=order_oid).first()

        if not order:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


        try:
            checkout_session = stripe.checkout.Session.create(
                customer_email=order.email,
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': order.full_name,
                            },
                            'unit_amount': int(order.total * 100),
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                # success_url = f"{settings.SITE_URL}/payment-success/{{order.oid}}/?session_id={{CHECKOUT_SESSION_ID}}",
                # cancel_url = f"{settings.SITE_URL}/payment-success/{{order.oid}}/?session_id={{CHECKOUT_SESSION_ID}}",

                success_url=settings.SITE_URL+'/payment-success/'+ order.oid +'?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.SITE_URL+'/?session_id={CHECKOUT_SESSION_ID}',
            )
            order.stripe_session_id = checkout_session.id 
            order.save()

            return redirect(checkout_session.url)
        except stripe.error.StripeError as e:
            return Response( {'error': f'Something went wrong when creating stripe checkout session: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def get_access_token(client_id, secret_key):
    # Function to get access token from PayPal API
    token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    data = {'grant_type': 'client_credentials'}
    auth = (client_id, secret_key)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        print("access_token ====", response.json()['access_token'])
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to get access token from PayPal. Status code: {response.status_code}') 

class PaymentSuccessAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CartOrderSerializer
    queryset = CartOrder.objects.all()
    
    def create(self, request, *args, **kwargs):
        payload = request.data
        
        order_oid = payload['order_oid']
        session_id = payload['session_id']
        paypal_order_id = payload['paypal_order_id']

        print("order_oid ====", order_oid)
        print("session_id ====", session_id)
        print("paypal_order_id ====", paypal_order_id)

        order = CartOrder.objects.get(oid=order_oid)
        order_items = CartOrderItem.objects.filter(order=order)

        if paypal_order_id != "null":
            paypal_api_url = f'https://api-m.sandbox.paypal.com/v2/checkout/orders/{paypal_order_id}'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {get_access_token(PAYPAL_CLIENT_ID, PAYPAL_SECRET_ID)}',
            }
            response = requests.get(paypal_api_url, headers=headers)
            print("response ========", response)
            if response.status_code == 200:
                paypal_order_data = response.json()
                paypal_payment_status = paypal_order_data['status']
                if paypal_payment_status == 'COMPLETED':
                    if order.payment_status == "Processing":
                        order.payment_status = "Paid"
                        order.save()
                        if order.student != None:
                            Notification.objects.create(user=order.student, order=order)

                        for o in order_items:
                            Notification.objects.create(teacher=o.teacher, order=order, order_item=o)
                            EnrolledCourse.objects.create(
                                course=o.course,
                                user=order.student,
                                teacher=o.teacher,
                                order_item=o,
                            )
                        return Response( {"message": "Payment Successfull"}, status=status.HTTP_201_CREATED)
                    else:
                        
                        return Response( {"message": "Already Paid"}, status=status.HTTP_201_CREATED)
            else:
                return Response( {"message": "An Error Occured 22"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # Process Stripe Payment
        if session_id != "null":
            session = stripe.checkout.Session.retrieve(session_id)

            if session.payment_status == "paid":
                if order.payment_status == "processing":
                    order.payment_status = "paid"
                    order.save()

                    if order.student != None:
                        Notification.objects.create(user=order.student, order=order)

                    for o in order_items:
                        Notification.objects.create(teacher=o.teacher, order=order, order_item=o)

                    return Response( {"message": "Payment Successfull"}, status=status.HTTP_201_CREATED)
                else:
                    return Response( {"message": "Already Paid"}, status=status.HTTP_201_CREATED)
                
            elif session.payment_status == "unpaid":
                return Response( {"message": "unpaid!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif session.payment_status == "canceled":
                return Response( {"message": "cancelled!"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response( {"message": "An Error Occured 1"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            session = None
            return Response( {"message": "An Error Occured 2"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SearchProductsAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.GET.get('query')
        return Course.objects.filter(title__icontains=query, platform_status="Published", teacher_course_status="Published")
       


################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
################################ Student Dashboard ################################
    
    
class StudentSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializers.StudentSummarySerializer
    #     # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny] 

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        user = User.objects.get(id=user_id)

        total_courses = EnrolledCourse.objects.filter(user=user).count()
        completed_lessons = CompletedLesson.objects.filter(user=user).count()
        achieved_ertificates = Certificate.objects.filter(user=user).count()

        return [{
            'total_courses': total_courses,
            'completed_lessons': completed_lessons,
            'achieved_ertificates': achieved_ertificates,
        }]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class StudentCourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.EnrolledCourseSerializer
        # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']

        user = User.objects.get(id=user_id)
        return EnrolledCourse.objects.filter(user=user)

class StudentCourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.EnrolledCourseSerializer
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated] # student isauthed
    lookup_field = 'enrollment_id'
    
    def get_object(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']
        
        user = User.objects.get(id=user_id)
        return EnrolledCourse.objects.get(user=user, enrollment_id=enrollment_id)
    
class StudentCourseCompletedCreateAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.CompletedLessonSerializer
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated] # student isauthed
    
    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        course_id = request.data['course_id']
        variant_item_id = request.data['variant_item_id']
        
        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)
        variant_item = VariantItem.objects.get(variant_item_id=variant_item_id)
        
        completed_lesson = CompletedLesson.objects.filter(user=user, course=course, variant_item=variant_item).first()
        if completed_lesson:
            completed_lesson.delete()
            return Response({"message": "Course Marked As Not Completed"})
        else:
            CompletedLesson.objects.create(user=user, course=course, variant_item=variant_item)
            return Response({"message": "Course Marked As Completed"})

class StudentNoteCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.NoteSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']

        user = User.objects.get(id=user_id)
        enrolled = EnrolledCourse.objects.get(enrollment_id=enrollment_id)

        return Note.objects.filter(user=user, course=enrolled.course)


    def create(self, request, *args, **kwargs):
        payload = request.data
        
        user_id = payload['user_id']
        enrollment_id = payload['enrollment_id']
        title = payload['title']
        note = payload['note']

        user = User.objects.get(id=user_id)
        enrolled = EnrolledCourse.objects.get(enrollment_id=enrollment_id)

        Note.objects.create(user=user, course=enrolled.course, note=note, title=title)

        return Response({"message": "Note created successfully"})

class StudentNoteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.NoteSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        enrollment_id = self.kwargs['enrollment_id']
        note_id = self.kwargs['note_id']

        user = User.objects.get(id=user_id)
        enrolled = EnrolledCourse.objects.get(enrollment_id=enrollment_id)
        note = Note.objects.get(user=user, course=enrolled.course, id=note_id)
        return note

class StudentRateCourseAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        payload = request.data

        user_id = payload['user_id']
        course_id = payload['course_id']
        rating = payload['rating']
        review = payload['review']

        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)

        Review.objects.create(
            user=user,
            course=course,
            rating=rating,
            review=review
        )

        return Response({"message": "Review Created!"}, status=status.HTTP_201_CREATED)

class StudentRateCourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        user_id = self.kwargs['user_id']
        review_id = self.kwargs['review_id']

        user = User.objects.get(id=user_id)
        return Review.objects.get(id=review_id, user=user)

class QuizListAPIView(generics.ListAPIView):
    pass

class QuizDetailAPIView(generics.RetrieveAPIView):
    pass

class QuizDetailAPIView(generics.RetrieveAPIView):
    pass

class QuizResultAPIView(generics.RetrieveAPIView):
    pass

class StudentWishListListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.WishlistSerializer
        # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.kwargs['user_id']

        user = User.objects.get(id=user_id)
        return Wishlist.objects.filter(user=user)
    
    def create(self, request, *args, **kwargs):
        payload = request.data

        user_id = payload['user_id']
        course_id = payload['course_id']

        user = User.objects.get(id=user_id)
        course = Course.objects.get(id=course_id)
        wishlist = Wishlist.objects.filter(user=user, course=course).first()
        if wishlist:
            wishlist.delete()
            return Response({"message": "Deleted From Wishlist"}, status=status.HTTP_200_OK)
        else:
            Wishlist.objects.create(user=user, course=course)
            return Response({"message": "Added to wishlist"}, status=status.HTTP_201_CREATED)
  
class QuestionAnswerListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.Question_AnswerSerializer
        # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs['course_id']

        course = Course.objects.get(id=course_id)
        return Question_Answer.objects.filter(course=course)
    
class QuestionAnswerDetailAPIView(generics.ListAPIView):
    serializer_class = api_serializers.Question_AnswerSerializer
        # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        qa_id = self.kwargs['qa_id']

        course = Course.objects.get(id=course_id)
        return Question_Answer.objects.get(id=qa_id)
    
class QuestionAnswerCreateAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.Question_AnswerSerializer
        # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        payload = request.data

        course_id = payload['course_id']
        user_id = payload['user_id']
        title = payload['title']
        message = payload['message']

        course = Course.objects.get(id=course_id)
        user = User.objects.get(id=user_id)
        question = Question_Answer.objects.create(
            course=course,
            user=user, 
            title=title, 
        )

        Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question,
        )

        return Response({"message": "Group Conversation Started"})

class QuestionAnswerMessageSendAPIView(generics.CreateAPIView):
    serializer_class = api_serializers.Question_AnswerSerializer
        # permission_classes = [IsAuthenticated] # student isauthed
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        payload = request.data

        course_id = payload['course_id']
        qa_id = payload['qa_id']
        user_id = payload['user_id']
        message = payload['message']

        course = Course.objects.get(id=course_id)
        question = Question_Answer.objects.get(qa_id=qa_id)
        user = User.objects.get(id=user_id)

        Question_Answer_Message.objects.create(
            course=course,
            user=user,
            message=message,
            question=question,
        )
        
        question_serializer = api_serializers.Question_AnswerSerializer(question)

        return Response({"message": "Message Sent", "question": question_serializer.data})
    




################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
################################ Teacher Dashboard ################################
    

    
class TeacherSummaryAPIView(generics.ListAPIView):
    serializer_class = api_serializers.TeacherSummarySerializer
    permission_classes = [AllowAny] 
    #permission_classes = [IsAuthenticated] # teacher isauthed

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)
        print("teacher_id =======", teacher_id)
        print("teacher =======", teacher)
        one_month_ago = datetime.today() - timedelta(days=28)

        total_courses = Course.objects.filter(teacher=teacher).count()
        total_revenue = CartOrderItem.objects.filter(teacher=teacher, order__payment_status="Paid").aggregate(total_revenue=Sum("price"))["total_revenue"] or 0
        monthly_revenue = CartOrderItem.objects.filter(teacher=teacher, order__payment_status="Paid", date__gte=one_month_ago).aggregate(total_revenue=Sum("price"))["total_revenue"] or 0
        
        # Query 
        courses = EnrolledCourse.objects.filter(teacher=teacher)
        unique_student_ids = set()
        students = []
        for course in courses:
            if course.user_id not in unique_student_ids:
                user = User.objects.get(id=course.user_id)
                student = {
                    'username': user.username,
                }
                students.append(student)
                unique_student_ids.add(course.user_id)

        return [{
            'total_courses': total_courses,
            'total_students': len(students),
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
        }]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
class TeacherCourseListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated] # teacher isauthed

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Course.objects.filter(teacher=teacher)

class TeacherReviewListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated] # teacher isauthed

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Review.objects.filter(course__teacher=teacher)

class TeacherReviewDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = api_serializers.ReviewSerializer
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated] # teacher isauthed

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        review_id = self.kwargs['review_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Review.objects.get(course__teacher=teacher, id=review_id)

class TeacherStudentsListAPIView(viewsets.ViewSet):

    # This defines a method named list within a class, likely a Django REST Framework view class. 
    # It takes three parameters: self, request, and teacher_id, with teacher_id having a default value of None.
    def list(self, request, teacher_id=None):
        
        # Retrieves a Teacher object from the database based on the provided teacher_id.
        teacher = Teacher.objects.get(id=teacher_id)
        
        # Retrieves all EnrolledCourse objects related to the specified teacher.
        courses = EnrolledCourse.objects.filter(teacher=teacher)
        
        # Initializes an empty set to store unique student IDs.
        unique_student_ids = set()
        
        # Initializes an empty list to store student data.
        students = []

        # Iterates over each EnrolledCourse related to the specified teacher.
        for course in courses:
           
            # Checks if the user ID associated with the current course is not already in the set of unique student IDs.
            # This ensures that each student is only added once to the students list.
            # when you have a ForeignKey field, such as user in your EnrolledCourse model, 
            # Django automatically creates an attribute user_id that represents the ID of the related object. 
            # So, even though you don't explicitly define a field named user_id in your EnrolledCourse model, 
            # Django automatically creates this attribute to represent the ID of the related user. 
            # Therefore, when you access course.user_id, you are accessing the ID of the user related to the EnrolledCourse instance.
            if course.user_id not in unique_student_ids:
                
                # Retrieves the User object associated with the current course.
                # This assumes that User is a Django model representing users.
                user = User.objects.get(id=course.user_id)
                
                # Creates a dictionary representing student data, including the username and the URL of the student's profile image.
                # This assumes that each user has a related profile object containing an image field.
                student = {
                    'full_name': user.profile.full_name,
                    'image': user.profile.image.url,
                    'country': course.order_item.order.country,
                    'date': course.date,
                }

                # Adds the student dictionary to the list of students.
                students.append(student)
                
                # Adds the user ID of the current course to the set of unique student IDs.
                unique_student_ids.add(course.user_id)

        # Returns a response containing the list of student data.
        # This assumes that Response is a class or function provided by a web framework like Django REST Framework to generate HTTP responses. It typically converts Python data structures (such as lists and dictionaries) into JSON format and includes it in the response.
        return Response(students)


    # def list(self, request, teacher_id=None):
    #     # Retrieve the teacher object based on the provided teacher_id
    #     teacher = Teacher.objects.get(id=teacher_id)

    #     # Query the EnrolledCourse model to filter courses taught by the teacher and
    #     # retrieve distinct users (students) associated with those courses
    #     students = EnrolledCourse.objects.filter(teacher=teacher).values('user').annotate(
    #         # Perform aggregation to get the maximum username and image for each user
    #         username=Max('user__username'), 
    #         image=Max('user__profile__image')
    #     )

    #     # Iterate through the students queryset
    #     for student in students:
    #         # Extract the image path for the student
    #         image_path = student['image']
    #         # Check if the image path is not empty
    #         if image_path:
    #             # Construct the complete image URL by appending the image path to MEDIA_URL
    #             student['image'] = settings.MEDIA_URL + image_path

    #     # Convert the queryset to a list of dictionaries for response
    #     student_list = []
    #     for student in students:
    #         student_list.append({
    #             'username': student['username'],
    #             'image': student['image']
    #         })

    #     # Return the list of students as a response
    #     return Response(student_list)
    
@api_view(('GET',))
def TeacherAllMonthsEarningListAPIView(request, teacher_id):
    teacher = Teacher.objects.get(id=teacher_id)
    monthly_earning_tracker = (
        CartOrderItem.objects
        .filter(teacher=teacher, order__payment_status="Paid")
        .annotate(
            month=ExtractMonth("date")
        )
        .values("month")
        .annotate(
            total_earning=Sum(F('price')))
        .order_by("month")
    )
    return Response(monthly_earning_tracker)

class TeacherBestSellingCoursesAPIView(viewsets.ViewSet):

    def list(self, request, teacher_id=None):
        # Get the current user (assuming it's the teacher/creator)
        teacher = Teacher.objects.get(id=teacher_id)

        # Retrieve all courses created by the teacher along with the total enrollment price
        courses_with_total_price = []
        courses = Course.objects.filter(teacher=teacher)

        for course in courses:
            # Calculate the total enrollment price for each course
            revenue = course.enrolledcourse_set.aggregate(total_price=Sum('order_item__price'))['total_price'] or 0
            sales = course.enrolledcourse_set.count()

            # Append course data to the list
            courses_with_total_price.append({
                'course_image': course.image.url,
                'course_title': course.title,
                'revenue': revenue,
                'sales': sales,
            })

        # Return the list of courses with total enrollment price
        return Response(courses_with_total_price)
    
class TeacherCourseOrdersListAPIView(generics.ListAPIView):
    serializer_class = api_serializers.CartOrderItemSerializer
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated] # teacher isauthed

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return CartOrderItem.objects.filter(teacher=teacher)

class TeacherQuestionAnswerListAPIView(generics.ListAPIView):

    serializer_class = api_serializers.Question_AnswerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)

        return Question_Answer.objects.filter(course__teacher=teacher)
    
class CourseCreateAPIView(generics.CreateAPIView):
    queryset = Course.objects.all()
    serializer_class = api_serializers.CourseSerializer

    def perform_create(self, serializer):
        serializer.is_valid(raise_exception=True)
        course_instance = serializer.save()
        print(self.request.data)

        variants_data = []

        for key, value in self.request.data.items():
            if key.startswith('variants') and '[variant_title]' in key:  # Check for the variant title field
                index = key.split('[')[1].split(']')[0]
                title = value
                
                variant_data = {'title': title}
                item_data_list = []
                current_item = {}

                for item_key, item_value in self.request.data.items():
                    if f'variants[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        if field_name == 'title':
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}
                        current_item.update({field_name: item_value})

                if current_item:
                    item_data_list.append(current_item)

                variants_data.append({'variant_data': variant_data, 'variant_item_data': item_data_list})
            
        for data_entry in variants_data:
            variant = Variant.objects.create( title=data_entry['variant_data']['title'], course=course_instance, )

            for item_data in data_entry['variant_item_data']:
                print("item_data ======", item_data)

                preview_value = item_data.get('preview')
                preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                VariantItem.objects.create(
                    variant=variant,
                    title=item_data.get('title'),
                    description=item_data.get('description'),
                    file=item_data.get('file'),
                    preview=preview,
                )
        
    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={'course_instance': course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance)

class CourseUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = api_serializers.CourseSerializer

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']

        teacher = Teacher.objects.get(id=teacher_id)
        return Course.objects.get(teacher=teacher, course_id=course_id)

    def update(self, request, *args, **kwargs):
        print("request.data['category'] =======", request.data['category'])
        course = self.get_object()

        serializer = self.get_serializer(course, data=request.data)
        serializer.is_valid(raise_exception=True)


        if 'image' in request.data and isinstance(request.data['image'], InMemoryUploadedFile):
            course.image = request.data['image']

        elif 'image' in request.data and str(request.data['image']) == "No file":
            course.image = None

        if 'file' in request.data and not str(request.data['file']).startswith("http://"):
            course.file = request.data['file']

        if 'category' in request.data and request.data['category'] != 'NaN' and request.data['category'] != 'undefined':
            category = Category.objects.get(id=request.data['category'])
            course.category = category

        self.perform_update(serializer)
        self.update_variants(course, request.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

        
    def update_variants(self, course, request_data):
        for key, value in request_data.items():
            
            # print("key =========", key)
            # print("value =========", value)

            if key.startswith('variants') and '[variant_title]' in key:  # Check for the variant title field
                index = key.split('[')[1].split(']')[0]
                title = value

                id_key = f'variants[{index}][variant_id]'
                variant_id = request_data.get(id_key)

                variant_data = {'title': title}
                item_data_list = []
                current_item = {}

                for item_key, item_value in request_data.items():
                    if f'variants[{index}][items]' in item_key:
                        field_name = item_key.split('[')[-1].split(']')[0]
                        print("field_name ========", item_value)
                        if field_name == 'title':
                            if current_item:
                                item_data_list.append(current_item)
                            current_item = {}
                        current_item.update({field_name: item_value})
                        print("current_item =====", current_item)
                if current_item:
                    item_data_list.append(current_item)

                # Find the existing variant by ID
                existing_variant = course.variant_set.filter(id=variant_id).first()


                if existing_variant:
                    print("item_data_list existing_variant ==========", item_data_list)

                    existing_variant.title = title
                    existing_variant.save()

                    # Update or create variant items
                    for item_data in item_data_list[1:]:
                        preview_value = item_data.get('preview')
                        preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                        variant_item = VariantItem.objects.filter(variant_item_id=item_data.get("variant_item_id")).first()

                        if not str(item_data.get("file")).startswith("http://"):
                            if item_data.get("file") != "null":
                                file = item_data.get("file")
                            else:
                                file = None

                            title = item_data.get('title')
                            description = item_data.get('description')

                            if variant_item:
                                variant_item.title = title
                                variant_item.description = description
                                variant_item.file = file
                                variant_item.preview = preview
                            else:
                                variant_item = VariantItem.objects.create(
                                    variant=existing_variant,
                                    title=title,
                                    description=description,
                                    file=file,
                                    preview=preview,
                                )
                        else:
                            title = item_data.get('title')
                            description = item_data.get('description')

                            if variant_item:
                                variant_item.title = title
                                variant_item.description = description
                                variant_item.preview = preview
                            else:
                                variant_item = VariantItem.objects.create(
                                    variant=existing_variant,
                                    title=title,
                                    description=description,
                                    preview=preview,
                                )

                        variant_item.save()
                else:

                    new_variant = Variant.objects.create(
                        course=course,
                        title=title,
                    )
                    print("item_data_list NOT existing_variant ==========", item_data_list)
                    print("new_variant ==========", new_variant)

                    # Create new variant items
                    for item_data in item_data_list:
                        print("item_data ==========", item_data)
                        preview_value = item_data.get('preview')
                        preview = bool(strtobool(str(preview_value))) if preview_value is not None else False

                        VariantItem.objects.create(
                            variant=new_variant,
                            title=item_data.get('title'),
                            description=item_data.get("description"),
                            file=item_data.get("file"),
                            preview=preview,
                        )

    def save_nested_data(self, course_instance, serializer_class, data):
        serializer = serializer_class(data=data, many=True, context={'course_instance': course_instance})
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course_instance)

class CourseVariantDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.VariantSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        variant_id = self.kwargs['variant_id']
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']
        print("variant_id =====", variant_id)
        print("teacher_id =====", teacher_id)
        print("course_id =====", course_id)
        teacher = Teacher.objects.get(id=teacher_id)
        course = Course.objects.get(teacher=teacher, course_id=course_id)
        return Variant.objects.get(variant_id=variant_id)
    

class CourseVariantItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.VariantItemSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        variant_id = self.kwargs['variant_id']
        variant_item_id = self.kwargs['variant_item_id']
        teacher_id = self.kwargs['teacher_id']
        course_id = self.kwargs['course_id']

        teacher = Teacher.objects.get(id=teacher_id)
        course = Course.objects.get(teacher=teacher, course_id=course_id)
        variant = Variant.objects.get(course=course, variant_id=variant_id)
        return VariantItem.objects.get(variant=variant, variant_item_id=variant_item_id)


class TeacherCourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        course_id = self.kwargs['course_id']
        return Course.objects.get(course_id=course_id)

class TeacherCourseDeleteAPIView(generics.DestroyAPIView):
    serializer_class = api_serializers.CourseSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        course_id = self.kwargs['course_id']
        return Course.objects.get(course_id=course_id)


class TeacherCouponListAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.CouponSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Coupon.objects.filter(teacher=teacher)
    
class TeacherCouponDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.CouponSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        coupon_id = self.kwargs['coupon_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Coupon.objects.get(teacher=teacher, id=coupon_id)


class TeacherNotificationListAPIView(generics.ListCreateAPIView):
    serializer_class = api_serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Notification.objects.filter(teacher=teacher, seen=False)
    
class TeacherNotificationDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = api_serializers.NotificationSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        teacher_id = self.kwargs['teacher_id']
        noti_id = self.kwargs['noti_id']
        teacher = Teacher.objects.get(id=teacher_id)
        return Notification.objects.get(teacher=teacher, id=noti_id)

    