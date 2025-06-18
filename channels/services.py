import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import ConnectedChannel, ProductListing
import logging

logger = logging.getLogger(__name__)

class BaseMarketplaceService:
    """Base class for marketplace integrations"""
    
    def __init__(self, channel):
        self.channel = channel
        self.platform = channel.platform
    
    def test_connection(self):
        """Test if the channel connection is working"""
        raise NotImplementedError
    
    def create_product(self, product):
        """Create a product on the marketplace"""
        raise NotImplementedError
    
    def update_product(self, product, listing):
        """Update an existing product on the marketplace"""
        raise NotImplementedError
    
    def delete_product(self, listing):
        """Delete a product from the marketplace"""
        raise NotImplementedError

class ShopifyService(BaseMarketplaceService):
    """Shopify marketplace integration"""
    
    def __init__(self, channel):
        super().__init__(channel)
        self.base_url = f"https://{channel.shop_name}.myshopify.com/admin/api/2023-10"
        self.headers = {
            'X-Shopify-Access-Token': channel.access_token,
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        """Test Shopify connection by fetching shop info"""
        try:
            response = requests.get(
                f"{self.base_url}/shop.json",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                shop_data = response.json().get('shop', {})
                self.channel.platform_username = shop_data.get('name', '')
                self.channel.shop_url = shop_data.get('domain', '')
                self.channel.status = 'active'
                self.channel.last_sync = timezone.now()
                self.channel.error_message = ''
                self.channel.save()
                return True, "Connection successful"
            else:
                error_msg = f"Shopify API error: {response.status_code}"
                self.channel.status = 'error'
                self.channel.error_message = error_msg
                self.channel.save()
                return False, error_msg
                
        except requests.RequestException as e:
            error_msg = f"Connection failed: {str(e)}"
            self.channel.status = 'error'
            self.channel.error_message = error_msg
            self.channel.save()
            return False, error_msg
    
    def create_product(self, product):
        """Create a product on Shopify"""
        try:
            # Prepare product data
            shopify_product = {
                "product": {
                    "title": product.title,
                    "body_html": product.description,
                    "vendor": product.user.business_name or product.user.display_name,
                    "product_type": "General",
                    "status": "active" if product.is_active else "draft",
                    "variants": [
                        {
                            "price": str(product.price),
                            "sku": product.sku or "",
                            "inventory_management": "shopify",
                            "inventory_quantity": 1
                        }
                    ]
                }
            }
            
            # Add images if available
            if product.images.exists():
                shopify_product["product"]["images"] = []
                for img in product.images.all():
                    shopify_product["product"]["images"].append({
                        "src": img.image.url,
                        "alt": img.alt_text or product.title
                    })
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/products.json",
                headers=self.headers,
                json=shopify_product,
                timeout=30
            )
            
            if response.status_code == 201:
                shopify_data = response.json().get('product', {})
                
                # Create or update listing
                listing, created = ProductListing.objects.get_or_create(
                    product=product,
                    channel=self.channel,
                    defaults={
                        'platform_product_id': str(shopify_data.get('id')),
                        'platform_url': f"https://{self.channel.shop_name}.myshopify.com/admin/products/{shopify_data.get('id')}",
                        'status': 'published',
                        'last_synced': timezone.now()
                    }
                )
                
                if not created:
                    listing.platform_product_id = str(shopify_data.get('id'))
                    listing.status = 'published'
                    listing.last_synced = timezone.now()
                    listing.error_message = ''
                    listing.save()
                
                return True, "Product created successfully on Shopify"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('errors', {})
                return False, f"Shopify error: {error_msg}"
                
        except Exception as e:
            logger.error(f"Shopify create product error: {str(e)}")
            return False, f"Failed to create product: {str(e)}"
    
    def update_product(self, product, listing):
        """Update an existing product on Shopify"""
        try:
            shopify_product = {
                "product": {
                    "id": int(listing.platform_product_id),
                    "title": listing.effective_title,
                    "body_html": listing.effective_description,
                    "status": "active" if product.is_active else "draft"
                }
            }
            
            response = requests.put(
                f"{self.base_url}/products/{listing.platform_product_id}.json",
                headers=self.headers,
                json=shopify_product,
                timeout=30
            )
            
            if response.status_code == 200:
                listing.status = 'published'
                listing.last_synced = timezone.now()
                listing.error_message = ''
                listing.save()
                return True, "Product updated successfully on Shopify"
            else:
                error_msg = f"Shopify update error: {response.status_code}"
                listing.status = 'failed'
                listing.error_message = error_msg
                listing.save()
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Failed to update product: {str(e)}"
            listing.status = 'failed'
            listing.error_message = error_msg
            listing.save()
            return False, error_msg

class EtsyService(BaseMarketplaceService):
    """Etsy marketplace integration"""
    
    def __init__(self, channel):
        super().__init__(channel)
        self.base_url = "https://openapi.etsy.com/v3"
        self.headers = {
            'Authorization': f'Bearer {channel.access_token}',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self):
        """Test Etsy connection by fetching user info"""
        try:
            response = requests.get(
                f"{self.base_url}/application/openapi-ping",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.channel.status = 'active'
                self.channel.last_sync = timezone.now()
                self.channel.error_message = ''
                self.channel.save()
                return True, "Connection successful"
            else:
                error_msg = f"Etsy API error: {response.status_code}"
                self.channel.status = 'error'
                self.channel.error_message = error_msg
                self.channel.save()
                return False, error_msg
                
        except requests.RequestException as e:
            error_msg = f"Connection failed: {str(e)}"
            self.channel.status = 'error'
            self.channel.error_message = error_msg
            self.channel.save()
            return False, error_msg
    
    def create_product(self, product):
        """Create a product on Etsy"""
        try:
            # Note: Etsy requires shop_id which should be stored during OAuth
            shop_id = self.channel.platform_user_id
            
            etsy_listing = {
                "quantity": 1,
                "title": product.title,
                "description": product.description,
                "price": float(product.price),
                "who_made": "i_did",  # Required for Etsy
                "when_made": "2020_2024",  # Required for Etsy
                "is_supply": False,
                "state": "active" if product.is_active else "draft"
            }
            
            response = requests.post(
                f"{self.base_url}/application/shops/{shop_id}/listings",
                headers=self.headers,
                json=etsy_listing,
                timeout=30
            )
            
            if response.status_code == 201:
                etsy_data = response.json()
                listing_id = etsy_data.get('listing_id')
                
                # Create listing record
                listing, created = ProductListing.objects.get_or_create(
                    product=product,
                    channel=self.channel,
                    defaults={
                        'platform_product_id': str(listing_id),
                        'platform_url': f"https://www.etsy.com/listing/{listing_id}",
                        'status': 'published',
                        'last_synced': timezone.now()
                    }
                )
                
                return True, "Product created successfully on Etsy"
            else:
                error_data = response.json() if response.content else {}
                return False, f"Etsy error: {error_data}"
                
        except Exception as e:
            logger.error(f"Etsy create product error: {str(e)}")
            return False, f"Failed to create product: {str(e)}"

def get_marketplace_service(channel):
    """Factory function to get the appropriate marketplace service"""
    services = {
        'shopify': ShopifyService,
        'etsy': EtsyService,
        # 'woocommerce': WooCommerceService,  # To be implemented
    }
    
    service_class = services.get(channel.platform)
    if service_class:
        return service_class(channel)
    else:
        raise ValueError(f"Unsupported marketplace: {channel.platform}")