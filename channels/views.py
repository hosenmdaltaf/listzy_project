from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import ConnectedChannel
from .services import get_marketplace_service
import requests
from django.conf import settings
import secrets

@login_required
def channel_list_view(request):
    """List all connected channels for the user"""
    channels = ConnectedChannel.objects.filter(user=request.user).order_by('-connected_at')
    
    # Group channels by type
    marketplace_channels = channels.filter(platform__in=['shopify', 'etsy', 'woocommerce'])
    social_channels = channels.filter(platform__in=['instagram', 'facebook', 'tiktok'])
    
    context = {
        'marketplace_channels': marketplace_channels,
        'social_channels': social_channels,
        'total_channels': channels.count()
    }
    return render(request, 'channels/list.html', context)

@login_required
def connect_channel_view(request):
    """Show available channels to connect"""
    user_channels = ConnectedChannel.objects.filter(user=request.user).values_list('platform', flat=True)
    
    available_platforms = [
        {
            'id': 'shopify',
            'name': 'Shopify',
            'description': 'Connect your Shopify store to sync products',
            'icon': '🛍️',
            'type': 'marketplace',
            'connected': 'shopify' in user_channels
        },
        {
            'id': 'etsy',
            'name': 'Etsy',
            'description': 'Sell handmade and vintage items on Etsy',
            'icon': '🎨',
            'type': 'marketplace',
            'connected': 'etsy' in user_channels
        },
        {
            'id': 'instagram',
            'name': 'Instagram',
            'description': 'Post product photos to Instagram',
            'icon': '📸',
            'type': 'social',
            'connected': 'instagram' in user_channels
        },
        {
            'id': 'facebook',
            'name': 'Facebook',
            'description': 'Share products on Facebook pages',
            'icon': '👥',
            'type': 'social',
            'connected': 'facebook' in user_channels
        }
    ]
    
    context = {'platforms': available_platforms}
    return render(request, 'channels/connect.html', context)

def shopify_login(request):
    """Initiate Shopify OAuth flow"""
    shop = request.GET.get('shop')

    if not shop:
        return render(request, 'accounts/install.html')

    shop = sanitize_shop_param(shop)

    # Generate and store OAuth state
    state = generate_oauth_state()
    request.session['oauth_state'] = state

    # Manually override in dev if needed
    base_url = "https://7931-2a02-c7c-f0af-4700-e96b-da17-61e7-7f68.ngrok-free.app"
    redirect_uri = base_url + reverse('shopify_callback')

    # Build Shopify OAuth URL
    # must need to add this in producation need to add this in production and commeent base_url  and redirect_uri variable    
    # redirect_uri = request.build_absolute_uri(reverse('shopify_callback'))
    print(f"Redirect URI: {redirect_uri}")
    scope = 'read_products,write_products,read_orders,write_orders,read_customers,write_customers,read_inventory,write_inventory'

    install_url = f"https://{shop}/admin/oauth/authorize?" + urlencode({
        'client_id': settings.SHOPIFY_API_KEY,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state,
    })
    print(f"Install URL: {install_url}")

    return redirect(install_url)


