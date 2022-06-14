import datetime
import random

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from .forms import RenewBookModelForm, AddBookModelForm
from .models import Book, BookInstance, Author, Genre, Language


# Create your views here.

def index(request):
    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.all().count()
    num_genres = Genre.objects.all().count
    num_book_title_with_word = Book.objects.filter(title__iregex='\w+').count()
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_genres': num_genres,
        'num_book_title_with_word': num_book_title_with_word,
        'num_visits': num_visits
    }
    return render(request, 'index.html', context)


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RenewBookModelForm(request.POST)
        if form.is_valid():
            book_inst.due_back = form.cleaned_data["due_back"]
            book_inst.save()
            return HttpResponseRedirect(reverse("all-borrowed"))
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})
    return render(request, 'catalog/book_renew_librarian.html', context={'form': form, 'bookinst': book_inst})


def generate_isbn():
    isbn = ''
    for i in range(13):
        isbn += str(random.randint(0, 9))
    return isbn


@permission_required('catalog.can_mark_returned')
def add_book_librarian(request):
    if request.method == 'POST':
        form = AddBookModelForm(request.POST)
        if form.is_valid():
            book = Book.objects.create()
            book.title = form.cleaned_data['title']
            book.author = form.cleaned_data['author']
            book.summary = form.cleaned_data['summary']
            book.genre.set(form.cleaned_data['genre'])
            book.isbn = form.cleaned_data['isbn']
            book.language = form.cleaned_data['language']
            book.save()
            return HttpResponseRedirect(reverse('book-detail', args=[book.id]))
    else:
        form = AddBookModelForm(initial={'isbn': generate_isbn()})
    return render(request, 'catalog/book_form.html', context={'form': form})


class BookListView(generic.ListView):
    model = Book
    paginate_by = 10


class BookDetailView(generic.DetailView):
    model = Book


class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author


class LoanedBooksByUserListView(LoginRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')


class LoanedBooksStaffListView(PermissionRequiredMixin, generic.ListView):
    permission_required = 'catalog.can_mark_returned'

    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_staff.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')


class AuthorCreate(PermissionRequiredMixin, generic.edit.CreateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    initial={'date_of_death':'12/10/2016',}
    fields = '__all__'


class AuthorUpdate(PermissionRequiredMixin, generic.edit.UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    fields = '__all__'


class AuthorDelete(PermissionRequiredMixin, generic.edit.DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Author
    success_url = reverse_lazy('authors')


class BookUpdate(PermissionRequiredMixin, generic.UpdateView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    fields = '__all__'


class BookDelete(PermissionRequiredMixin, generic.DeleteView):
    permission_required = 'catalog.can_mark_returned'
    model = Book
    success_url = reverse_lazy('books')
