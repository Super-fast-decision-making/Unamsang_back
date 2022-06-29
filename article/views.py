from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from .serializers import ArticleSerializer
from .models import Article as ArticleModel
from django.db.models.query_utils import Q

# Create your views here.
class ArticleView(APIView):

    def get(self, request):
        user =request.user
        articles= ArticleModel.objects.all()
        article_serializer = ArticleSerializer(articles, many=True)       

        return Response(article_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        request.data['user'] = user.id
        article_serializer = ArticleSerializer(data=request.data)
        print(article_serializer)
        if article_serializer.is_valid():
            article_serializer.save()
            return Response(article_serializer.data, status=status.HTTP_200_OK)
        return Response(article_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        return Response({'message': 'put입니다'})
        
    def delete(self, request):
        return Response({'message': 'delete입니다'})
    
class ArticleSearchView(APIView):
    def get(self, request):
        words = request.query_params.getlist('words', '')
        print("words = ", end=""), print(words)

        query = Q()
        for word in words:
            if word.strip() !="":
                query.add(Q(title__icontains=word.strip()), Q.OR)
                query.add(Q(user__username__icontains=word.strip()), Q.OR)
        articles = ArticleModel.objects.filter(query)
        
        if articles.exists():
            serializer = ArticleSerializer(articles, many=True)
            return Response(serializer.data) 

        return Response(status=status.HTTP_404_NOT_FOUND)
