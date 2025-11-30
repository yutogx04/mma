from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import Review
from products.models import Product

@login_required
def review_create_view(request, product_id):
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        
        token = request.session.get('access_token')
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        response = requests.post(
            "http://127.0.0.1:8000/api/reviews/create/",
            data={
                "product_id": product_id,
                "rating": rating,
                "comment": comment
            },
            headers=headers
        )
        
        if response.status_code == 201:
            return redirect('product_detail', product_id=product_id)
        else:
            product = get_object_or_404(Product, id=product_id)
            return render(request, "reviews/create.html", {
                'product': product,
                'error': 'Failed to create review'
            })
    
    product = get_object_or_404(Product, id=product_id)
    return render(request, "reviews/create.html", {
        'product': product
    })

# API Views
@api_view(['POST'])
@login_required
def review_create_api(request):
    product_id = request.data.get('product_id')
    rating = request.data.get('rating')
    comment = request.data.get('comment')
    
    product = get_object_or_404(Product, id=product_id)
    
    if Review.objects.filter(user=request.user, product=product).exists():
        return Response(
            {'error': 'You have already reviewed this product'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    review = Review.objects.create(
        user=request.user,
        product=product,
        rating=rating,
        comment=comment
    )
    
    return Response({
        'id': review.id,
        'message': 'Review created successfully'
    }, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@login_required
def review_delete_api(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    
    return Response(
        {'message': 'Review deleted successfully'},
        status=status.HTTP_204_NO_CONTENT
    )

@api_view(['GET'])
def product_reviews_api(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product)
    
    data = [{
        'id': review.id,
        'user_name': review.user.username,
        'rating': review.rating,
        'comment': review.comment,
        'created_at': review.created_at
    } for review in reviews]
    
    return Response(data)