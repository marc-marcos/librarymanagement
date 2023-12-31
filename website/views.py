from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout

from website.models import Book, Transaction
from .forms import AddBookForm, ISBNForm, LoginForm, SignUpForm

from . import logic
import isbnlib
import random

# Create your views here.


def index(request):
    books = Book.objects.all().filter(in_house=True)
    return render(request, "index.html", {'books': books})


def logout_view(request):
    if (request.user.is_authenticated):
        logout(request)
        messages.success(request, "Logged out successfully!")
        return redirect("index")

    else:
        messages.error(request, "You are not logged in.")
        return redirect("index")


def login_view(request):
    if (request.user.is_authenticated):
        pass

    else:
        if (request.method == "POST"):
            form = LoginForm(request.POST)
            if (form.is_valid()):
                username = form.cleaned_data['username']
                password = form.cleaned_data['password']

                authenticated_user = authenticate(
                    username=username, password=password)

                if (authenticated_user is not None):
                    login(request, authenticated_user)
                    messages.success(request, "Logged in successfully!")
                    return redirect("index")

                else:
                    messages.error(request, "Invalid username or password.")
                    return redirect("login")

        else:
            form = LoginForm()
        return render(request, "login.html", {"form": form})


def addbook(request):
    if (request.user.is_authenticated):
        if (request.user.is_superuser):
            if (request.method == "POST"):
                form = AddBookForm(request.POST)
                if (form.is_valid()):
                    # book = form.save(commit=False)
                    # book.in_house = True
                    # book.save()
                    form.save()
                    messages.success(request, "Book added successfully!")
                    return redirect("index")

            else:
                form = AddBookForm()
            return render(request, "addbook.html", {"form": form})

        else:
            messages.error(
                request, "You need to be a superuser to be able to add books.")
            return redirect("index")

    else:
        messages.error(
            request, "You need to be logged in to access this resource.")
        return redirect("index")


def register_view(request):
    if (request.user.is_authenticated):
        pass

    else:
        if (request.method == "POST"):
            form = SignUpForm(request.POST)
            if (form.is_valid()):
                user = form.save()
                login(request, user)
                messages.success(request, "Account created successfully!")
                return redirect("index")

        else:
            form = SignUpForm()
        return render(request, "register.html", {"form": form})


def read_isbn(request, isbn):
    metadata = logic.extract_metadata_from_isbn(isbnlib.clean(isbn))
    print(metadata)

    if (len(metadata) != 0):
        if (request.user.is_authenticated):
            if (request.user.is_superuser):
                if (request.method == "POST"):
                    form = AddBookForm(request.POST)
                    if (form.is_valid()):
                        form.save()
                        messages.success(request, "Book added successfully!")
                        return redirect("index")

                else:
                    form = AddBookForm(
                        {"isbn": isbn, "title": metadata["Title"], "author": metadata["Authors"][0], "n_pages": random.randint(100, 400)})
                return render(request, "addbook.html", {"form": form})

            else:
                messages.error(
                    request, "You need to be a superuser to be able to add books.")
                return redirect("index")

        else:
            messages.error(
                request, "You need to be logged in to access this resource.")
            return redirect("index")

    else:
        return redirect("addbook")


def book(request, book_id):
    book = Book.objects.get(id=book_id)
    transactions = Transaction.objects.all().filter(book=book, returned=True)

    return render(request, "book.html", {"book": book, "transactions": transactions})


def get_book(request, book_id):
    if (request.user.is_authenticated):
        book = Book.objects.get(id=book_id)
        if (book.in_house):
            book.in_house = False
            book.retired_by = request.user
            book.save()
            t = Transaction(book=book, user=request.user, returned=False)
            t.save()
            messages.success(request, "Book retired successfully!")
            return redirect("index")

        else:
            messages.error(request, "Book is not in house.")
            return redirect("index")

    else:
        messages.error(request, "You need to be logged in to withdraw books.")
        return redirect("index")


def return_book(request, book_id):
    if (request.user.is_authenticated):
        book = Book.objects.get(id=book_id)
        if (not book.in_house):
            if (book.retired_by == request.user):
                book.in_house = True
                book.retired_by = None
                book.save()
                t = Transaction(book=book, user=request.user, returned=True)
                t.save()
                messages.success(request, "Book returned successfully!")
                return redirect("index")

            else:
                messages.error(
                    request, "You can't return a book that you didn't withdraw.")
                return redirect("index")

        else:
            messages.error(request, "Book is in house.")
            return redirect("index")

    else:
        messages.error(request, "You need to be logged in to return books.")
        return redirect("index")


def profile(request):
    if (request.user.is_authenticated):
        books = Book.objects.all().filter(retired_by=request.user)
        return render(request, "profile.html", {"user": request.user, "books": books})

    else:
        messages.error(
            request, "You need to be logged in to access your profile.")
        return redirect('index')


def transactions(request):
    if (request.user.is_superuser):
        transactions = Transaction.objects.all()
        transactions = transactions[::-1]
        return render(request, "transactions.html", {"transactions": transactions})

    else:
        messages.error(
            request, "You need to be a superuser to access the transactions log.")
        return redirect("index")

def delete_all_transactions(request):
    if (request.user.is_superuser):
        Transaction.objects.all().delete()
        messages.success(request, "All transactions deleted successfully!")
        return redirect("transactions")

    else:
        messages.error(
            request, "You need to be a superuser to access the transactions log.")
        return redirect("index")

def withdrawn_books(request):
    if (request.user.is_superuser):
        books = Book.objects.all().filter(in_house=False)
        return render(request, "withdrawn_books.html", {"books": books})

    else:
        messages.error(
            request, "You need to be superuser to access the withdrawn books.")
        return redirect("index")

def auto_isbn(request):
    if request.method == 'POST':
        form = ISBNForm(request.POST)
        if form.is_valid():
            # Redirect to the read_isbn view with the entered ISBN
            isbn = form.cleaned_data['isbn']
            return redirect('read_isbn', isbn=isbn)
    else:
        form = ISBNForm()
    return render(request, 'auto_isbn.html', {'form': form})
