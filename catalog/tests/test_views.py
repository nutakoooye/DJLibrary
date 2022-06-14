import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from ..models import Author, Book, BookInstance, Genre, Language


class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        number_of_authors = 13
        for author_num in range(number_of_authors):
            Author.objects.create(
                first_name=f'FName {author_num}',
                last_name=f'LName {author_num}'
            )

    def test_view_url_exists_at_desired_location(self):
        resp = self.client.get('/catalog/authors/')
        self.assertTrue(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('authors'))
        self.assertTrue(resp.status_code, 200)

    def test_view_uses_correct_template(self):
        resp = self.client.get(reverse('authors'))
        self.assertTrue(resp.status_code, 200)

        self.assertTemplateUsed(resp, 'catalog/author_list.html')

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('authors'))
        self.assertTrue(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertEqual(len(resp.context['author_list']), 10)

    def test_lists_all_authors(self):
        resp = self.client.get(reverse('authors') + '?page=2')
        self.assertTrue(resp.status_code, 200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertEqual(len(resp.context['author_list']), 3)


class LoanedBookInstancesByUserListViewTest(TestCase):
    def setUp(self) -> None:
        test_user1 = User.objects.create_user(username='User1', password='1111')
        test_user1.save()
        test_user2 = User.objects.create_user(username='User2', password='1111')
        test_user2.save()

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
        setup_book.save()
        number_of_book_copies = 30
        for book_copy_num in range(number_of_book_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy_num % 5)
            if book_copy_num % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            BookInstance.objects.create(
                book=setup_book,
                imprint='wefw',
                due_back=return_date,
                borrower=the_borrower,
                status='m'
            )

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('my-borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='User1', password='1111')
        resp = self.client.get(reverse('my-borrowed'))

        self.assertEqual(str(resp.context['user']), 'User1')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='User1', password='1111')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'User1')
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        get_ten_books = BookInstance.objects.all()[:10]
        for copy in get_ten_books:
            copy.status = 'o'
            copy.save()
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'User1')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('bookinstance_list' in resp.context)

        for book_item in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], book_item.borrower)
            self.assertEqual('o', book_item.status)

    def test_pages_ordered_by_due_date(self):
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='User1', password='1111')
        resp = self.client.get(reverse('my-borrowed'))
        self.assertEqual(str(resp.context['user']), 'User1')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(resp.context['bookinstance_list']), 10)

        last_date = 0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


class RenewBookInstancesViewTest(TestCase):
    def setUp(self) -> None:
        test_user1 = User.objects.create_user(username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password='12345')
        test_user2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        test_author = Author.objects.create(first_name='John', last_name='Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_language = Language.objects.create(name='English')
        test_book = Book.objects.create(title='Book Title', summary='My book summary', isbn='ABCDEFG',
                                        author=test_author, language=test_language, )
        # Создание жанра Create genre as a post-step
        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        # Создание объекта BookInstance для для пользователя test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                              due_back=return_date, borrower=test_user1, status='o')

        # Создание объекта BookInstance для для пользователя test_user2
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                              due_back=return_date, borrower=test_user2, status='o')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))

        # Check that it lets us login. We're a librarian, so we can view any users book
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uid = uuid.uuid4()
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': test_uid, }))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/book_renew_librarian.html')

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)
        date_3_week_in_the_future = datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(date_3_week_in_the_future, resp.context['form'].initial['due_back'])

    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)
        valid_date_in_the_future = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post((reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk})),
                                {'due_back': valid_date_in_the_future})
        self.assertRedirects(resp, reverse('all-borrowed'))

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)

        date_in_past = datetime.date.today() - datetime.timedelta(weeks=1)

        resp = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }),
                                {'due_back': date_in_past})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'due_back', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }))
        self.assertEqual(resp.status_code, 200)

        date_in_past = datetime.date.today() + datetime.timedelta(weeks=5)

        resp = self.client.post(reverse('renew-book-librarian', kwargs={'pk': self.test_bookinstance1.pk, }),
                                {'due_back': date_in_past})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'due_back', 'Invalid date - renewal more than 4 weeks ahead')


class AuthorCreateTest(TestCase):
    def setUp(self) -> None:
        test_user1 = User.objects.create_user(username='testuser1', password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password='12345')
        test_user2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 403)

    def test_redirect_if_logged_in_with_correct_permission(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)

    def test_uses_correct_template(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'catalog/author_form.html')

    def test_uses_correct_initial_date_of_death(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['form'].initial['date_of_death'], '12/10/2016')

    def test_success_redirect(self):
        login = self.client.login(username='testuser2', password='12345')
        resp = self.client.get(reverse('author-create'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(reverse('author-create'), {
            'first_name': 'bill',
            'last_name':'wefd',
            'date_of_death': '11/03/1899',
            'date_of_birth': '05/11/1834',
        })
        self.assertRedirects(resp, reverse('author-detail', kwargs={'pk':1}))
