from django.test import TestCase

from catalog.models import Author, BookInstance,Book, Genre
from django.contrib.auth.models import User
from django.urls import reverse
import datetime
from django.utils import timezone
from django.contrib.auth.models import Permission

class AuthorListViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        number_of_authors = 13
        for author_num in range(number_of_authors):
            Author.objects.create(first_name ='Christian %s' %author_num, last_name = 'Surname %s' %author_num,)


    def test_view_url_exits_at_desired_locationn(self):
        resp = self.client.get('/catalog/authors/')
        self.assertEqual(resp.status_code, 200)

    def test_view_url_accessible_by_name(self):
        resp = self.client.get(reverse('catalog:authors'))
        self.assertEqual(resp.status_code,200)

    def test_pagination_is_ten(self):
        resp = self.client.get(reverse('catalog:authors'))
        self.assertEqual(resp.status_code,200)
        self.assertTrue('is_paginated' in resp.context)
        self.assertTrue(resp.context['is_paginated'] == True)
        self.assertTrue(len(resp.context['author_list']) ==10)

    def test_lists_all_authors(self):
        resp = self.client.get(reverse('catalog:authors') + '?page=2')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['author_list']) == 3)


class LoandBookInstancesByUserListViewTest(TestCase):

    def setUp(self):
        # Create two users
        test_user1 = User.objects.create_user(username='testuser1',password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(username='testuser2', password = '12345')
        test_user2.save()

        #Create a book instance
        test_author = Author.objects.create(first_name = 'join', last_name = 'Smith')
        test_genre = Genre.objects.create(name='Fantasy')
        test_book = Book.objects.create(title = 'Book Title',summary = 'My book summary', isbn='12345678',author = test_author)

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)
        test_book.save()

        #Create 30 BookInstance objects
        number_of_books_copies = 30
        for book_copy in range(number_of_books_copies):
            return_date = timezone.now() + datetime.timedelta(days=book_copy % 5)
            if book_copy % 2:
                the_borrower = test_user1
            else:
                the_borrower = test_user2
            status='m'

            BookInstance.objects.create(book=test_book,imprint = 'Unlikely Imprint, 2016',due_back = return_date, borrower = the_borrower,status = status)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('catalog:my_borrowed'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/mybooks/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password ='12345' )
        resp = self.client.get(reverse('catalog:my_borrowed'))

        #check our user is logged in
        self.assertEqual(str(resp.context['user']),'testuser1')
        #check that we got a response 'success"
        self.assertEqual(resp.status_code, 200)

        #check we used the correct template
        self.assertTemplateUsed(resp, 'catalog/bookinstance_list_borrowed_user.html')

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username='testuser1', password='12345')
        resp = self.client.get(reverse('catalog:my_borrowed'))

        #check that initially we don't have any books in list (none on loan)
        self.assertEqual(str(resp.context['user']),'testuser1')
        self.assertEqual(resp.status_code, 200)


        self.assertTrue('bookinstance_list' in resp.context)
        self.assertEqual(len(resp.context['bookinstance_list']), 0)

        #now change all books to be on loan
        get_ten_books = BookInstance.objects.all()[:10]

        for copy in get_ten_books:
            copy.status ='o'
            copy.save()

        # check now we have borrowed books in the list
        resp = self.client.get(reverse('catalog:my_borrowed'))
        self.assertEqual(str(resp.context['user']), 'testuser1')
        self.assertEqual(resp.status_code, 200)

        self.assertTrue('bookinstance_list' in resp.context)

        for bookitem in resp.context['bookinstance_list']:
            self.assertEqual(resp.context['user'], bookitem.borrower)
            self.assertEqual('o', bookitem.status)

    def test_pages_ordered_by_due_date(self):
        #change all books to be on loan
        for copy in BookInstance.objects.all():
            copy.status = 'o'
            copy.save()

        login = self.client.login(username='testuser1',password='12345')
        resp = self.client.get(reverse('catalog:my_borrowed'))

        self.assertEqual(len(resp.context['bookinstance_list']),10)

        last_date=0
        for copy in resp.context['bookinstance_list']:
            if last_date == 0:
                last_date = copy.due_back
            else:
                self.assertTrue(last_date <= copy.due_back)


