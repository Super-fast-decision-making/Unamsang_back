from rest_framework.views import APIView
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from .serializers import ArticleSerializer, CommentSerializer, RatingSerializer
from .models import Article as ArticleModel, Rating
from .models import Comment as CommentModel
from .models import Rating as RatingModel
from django.db.models.query_utils import Q
from v_diffusion_pytorch.image_gen import run
import os
from rest_framework_simplejwt.authentication import JWTAuthentication
from datetime import datetime

today = datetime.now().date()

class ImageGenerationView(APIView):
    def post(self, request):
        prompt = request.data["prompt"]
        header_of_filename = run(request.user.username, prompt)
        images = []
        for i in range(4):
            images.append(f'media/images/{header_of_filename}_{i}.png')
        images.append(f'media/images/{header_of_filename}_finalgrid.png')

        image = f'media/images/{header_of_filename}'

        return Response({"msg": "Success", "images": image, "title": prompt})

    def delete(self, request, images):
        for image in images:
            os.remove(image)
        return Response({"msg": "delete success"})


class ArticleView(APIView):
    authentication_classes = [JWTAuthentication]
    def get(self, request):
        articles= ArticleModel.objects.all().order_by('-id')
        article_serializer = ArticleSerializer(articles, many=True)
        return Response(article_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        global header_of_filename

        try:
            request.data['user']=request.user.id
        except:
            pass  

        article_serializer = ArticleSerializer(data=request.data)
        if article_serializer.is_valid():
            article_serializer.save()
            return Response(article_serializer.data, status=status.HTTP_200_OK)
        return Response(article_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, obj_id):
        article = ArticleModel.objects.get(id=obj_id)
        article_serializer = ArticleSerializer(
            article, data=request.data, partial=True)

        if article_serializer.is_valid():
            article_serializer.save()
            return Response(article_serializer.data, status=status.HTTP_200_OK)
        return Response(article_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, obj_id):
        article = ArticleModel.objects.get(id=obj_id)
        article.delete()

        return Response({'message': '삭제되었습니다'}, status=status.HTTP_200_OK)


class ArticleSearchView(APIView):
    def get(self, request):
        words = request.query_params.get('words', '').strip()

        if words == '':
            return Response({'message': '검색어를 입력해 주세요.'}, status=status.HTTP_404_NOT_FOUND)
        words = words.split(' ')
        query = Q()
        for word in words:

            if word.strip() !="":
                query.add(Q(title__icontains=word.strip(), is_active=True, exposure_end_date__gte=today), Q.OR)
                query.add(Q(user__username__icontains=word.strip(), is_active=True, exposure_end_date__gte=today), Q.OR)

        articles = ArticleModel.objects.filter(query)

        if articles.exists():
            serializer = ArticleSerializer(articles, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK) 

        return Response({'message': '검색된 게시물이 없습니다.'}, status=status.HTTP_404_NOT_FOUND)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = CommentModel.objects.all()
    serializer_class = CommentSerializer
    
    def perform_create(self, serializer):
        serializer.save(user = self.request.user)
        return Response({"리뷰 작성 완료"})
    

class RatingViewSet(viewsets.ModelViewSet):

    queryset = RatingModel.objects.all()
    serializer_class = RatingSerializer
    
    def perform_create(self, serializer):
        user = self.request.user
        article_id = self.request.data['article']
        article = ArticleModel.objects.get(id=article_id)
        rating = self.request.data['rating']
        try:
            rating_model_target = RatingModel.objects.get(user=user, article=article)
        except:
            rating_model_target = False
        if rating_model_target:
            RatingModel(rating_model_target.id, rating=rating, user=user, article=article).save()
            return Response(status=status.HTTP_200_OK) # Response는 mixins.py에서 (viewset) 자동으로 주기때문에 의미가 없습니다..ㅜ
        serializer.save(user = self.request.user)
        return Response(status=status.HTTP_201_CREATED)
    
