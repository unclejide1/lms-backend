from django.contrib import admin
from api.models import Certificate, CompletedLesson, Teacher, Category, Course, Variant, VariantItem, Cart, CartOrder, CartOrderItem, EnrolledCourse, Review, Notification, Coupon, Wishlist, Country, Question_Answer, Question_Answer_Message, Note


class CourseAdmin(admin.ModelAdmin):
    list_editable = ['title', 'image', 'price', 'level', 'language',  'platform_status', 'teacher_course_status', 'featured', 'rating', 'course_id',]
    list_display = [ 'thumbnail', 'title', 'image', 'price', 'teacher', 'level', 'language', 'category', 'platform_status', 'teacher_course_status', 'featured', 'rating', 'course_id',]
    
class VariantAdmin(admin.ModelAdmin):
    list_display = ['course', 'title', 'variant_id']

    
class VariantItemAdmin(admin.ModelAdmin):
    list_display = [ 'variant', 'title', 'file', 'content_duration', 'preview', 'variant_item_id']
    list_editable = ['file', 'preview']

class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ['date']
    list_display = ['student', 'total', 'payment_status', 'full_name', 'date']


class CartOrderItemAdmin(admin.ModelAdmin):
    list_editable = ['date']
    list_display = ['order', 'total', 'date']


class EnrolledCourseAdmin(admin.ModelAdmin):
    list_display = [ 'course', 'user', 'teacher', 'order_item', 'date',]
    list_editable = [ 'user']



admin.site.register(Teacher)
admin.site.register(Category)
admin.site.register(Course, CourseAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(VariantItem, VariantItemAdmin)
admin.site.register(Cart)
admin.site.register(CartOrder, CartOrderAdmin)
admin.site.register(CartOrderItem, CartOrderItemAdmin)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(Coupon)
admin.site.register(Wishlist)
admin.site.register(Country)
admin.site.register(EnrolledCourse, EnrolledCourseAdmin)
admin.site.register(CompletedLesson)
admin.site.register(Certificate)
admin.site.register(Question_Answer)
admin.site.register(Question_Answer_Message)
admin.site.register(Note)

