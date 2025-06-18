from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, ProductImage
from .forms import ProductForm, ProductImageFormSet
import openai
from django.conf import settings

@login_required
def product_list_view(request):
    """List all products for the current user"""
    products = Product.objects.filter(user=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'draft':
        products = products.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(products.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_products': products.count()
    }
    return render(request, 'products/list.html', context)

@login_required
def product_create_view(request):
    """Create a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        image_formset = ProductImageFormSet(
            request.POST, 
            request.FILES, 
            queryset=ProductImage.objects.none()
        )
        
        if form.is_valid() and image_formset.is_valid():
            product = form.save(commit=False)
            product.user = request.user
            product.save()
            
            # Save images
            for image_form in image_formset:
                if image_form.cleaned_data and not image_form.cleaned_data.get('DELETE'):
                    image = image_form.save(commit=False)
                    image.product = product
                    image.save()
            
            messages.success(request, f'Product "{product.title}" created successfully!')
            return redirect('products:detail', product.id)
    else:
        form = ProductForm()
        image_formset = ProductImageFormSet(queryset=ProductImage.objects.none())
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'action': 'Create'
    }
    return render(request, 'products/form.html', context)

@login_required
def product_detail_view(request, product_id):
    """View and edit product details"""
    product = get_object_or_404(Product, id=product_id, user=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        image_formset = ProductImageFormSet(
            request.POST, 
            request.FILES, 
            queryset=product.images.all()
        )
        
        if form.is_valid() and image_formset.is_valid():
            product = form.save()
            
            # Save images
            for image_form in image_formset:
                if image_form.cleaned_data:
                    if image_form.cleaned_data.get('DELETE'):
                        if image_form.instance.pk:
                            image_form.instance.delete()
                    else:
                        image = image_form.save(commit=False)
                        image.product = product
                        image.save()
            
            messages.success(request, f'Product "{product.title}" updated successfully!')
            return redirect('products:detail', product.id)
    else:
        form = ProductForm(instance=product)
        image_formset = ProductImageFormSet(queryset=product.images.all())
    
    context = {
        'product': product,
        'form': form,
        'image_formset': image_formset,
        'action': 'Update'
    }
    return render(request, 'products/form.html', context)

@login_required
def product_delete_view(request, product_id):
    """Delete a product"""
    product = get_object_or_404(Product, id=product_id, user=request.user)
    
    if request.method == 'POST':
        title = product.title
        product.delete()
        messages.success(request, f'Product "{title}" deleted successfully!')
        return redirect('products:list')
    
    context = {'product': product}
    return render(request, 'products/delete.html', context)

@login_required
def generate_ai_description(request, product_id):
    """Generate AI description for a product"""
    product = get_object_or_404(Product, id=product_id, user=request.user)
    
    if not settings.OPENAI_API_KEY:
        messages.error(request, 'AI features are not available at the moment.')
        return redirect('products:detail', product.id)
    
    try:
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Write a compelling product description for an e-commerce listing:
        
        Product Title: {product.title}
        Price: ${product.price}
        Current Description: {product.description or 'No description yet'}
        
        Create a professional, engaging description that:
        - Highlights key features and benefits
        - Appeals to potential customers
        - Is suitable for marketplace listings
        - Is around 100-150 words
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        
        ai_description = response.choices[0].message.content.strip()
        product.ai_generated_description = ai_description
        product.save()
        
        messages.success(request, 'AI description generated successfully!')
        
    except Exception as e:
        messages.error(request, f'Failed to generate AI description: {str(e)}')
    
    return redirect('products:detail', product.id)