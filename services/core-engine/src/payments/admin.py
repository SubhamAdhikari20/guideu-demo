from django.contrib import admin

from .models import PaymentTransaction, EscrowLedger


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'booking', 'guide_request', 'service_booking', 'amount', 'currency', 'status', 'gateway', 'mode', 'created_at')
    list_filter = ('status', 'gateway', 'mode')
    search_fields = ('gateway_reference', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EscrowLedger)
class EscrowLedgerAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'entry_type', 'amount', 'balance', 'created_at')
    list_filter = ('entry_type',)
    search_fields = ('transaction__gateway_reference',)
    readonly_fields = ('created_at', 'updated_at')