class RenewBookInstanceViewTest(TestCase):

    def setUp(self):
        #Create a user
        test_user1 = User.objects.create_user(username = 'testuser1',password='12345')
        test_user1.save()

        test_user2 = User.objects.create_user(username = 'testuser2',password='12345')
        test_user2.save()
        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        #Create a book
        test_author = Author.objects.create(first_name= 'John', last_name='Smith')
        test_genre = Genre.objects.create(name = 'Fantasy')
        test_book = Book.objects.create(title = 'Book Title',summary = 'My book summary', isbn='12345678',
                                        author = test_author, language = 'EN', )

        genre_objects_for_book = Genre.objects.all()
        test_book.genre.set(genre_objects_for_book)  # Direct assignment of many-to-many types is not allowed.
        test_book.save()

        #Create a BookInstance object for test_user1
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(book = test_book, imprint='Unlikely Imprint, 2016',
                                                              due_back=return_date, borrower= test_user1, status='o')
        return_date = datetime.date.today() + datetime.timedelta(days=5)
        self.test_bookinstance2 = BookInstance.objects.create(book=test_book, imprint='Unlikely Imprint, 2016',
                                                              due_back=return_date, borrower=test_user2, status='o')

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('catalog:renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk,}))
        #manually check redirect(Can't use assertRedirect, because the redirect URL is unpredictable)
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/accounts/login/'))

    def test_login_in_with_permission_borrowed_book(self):
        login = self.client.login(username='testuser2', password = '12345')
        resp = self.client.get(reverse('catalog:renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk,}))
        self.assertEqual(resp.status_code, 200)

    def test_HTTP404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uid = uuid.uuid4()
        login = self.client.login(username='testuser2', password = '12345')
        resp = self.client.get(reverse('catalog:renew-book-librarian', kwargs={'pk':test_uid}))
        self.assertEqual(resp.status_code, 404)

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username = 'testuser2', password = '12345')
        resp = self.client.get(reverse('catalog:renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)

        date_3_weeks_in_future= datetime.date.today() + datetime.timedelta(weeks=3)
        self.assertEqual(resp.context['form'].initial['renewal_date'], date_3_weeks_in_future)

    #check the view redirects to a list of all borrowed books if renewal succeeds.
    def test_redirects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username='testuser2',password='12345')
        valid_date_in_future = datetime.date.today() + datetime.timedelta(weeks=2)
        resp = self.client.post(reverse('catalog:renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk,}),{'renewal_date':valid_date_in_future})
        self.assertRedirects(resp, reverse('catalog:all_borrowed'))

    def test_form_invalid_renewal_date_past(self):
        login = self.client.login(username='testuser2', password='12345')
        date_in_past = datetime.date.today() - datetime.timedelta(weeks = 1)
        resp = self.client.post(reverse('catalog:renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk}),{'renewal_date':date_in_past})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal in past')

    def test_form_invalid_renewal_date_future(self):
        login = self.client.login(username='testuser2', password='12345')
        invalid_date_in_future = datetime.date.today() + datetime.timedelta(weeks = 5)
        resp = self.client.post(reverse('catalog:renew-book-librarian', kwargs={'pk':self.test_bookinstance1.pk}),{'renewal_date':invalid_date_in_future})
        self.assertEqual(resp.status_code, 200)
        self.assertFormError(resp, 'form', 'renewal_date', 'Invalid date - renewal more than 4 weeks ahead')


class AuthorCreateViewTest(TestCase):

    def setUp(self):
        #Create a user
        test_user1 = User.objects.create_user(username='testuser1',password='12345')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='12345')
        test_user2.save()

        permission = Permission.objects.get(name='Set book as returned')
        test_user2.user_permissions.add(permission)
        test_user2.save()

        #create an author
        date_of_birth = datetime.date.today() - datetime.timedelta(days = 50 *365)
        self.test_author1 = Author.objects.create(first_name='John', last_name = 'Smith',date_of_birth = date_of_birth)

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse('catalog:author_create'))
        self.assertRedirects(resp, '/accounts/login/?next=/catalog/author/create/' )

    def test_login_in_with_permission_author_create(self):
        login = self.client.login(username='testuser2',password='12345')
        resp = self.client.get(reverse('catalog:author_create'))
        self.assertEqual(resp.status_code,200)

    def test_redirects_to_detail_view_on_success(self):
        login = self.client.login(username='testuser2', password='12345')
        date_of_birth = datetime.date.today() - datetime.timedelta(days = 50*365)
        resp = self.client.post(reverse('catalog:author_create'),{'first_name':'John','last_name':'Smith','date_of_birth': date_of_birth} )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith('/catalog/author/'))


