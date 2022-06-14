from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('books/', views.BookListView.as_view(), name='books'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='book-detail'),
    path('authors/', views.AuthorListView.as_view(), name='authors'),
    path('authors/<int:pk>/', views.AuthorDetailView.as_view(), name='author-detail'),
    path('mybooks/', views.LoanedBooksByUserListView.as_view(), name='my-borrowed'),
    path('borrowed/', views.LoanedBooksStaffListView.as_view(), name='all-borrowed'),
    path('book/<pk>/renew/', views.renew_book_librarian, name='renew-book-librarian'),
    path('author/<pk>/update/', views.AuthorUpdate.as_view(), name='author-update'),
    path('author/create/', views.AuthorCreate.as_view(), name='author-create'),
    path('author/<pk>/delete/', views.AuthorDelete.as_view(), name='author-delete'),
    path('book/add/', views.add_book_librarian, name='book-add'),
    path('book/<pk>/update/', views.BookUpdate.as_view(), name='book-update'),
    path('book/<pk>/delete/', views.BookDelete.as_view(), name='book-delete'),
]
