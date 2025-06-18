from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from products.models import Product
from channels.models import ConnectedChannel, ProductListing
from social.models import SocialPost

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

def home_view(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    context = {
        'features': [
            {
                'title': 'List Once, Sell Everywhere',
                'description': 'Create one product and publish to Shopify, Etsy, WooCommerce instantly',
                'icon': '🚀'
            },
            {
                'title': 'Auto Social Media Posts',
                'description': 'Automatically post to Instagram, Facebook, TikTok with AI-generated captions',
                'icon': '📱'
            },
            {
                'title': 'AI-Powered Content',
                'description': 'Generate compelling product descriptions and hashtags with AI',
                'icon': '🤖'
            },
            {
                'title': 'Simple Analytics',
                'description': 'Track views, clicks, and engagement across all your channels',
                'icon': '📊'
            }
        ]
    }
    return render(request, 'core/home.html', context)

@login_required
def dashboard_view(request):
    """Main dashboard for authenticated users"""
    user = request.user
    
    # Get user's stats
    total_products = Product.objects.filter(user=user).count()
    active_products = Product.objects.filter(user=user, is_active=True).count()
    connected_channels = ConnectedChannel.objects.filter(user=user, status='active').count()
    total_listings = ProductListing.objects.filter(product__user=user).count()
    
    # Recent products
    recent_products = Product.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Recent social posts
    recent_posts = SocialPost.objects.filter(product__user=user).order_by('-created_at')[:5]
    
    # Connected channels breakdown
    channels = ConnectedChannel.objects.filter(user=user).values('platform').annotate(
        count=Count('id')
    )
    
    # Quick stats for charts/widgets
    marketplace_channels = ConnectedChannel.objects.filter(
        user=user, 
        platform__in=['shopify', 'etsy', 'woocommerce'],
        status='active'
    ).count()
    
    social_channels = ConnectedChannel.objects.filter(
        user=user, 
        platform__in=['instagram', 'facebook', 'tiktok'],
        status='active'
    ).count()
    
    context = {
        'stats': {
            'total_products': total_products,
            'active_products': active_products,
            'connected_channels': connected_channels,
            'total_listings': total_listings,
            'marketplace_channels': marketplace_channels,
            'social_channels': social_channels,
        },
        'recent_products': recent_products,
        'recent_posts': recent_posts,
        'channels': channels,
        'user': user,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def getting_started_view(request):
    """Onboarding flow for new users"""
    user = request.user
    
    # Check completion status
    has_products = Product.objects.filter(user=user).exists()
    has_channels = ConnectedChannel.objects.filter(user=user).exists()
    has_listings = ProductListing.objects.filter(product__user=user).exists()
    
    steps = [
        {
            'title': 'Create Your First Product',
            'description': 'Add a product with title, description, price, and images',
            'completed': has_products,
            'url': 'products:create' if not has_products else 'products:list',
            'icon': '📦'
        },
        {
            'title': 'Connect Your Channels',
            'description': 'Link your Shopify, Etsy, or social media accounts',
            'completed': has_channels,
            'url': 'channels:connect',
            'icon': '🔗'
        },
        {
            'title': 'Publish Your Product',
            'description': 'List your product on marketplaces and social media',
            'completed': has_listings,
            'url': 'products:list' if has_products else 'products:create',
            'icon': '🚀'
        }
    ]
    
    completion_percentage = sum(1 for step in steps if step['completed']) / len(steps) * 100
    
    context = {
        'steps': steps,
        'completion_percentage': completion_percentage,
        'is_completed': completion_percentage == 100
    }
    return render(request, 'core/getting_started.html', context)