from django.urls import path
from api import views as api_views
from userauths import views as userauths_views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    ############################ Authentication URLs ###########################
    ############################ Authentication URLs ###########################
    ############################ Authentication URLs ###########################
    ############################ Authentication URLs ###########################
    ############################ Authentication URLs ###########################
    ############################ Authentication URLs ###########################
    path('user/token/', userauths_views.MyTokenObtainPairView.as_view()),
    path('user/token/refresh/', TokenRefreshView.as_view()),
    path('user/register/', userauths_views.RegisterView.as_view()),
    path('user/password-reset/<email>/', userauths_views.PasswordEmailVerify.as_view()),
    path('user/password-change/', userauths_views.PasswordChangeView.as_view()),
    path('user/change-password/', userauths_views.ChangePasswordAPIView.as_view()),
    path('user/profile/<user_id>/', userauths_views.ProfileAPIView.as_view()),

    ########################### Course Core Routes ###########################
    ########################### Course Core Routes ###########################
    ########################### Course Core Routes ###########################
    ########################### Course Core Routes ###########################
    ########################### Course Core Routes ###########################
    ########################### Course Core Routes ###########################
    path('course/category/', api_views.CategoryListView.as_view()),
    path('course/course-list/', api_views.CourseListAPIView.as_view()),
    path('course/course-detail/<slug>/', api_views.CourseDetailAPIView.as_view()),
    path('cart/create/', api_views.CartAPIView.as_view()),
    path('cart/list/<cart_id>/', api_views.CartListAPIView.as_view()),
    path('cart/list/<cart_id>/<user_id>/', api_views.CartListAPIView.as_view()),
    path('cart/stats/<cart_id>/', api_views.CartStatsAPIView.as_view()),
    path('cart/stats/<cart_id>/<user_id>/', api_views.CartStatsAPIView.as_view()),
    path('cart/item-delete/<cart_id>/<item_id>/', api_views.CartItemDeleteAPIView.as_view()),
    path('cart/item-delete/<cart_id>/<item_id>/<user_id>/', api_views.CartItemDeleteAPIView.as_view()),
    path('order/create-order/', api_views.CreateOrderAPIView.as_view()),
    path('order/checkout/<order_oid>/', api_views.CheckoutAPIView.as_view()),
    path('order/coupon-apply/', api_views.CouponApplyAPIView.as_view()),
    path('payment/stripe-checkout/<order_oid>/', api_views.StripeCheckoutAPIView.as_view(), name='stripe-checkout'),
    path('payment/payment-success/', api_views.PaymentSuccessAPIView.as_view(), name='payment-success'),
    path('course/search/', api_views.SearchProductsAPIView.as_view()),

    ########################### Student API Routes ###########################
    ########################### Student API Routes ###########################
    ########################### Student API Routes ###########################
    ########################### Student API Routes ###########################
    ########################### Student API Routes ###########################
    ########################### Student API Routes ###########################

    path('student/summary/<user_id>/', api_views.StudentSummaryAPIView.as_view()),
    path('student/course-list/<user_id>/', api_views.StudentCourseListAPIView.as_view()),
    path('student/course-detail/<user_id>/<enrollment_id>/', api_views.StudentCourseDetailAPIView.as_view()),
    path('student/course-completed/', api_views.StudentCourseCompletedCreateAPIView.as_view()),
    path('student/course-note/<user_id>/<enrollment_id>/', api_views.StudentNoteCreateAPIView.as_view()),
    path('student/course-note-detail/<user_id>/<enrollment_id>/<note_id>/', api_views.StudentNoteDetailAPIView.as_view()),
    path('student/rate-course/', api_views.StudentRateCourseAPIView.as_view()),
    path('student/review-detail/<user_id>/<review_id>/', api_views.StudentRateCourseUpdateAPIView.as_view()),
    path('student/quiz/<user_id>/', api_views.QuizListAPIView.as_view()),
    path('student/quiz/<user_id>/', api_views.QuizDetailAPIView.as_view()),
    path('student/quiz/<user_id>/', api_views.QuizDetailAPIView.as_view()),
    path('student/quiz/<user_id>/', api_views.QuizResultAPIView.as_view()),
    path('student/wishlist/<user_id>/', api_views.StudentWishListListCreateAPIView.as_view()),
    path('student/question-answer-list/<course_id>/', api_views.QuestionAnswerListAPIView.as_view()),
    path('student/question-answer-detail/<course_id>/<qa_id>/', api_views.QuestionAnswerDetailAPIView.as_view()),
    path('student/question-answer-create/', api_views.QuestionAnswerCreateAPIView.as_view()),
    path('student/question-answer-message-create/', api_views.QuestionAnswerMessageSendAPIView.as_view()),

    ########################### Teacher API Routes ###########################
    ########################### Teacher API Routes ###########################
    ########################### Teacher API Routes ###########################
    ########################### Teacher API Routes ###########################
    ########################### Teacher API Routes ###########################
    ########################### Teacher API Routes ###########################

    path('teacher/summary/<teacher_id>/', api_views.TeacherSummaryAPIView.as_view()),
    path('teacher/course-lists/<teacher_id>/', api_views.TeacherCourseListAPIView.as_view()),
    path('teacher/review-lists/<teacher_id>/', api_views.TeacherReviewListAPIView.as_view()),
    path('teacher/review-detail/<teacher_id>/<review_id>/', api_views.TeacherReviewDetailAPIView.as_view()),
    path('teacher/student-lists/<teacher_id>/', api_views.TeacherStudentsListAPIView.as_view({'get': 'list'})),
    path('teacher/all-months-earning/<teacher_id>/', api_views.TeacherAllMonthsEarningListAPIView),
    path('teacher/best-course-earning/<teacher_id>/', api_views.TeacherBestSellingCoursesAPIView.as_view({'get': 'list'})),
    path('teacher/course-order-list/<teacher_id>/', api_views.TeacherCourseOrdersListAPIView.as_view()),
    path('teacher/question-answer-list/<teacher_id>/', api_views.TeacherQuestionAnswerListAPIView.as_view()),
    path('teacher/course-create/', api_views.CourseCreateAPIView.as_view()),
    path('teacher/course-update/<teacher_id>/<course_id>/', api_views.CourseUpdateAPIView.as_view()),
    path('teacher/course/variant-delete/<variant_id>/<teacher_id>/<course_id>/', api_views.CourseVariantDeleteAPIView.as_view()),
    path('teacher/course/variant/item-delete/<variant_id>/<variant_item_id>/<teacher_id>/<course_id>/', api_views.CourseVariantItemDeleteAPIView.as_view()),
    path('teacher/course-detail/<course_id>/', api_views.TeacherCourseDetailAPIView.as_view()),
    path('teacher/course-delete/<course_id>/', api_views.TeacherCourseDeleteAPIView.as_view()),
    path('teacher/coupon-list/<teacher_id>/', api_views.TeacherCouponListAPIView.as_view()),
    path('teacher/coupon-detail/<teacher_id>/<coupon_id>/', api_views.TeacherCouponDetailAPIView.as_view()),
    path('teacher/noti-list/<teacher_id>/', api_views.TeacherNotificationListAPIView.as_view()),
    path('teacher/noti-detail/<teacher_id>/<noti_id>/', api_views.TeacherNotificationDetailAPIView.as_view()),

]