@login_required
def shopify_connect_view(request):
    """Initiate Shopify OAuth connection"""
    if request.method == 'POST':
        shop_name = request.POST.get('shop_name', '').strip()
        
        if not shop_name:
            messages.error(request, 'Please enter your Shopify shop name.')
            return redirect('channels:connect')
        
        # Remove .myshopify.com if user included it
        shop_name = shop_name.replace('.myshopify.com', '')
        
        # Generate state for OAuth security
        state = secrets.token_urlsafe(32)
        request.session['oauth_state'] = state
        request.session['shop_name'] = shop_name
        
        # Shopify OAuth URL
        scopes = 'read_products,write_products,read_orders'

        # Manually override in dev if needed
        base_url = "https://98e3-2a02-c7c-f0af-4700-e0b3-cd47-9b3e-7946.ngrok-free.app"
        redirect_uri = base_url + reverse('channels:shopify_callback')

    # Build Shopify OAuth URL
    # must need to add this in producation need to add this in production and commeent base_url  and redirect_uri variable    
    # redirect_uri = request.build_absolute_uri(reverse('channels:shopify_callback'))
        oauth_url = (
            f"https://{shop_name}.myshopify.com/admin/oauth/authorize?"
            f"client_id={settings.SHOPIFY_API_KEY}&"
            f"scope={scopes}&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )
        
        return redirect(oauth_url)
    
    return render(request, 'channels/shopify_connect.html')

import hmac
import hashlib
from urllib.parse import urlencode

def is_valid_shopify_hmac(request, shared_secret):
    """Verify Shopify HMAC in OAuth callback"""
    params = request.GET.dict()
    hmac_received = params.pop('hmac', None)
    
    if not hmac_received:
        return False
    
    # Sort and encode parameters
    sorted_params = sorted((k, v) for k, v in params.items())
    message = urlencode(sorted_params)

    # Compute HMAC digest
    digest = hmac.new(
        key=shared_secret.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    # Compare securely
    return hmac.compare_digest(digest, hmac_received)


@login_required
def shopify_callback_view(request):
    """Handle Shopify OAuth callback"""
    code = request.GET.get('code')
    state = request.GET.get('state')
    shop = request.GET.get('shop')
    
    # Verify state parameter
    if state != request.session.get('oauth_state'):
        messages.error(request, 'Invalid OAuth state. Please try again.')
        return redirect('channels:connect')
    
       # 2. Check HMAC
    if not is_valid_shopify_hmac(request, settings.SHOPIFY_API_SECRET):
        messages.error(request, 'Invalid HMAC. Request may have been tampered with.')
        return redirect('channels:connect')
    
    if not code or not shop:
        messages.error(request, 'Shopify authorization failed.')
        return redirect('channels:connect')
    
    try:
        # Exchange code for access token
        token_url = f"https://{shop}/admin/oauth/access_token"
        token_data = {
            'client_id': settings.SHOPIFY_API_KEY,
            'client_secret': settings.SHOPIFY_API_SECRET,
            'code': code
        }
        
        response = requests.post(token_url, json=token_data, timeout=10)
        
        if response.status_code == 200:
            token_info = response.json()
            access_token = token_info.get('access_token')
            
            # Create or update channel
            channel, created = ConnectedChannel.objects.get_or_create(
                user=request.user,
                platform='shopify',
                shop_name=shop.replace('.myshopify.com', ''),
                defaults={
                    'access_token': access_token,
                    'platform_user_id': shop,
                    'status': 'active'
                }
            )
            
            if not created:
                channel.access_token = access_token
                channel.status = 'active'
                channel.save()
            
            # Test the connection
            service = get_marketplace_service(channel)
            success, message = service.test_connection()
            
            if success:
                messages.success(request, f'Shopify store "{shop}" connected successfully!')
            else:
                messages.warning(request, f'Connected but unable to verify: {message}')
            
            return redirect('channels:list')
        else:
            messages.error(request, 'Failed to get access token from Shopify.')
            
    except Exception as e:
        messages.error(request, f'Connection failed: {str(e)}')
    
    return redirect('channels:connect')

@login_required
@require_POST
def test_channel_connection(request, channel_id):
    """Test a channel connection via AJAX"""
    channel = get_object_or_404(ConnectedChannel, id=channel_id, user=request.user)
    
    try:
        service = get_marketplace_service(channel)
        success, message = service.test_connection()
        
        return JsonResponse({
            'success': success,
            'message': message,
            'status': channel.status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'status': 'error'
        })

@login_required
@require_POST
def disconnect_channel(request, channel_id):
    """Disconnect a channel"""
    channel = get_object_or_404(ConnectedChannel, id=channel_id, user=request.user)
    platform_name = channel.get_platform_display()
    
    # Delete all related listings
    channel.listings.all().delete()
    channel.delete()
    
    messages.success(request, f'{platform_name} disconnected successfully.')
    return redirect('channels:list')