import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Author, Book, Genre, Language, BookInstance
from django.urls import reverse


class AuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Author.objects.create(first_name='Bil', last_name='Geyts')

    def test_first_name_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('first_name').verbose_name
        self.assertEqual(field_label, 'first name')

    def test_last_name_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('last_name').verbose_name
        self.assertEqual(field_label, 'last name')

    def test_date_of_birth_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('date_of_birth').verbose_name
        self.assertEqual(field_label, 'date of birth')

    def test_date_of_death_label(self):
        author = Author.objects.get(id=1)
        field_label = author._meta.get_field('date_of_death').verbose_name
        self.assertEqual(field_label, 'Died')

    def test_first_name_max_length(self):
        author = Author.objects.get(id=1)
        max_length = author._meta.get_field('first_name').max_length
        self.assertEqual(max_length, 100)

    def test_object_name(self):
        author = Author.objects.get(id=1)
        expected_object_name = f'{author.first_name} {author.last_name}'
        self.assertEqual(expected_object_name, str(author))

    def test_get_absolute_url(self):
        author = Author.objects.get(id=1)
        self.assertEqual(author.get_absolute_url(), '/catalog/authors/1/')


class BookModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_author = Author.objects.create(first_name='Billi', last_name='Boykk')
        setup_language = Language.objects.create(name='Русский')
        setup_genre1 = Genre.objects.create(name='Фантастика1')
        setup_genre2 = Genre.objects.create(name='Фантастика2')
        book = Book.objects.create(title='Title',
                                   author=setup_author,
                                   summary='Some summary',
                                   isbn='123123211312',
                                   language=setup_language,
                                   )
        book.genre.set([setup_genre1, setup_genre2])

    def test_set_null_after_delete_author(self):
        Author.objects.get(id=1).delete()
        book = Book.objects.get(id=1)
        self.assertEqual(book.author, None)

    def test_display_genre(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.display_genre(), 'Фантастика1, Фантастика2')

    def test_get_absolute_url(self):
        book = Book.objects.get(id=1)
        self.assertEqual(book.get_absolute_url(), '/catalog/books/1/')

    def test_summary_max_nength(self):
        book = Book.objects.get(id=1)
        field_max_l = book._meta.get_field('summary').max_length
        expected_max_l = 1000
        self.assertEqual(field_max_l, expected_max_l)


class BookInstanceModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_author = Author.objects.create(first_name='Billi', last_name='Boykk')
        setup_language = Language.objects.create(name='Русский')
        setup_genre1 = Genre.objects.create(name='Фантастика1')
        setup_genre2 = Genre.objects.create(name='Фантастика2')
        setup_book = Book.objects.create(title='Title',
                                         author=setup_author,
                                         summary='Some summary',
                                         isbn='123123211312',
                                         language=setup_language,
                                         )
        setup_book.genre.set([setup_genre1, setup_genre2])
        User = get_user_model()
        setup_user = User.objects.create(username='boby', password='1111')
        BookInstance.objects.create(
            book=setup_book,
            imprint='Good',
            due_back=datetime.date.today(),
            status='o',
            borrower=setup_user
        )

    def test_is_overdue(self):
        import datetime
        book_i = BookInstance.objects.all()[0]
        book_i.due_back=datetime.date.today()-datetime.timedelta(days=20)
        self.assertTrue(book_i.is_overdue)

    def test_str(self):
        book_i = BookInstance.objects.all()[0]
        description = f"{book_i.id} ({book_i.book.title})"
        self.assertEqual(str(book_i), description)