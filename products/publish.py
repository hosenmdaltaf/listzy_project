from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.template.context_processors import csrf
from channels.models import ConnectedChannel, ProductListing
from channels.services import get_marketplace_service
from .models import Product
import json
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
@csrf_protect
def publish_product_to_channel(request, product_id, channel_id):
    """Publish a specific product to a specific channel"""
    try:
        product = get_object_or_404(Product, id=product_id, user=request.user)
        channel = get_object_or_404(ConnectedChannel, id=channel_id, user=request.user)
        
        # Check if already published
        existing_listing = ProductListing.objects.filter(
            product=product, 
            channel=channel
        ).first()
        
        if existing_listing and existing_listing.status == 'published':
            return JsonResponse({
                'success': False,
                'message': f'Product is already published to {channel.get_platform_display()}'
            })
        
        # Get marketplace service
        service = get_marketplace_service(channel)
        
        # Publish product
        if existing_listing:
            success, message = service.update_product(product, existing_listing)
        else:
            success, message = service.create_product(product)
        
        return JsonResponse({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f'Publishing error: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Publishing failed: {str(e)}'
        })

@login_required
@require_POST
@csrf_protect
def publish_product_to_all_channels(request, product_id):
    """Publish a product to all connected marketplace channels"""
    try:
        product = get_object_or_404(Product, id=product_id, user=request.user)
        
        marketplace_channels = ConnectedChannel.objects.filter(
            user=request.user,
            platform__in=['shopify', 'etsy', 'woocommerce'],
            status='active'
        )
        
        if not marketplace_channels:
            return JsonResponse({
                'success': False,
                'message': 'No marketplace channels connected'
            })
        
        results = []
        success_count = 0
        
        for channel in marketplace_channels:
            try:
                service = get_marketplace_service(channel)
                success, message = service.create_product(product)
                
                results.append({
                    'channel': channel.get_platform_display(),
                    'success': success,
                    'message': message
                })
                
                if success:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f'Channel {channel.platform} error: {str(e)}')
                results.append({
                    'channel': channel.get_platform_display(),
                    'success': False,
                    'message': str(e)
                })
        
        return JsonResponse({
            'success': success_count > 0,
            'message': f'Published to {success_count}/{len(marketplace_channels)} channels',
            'results': results
        })
        
    except Exception as e:
        logger.error(f'Bulk publishing error: {str(e)}', exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Bulk publishing failed: {str(e)}'
        })

@login_required
def product_listings_view(request, product_id):
    """View all listings for a product across channels"""
    product = get_object_or_404(Product, id=product_id, user=request.user)
    
    # Get all user's channels
    marketplace_channels = ConnectedChannel.objects.filter(
        user=request.user,
        platform__in=['shopify', 'etsy', 'woocommerce']
    ).order_by('platform')
    
    # Get existing listings
    listings = ProductListing.objects.filter(product=product)
    listing_map = {listing.channel_id: listing for listing in listings}
    
    # Prepare channel data with listing status
    channel_data = []
    for channel in marketplace_channels:
        listing = listing_map.get(channel.id)
        channel_data.append({
            'channel': channel,
            'listing': listing,
            'can_publish': channel.status == 'active',
            'status': listing.status if listing else 'not_published'
        })
    
    context = {
        'product': product,
        'channel_data': channel_data
    }
    return render(request, 'products/listings.html', context)