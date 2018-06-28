from django.shortcuts import render, get_object_or_404
# Create your views here.
from .models import Book,Author,BookInstance,Genre
from django.views import generic
from django.contrib.auth.decorators import login_required

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView


from .forms import RenewBookForm
import datetime





@login_required
def index(request):
      num_books = Book.objects.all().count()
      num_instances = BookInstance.objects.all().count()

      num_instances_available = BookInstance.objects.filter(status__exact = 'a').count()

      num_authors = Author.objects.count()

      #Number of visitors to this view, as counted tin the session variable.
      #get the value of 'num_visits' session key, setting the value to 0 if it has not previoulsy been set.
      num_visits = request.session.get('num_visits',0)
      request.session['num_visits'] = num_visits + 1

      num_Chinesebooks = Book.objects.filter(language = 'CN').count()

      context = {
          'num_books':num_books,
          'num_instances': num_instances,
          'num_instances_available': num_instances_available,
          'num_authors':num_authors,
          'num_Chinesebooks':num_Chinesebooks,
          'num_visits':num_visits,

      }

      return render(
          request,
          'catalog/index.html',
          context,
      )

#a class based generic list view(ListView), as generic view already implmented most of the functions we need.
class BookListView(LoginRequiredMixin, generic.ListView):
    model = Book
    paginate_by = 10

    #by default, name of list of objects is 'object_list' OR 'book_list'. you can overriding it by -
    #context_object_name = 'my_book_list'  #your own name of the list

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
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact = 'o').order_by('due_back')


class LoanedBooksByStaffListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_staff.html'
    paginate_by = 10

    permission_required = ('catalog.can_mark_returned')

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact ='o').order_by('due_back')


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk = pk)

    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        #check if the form is valid:
        if form.is_valid():
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            return HttpResponseRedirect(reverse('catalog:all_borrowed'))

    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks = 3)
        form = RenewBookForm(initial={'renewal_date':proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html',{'form':form, 'bookinst':book_inst})


#class AuthorCreate(CreateView):
#    model = Author
#   fields = '__all__'

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = '__all__'
    initial ={'date_of_death':'12/10/2016',}
    permission_required = 'catalog.can_mark_returned'


class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('catalog:authors')

class BookCreate(CreateView):
    model = Book
    fields ='__all__'

class BookUpdate(UpdateView):
    model = Book
    fields = '__all__'

class BookDelete(DeleteView):
    model = Book
    success_url = reverse_lazy('catalog:books')

