from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from . import models
from django.conf import settings
import requests

# Register your models here.

class EnrollmentInline(admin.TabularInline):
    model = models.Enrollment
    extra = 0  # Adjust as needed

class PaymentInline(admin.TabularInline):
    model = models.Payment
    extra = 0  # Adjust as needed


class StatusFilter(admin.SimpleListFilter):
    title = _('status')  # or use 'verbose_name' of the field
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each tuple is the coded value
        for the option that will appear in the URL query. The second element is the
        human-readable name for the option that will appear in the dropdown menu.
        """
        return (
            ('active', _('Active')),
            ('inactive', _('Inactive')),
            # Add more status options here
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value provided in the query string
        and retrievable via `self.value()`.
        """
        if self.value() == 'active':
            return queryset.filter(status='active')
        if self.value() == 'inactive':
            return queryset.filter(status='inactive')
        # Handle more statuses here

class EnrollmentAdmin(admin.ModelAdmin):
    inlines = [PaymentInline,]
    
    change_form_template = "admin/accounts/enrollment/change_form.html"
    
    list_display = ('id', 'get_user_email','get_service_title', 'get_program_title', 'status')

    # Adding filters
    list_filter = ('status', 'name', 'user__email')

    # Search functionality (optional, but useful)
    search_fields = ('status', 'user__email')
    
    def get_user_email(self, obj):
        # Return user email if it exists, otherwise return a default value
        return obj.user.email if obj.user else 'No email'
    get_user_email.short_description = 'User Email'  # Sets column name in admin
    
    def get_service_title(self, obj):
        return obj.service_id.title if obj.service_id else 'No Service'
    get_service_title.short_description = 'Service Title'

    def get_program_title(self, obj):
        return obj.program_id.title if obj.program_id else 'No Program'
    get_program_title.short_description = 'Program Title'

    
admin.site.register(models.Enrollment, EnrollmentAdmin)
        
class PaymentAdmin(admin.ModelAdmin):
    actions = ["process_refund"]

    def process_refund(self, request, queryset):
        for payment in queryset:
            try:
                # Example API call
                headers = {"Authorization": f"Bearer {settings.PAYZE_API_KEY}"}
                response = requests.put(
                    "https://api.payze.io/payment/refund",
                    headers=headers,
                    json={"paymentId": payment.payze_paymentId}
                )
                if response.status_code == 200:
                    self.message_user(request, "Refund processed successfully for payment ID: {}".format(payment.pk))
                else:
                    self.message_user(request, "Failed to process refund for payment ID: {}. Error: {}".format(payment.pk, response.text))
            except Exception as e:
                self.message_user(request, "An error occurred while processing the refund for payment ID: {}. Error: {}".format(payment.pk, str(e)))

    process_refund.short_description = "Refund selected payments"
    
    list_display = ('id', 'amount', 'status', 'enrollment', 'created_at', 'updated_at')

    # Adding filters
    list_filter = (StatusFilter, 'status', 'created_at', 'updated_at', 'enrollment')

    # Search functionality (optional, but useful)
    search_fields = ('status', 'enrollment__user__email', 'payze_transactionId', 'payze_paymentId')

admin.site.register(models.Payment, PaymentAdmin)


class BitCampUserAdmin(UserAdmin):   
    inlines = [EnrollmentInline,]
 
    # Use the default fields from UserAdmin and add 'phone_number'
    fieldsets = UserAdmin.fieldsets + (
        (('Additional Info'), {'fields': ('phone_number',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (('Additional Info'), {'fields': ('phone_number',)}),
    )

    list_display = ('email', 'first_name', 'last_name', 'phone_number')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')

admin.site.register(models.BitCampUser, BitCampUserAdmin)