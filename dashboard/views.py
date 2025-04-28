from django.shortcuts import render
from . forms import *
from django import contrib
from django.core.checks import messages

from django.contrib import messages
from django.shortcuts import redirect
from django.views import generic
import requests
from bs4 import BeautifulSoup
import wikipedia
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
    return render(request, 'dashboard/home.html')
    
@login_required
def notes(request):
    if request.method == 'POST':
        form = NotesForm(request.POST)
        if form.is_valid():
            notes = Notes ( user = request.user, title = request.POST['title'], description = request.POST['description'])
            notes.save()
        messages.success(request, f"Notes added from {request.user.username} successfully!")
        return redirect('notes') 
   
    else:
        form = NotesForm()
    notes = Notes.objects.filter(user=request.user)
    context = {'notes': notes, 'form': form}
    return render(request, 'dashboard/notes.html', context)

@login_required
def delete_note(request, pk=None):
    Notes.objects.get(id=pk).delete()
    messages.success(request, f"Notes deleted successfully!")
    return redirect('notes')

class NotesDeatilsView(generic.DetailView):
    model = Notes

@login_required
def homework(request):
    if request.method == 'POST':
        form = HomeworkForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            homeworks = Homework ( user = request.user, subject = request.POST['subject'], title = request.POST['title'], description = request.POST['description'], due = request.POST['due'], is_finished = finished)
            homeworks.save()
            messages.success(request, f"Homework added from {request.user.username} successfully!")
    else:
        form = HomeworkForm()
    homework = Homework.objects.filter(user=request.user)
    if len(homework) == 0:
        homework_done = True
    else:
        homework_done = False

    context = {'homeworks': homework, 'homework_done': homework_done, 'form': form}
    return render(request, 'dashboard/homework.html', context)

@login_required
def update_homework(request, pk=None):
    homework = Homework.objects.get(id=pk)
    if homework.is_finished == True:
        homework.is_finished = False
    else:
        homework.is_finished = True
    homework.save()
    return redirect('homework')

@login_required
def delete_homework(request, pk=None):
    Homework.objects.get(id=pk).delete()
    messages.success(request, f"Homework deleted successfully!")
    return redirect('homework')

def youtube(request):
    result_list = []
    if request.method == 'POST':
        form = DashboardForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['text']
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            response = requests.get(search_url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # YouTube search results are usually inside the <script> tags with JSON data.
            # We need to locate the correct script tag containing search results.
            
            # Search for the first <script> tag containing the initial search data
            scripts = soup.find_all('script')
            for script in scripts:
                if 'var ytInitialData' in str(script):
                    # Extract JSON data from script
                    start = script.string.find('var ytInitialData =') + len('var ytInitialData =')
                    end = script.string.find('};', start) + 1
                    json_data = script.string[start:end]
                    
                    # Convert to JSON object
                    import json
                    data = json.loads(json_data)

                    # Now extract the video data
                    video_results = data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']
                    
                    # Parse video details from JSON data
                    for video in video_results:
                        try:
                            video_data = video['videoRenderer']
                            title = video_data['title']['runs'][0]['text']
                            link = f"https://www.youtube.com/watch?v={video_data['videoId']}"
                            thumbnail = video_data['thumbnail']['thumbnails'][0]['url']
                            duration = video_data['lengthText']['simpleText']
                            channel = video_data['ownerText']['runs'][0]['text']
                            views = video_data['viewCountText']['simpleText']
                            published = video_data['publishedTimeText']['simpleText']
                            description = video_data.get('descriptionSnippet', {}).get('runs', [{}])[0].get('text', '')
                            
                            result_list.append({
                                'title': title,
                                'duration': duration,
                                'thumbnail': thumbnail,
                                'channel': channel,
                                'link': link,
                                'views': views,
                                'published': published,
                                'description': description,
                            })
                            if len(result_list) >= 10:
                                break
                        except KeyError:
                            continue  # If the video doesn't have all required data, skip it.

    else:
        form = DashboardForm()
        
    context = {
        'form': form,
        'results': result_list
    }
    return render(request, 'dashboard/youtube.html', context)

@login_required
def todo(request):
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            todos = Todo ( user = request.user, title = request.POST['title'], is_finished = finished)
            todos.save()
            messages.success(request, f"Todo added from {request.user.username} successfully!")
    else:
        form = TodoForm()
    todo = Todo.objects.filter(user=request.user)
    if len(todo) == 0:
        todo_done = True
    else:
        todo_done = False

    context = {'todos': todo, 'todo_done': todo_done, 'form': form}
    return render(request, 'dashboard/todo.html', context)

@login_required
def update_todo(request, pk=None):
    todo = Todo.objects.get(id=pk)
    if todo.is_finished == True:
        todo.is_finished = False
    else:
        todo.is_finished = True
    todo.save()
    return redirect('todo')

@login_required
def delete_todo(request, pk=None):
    Todo.objects.get(id=pk).delete()
    messages.success(request, f"Todo deleted successfully!")
    return redirect('todo')

def books(request):
    result_list = []
    if request.method == 'POST':
        form = DashboardForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['text']
            search_url = f"https://www.googleapis.com/books/v1/volumes?q={query.replace(' ', '+')}&maxResults=10"
            
            response = requests.get(search_url)
            data = response.json()

            # Parse the book details from the API response
            if 'items' in data:
                for book in data['items']:
                    try:
                        volume_info = book['volumeInfo']
                        title = volume_info.get('title', 'No Title Available')
                        subtitle = volume_info.get('subtitle', 'No Subtitle Available')
                        description = volume_info.get('description', 'No Description Available')
                        category = volume_info.get('categories', ['Unknown Category'])[0]
                        page_count = volume_info.get('pageCount', 'N/A')
                        rating = volume_info.get('averageRating', 'N/A')
                        thumbnail = volume_info.get('imageLinks', {}).get('thumbnail', '')
                        info_link = volume_info.get('infoLink', '#')
                        
                        result_list.append({
                            'title': title,
                            'subtitle': subtitle,
                            'description': description,
                            'category': category,
                            'pages': page_count,
                            'rating': rating,
                            'thumbnail': thumbnail,
                            'link': info_link,
                        })
                    except KeyError:
                        continue  # Skip if any data is missing

    else:
        form = DashboardForm()

    context = {
        'form': form,
        'results': result_list
    }
    return render(request, 'dashboard/books.html', context)

def dictionary(request):
    context = {}
    
    if request.method == 'POST':
        form = DashboardForm(request.POST)
        text = request.POST.get('text')
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{text}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            try:
                entry = data[0]
                phonetic = ""
                audio = ""

                # Get first non-empty phonetic
                for ph in entry.get("phonetics", []):
                    if ph.get("text"):
                        phonetic = ph.get("text")
                    if ph.get("audio"):
                        audio = ph.get("audio")
                        break

                meaning = entry.get("meanings", [])[0]
                definition_data = meaning.get("definitions", [])[0]

                context = {
                    'form': form,
                    'input': text,
                    'phonetics': phonetic,
                    'audio': audio,
                    'definition': definition_data.get('definition', 'No definition available.'),
                    'example': definition_data.get('example', 'No example available.'),
                    'synonyms': definition_data.get('synonyms', []),
                }

            except (IndexError, KeyError, TypeError):
                context = {
                    'form': form,
                    'input': text,
                    'definition': 'Definition not found.',
                    'example': 'Example not available.',
                    'synonyms': [],
                }
        else:
            context = {
                'form': form,
                'input': text,
                'definition': 'Word not found or API request failed.',
                'example': '',
                'synonyms': [],
            }
    else:
        form = DashboardForm()
        context = {'form': form}

    return render(request, 'dashboard/dictionary.html', context)

def wiki(request):
    if request.method == 'POST':
        form = DashboardForm(request.POST)
        text = request.POST.get('text')
        search = wikipedia.page(text)
        context = {
            'form': form,
            'title': search.title,
            'link': search.url,
            'details': search.summary,
        }
        return render(request, 'dashboard/wiki.html', context)
    else:
        form = DashboardForm()
        context = {'form': form}

    return render(request, 'dashboard/wiki.html', context)

def conversion(request):
    if request.method == 'POST':
        form = ConversionForm(request.POST)
        if request.POST['measurement'] == 'length':
            measurement_form = ConversionLengthForm()
            context = {'form': form, 'm_form': measurement_form, 'input': True}
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'yard' and second == 'foot':
                        answer = f'{input} yard = {int(input) * 3} foot'
                    if first == 'foot' and second == 'yard':
                        answer = f'{input} foot = {int(input) / 3} yard'
                    context = {'form': form, 'm_form': measurement_form, 'input': True, 'answer': answer}
        if request.POST['measurement'] == 'mass':
            measurement_form = ConversionMassForm()
            context = {'form': form, 'm_form': measurement_form, 'input': True}
            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST['input']
                answer = ''
                if input and int(input) >= 0:
                    if first == 'pound' and second == 'kilogram':
                        answer = f'{input} pound = {int(input) * 0.453592} kilogram'
                    if first == 'kilogram' and second == 'pound':
                        answer = f'{input} kilogram = {int(input) * 2.20462} pound'
                    context = {'form': form, 'm_form': measurement_form, 'input': True, 'answer': answer}

    else:
        form = ConversionForm()
        context = {'form': form, 'input': False}
    return render(request, 'dashboard/conversion.html', context)

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f"Account created for {username} successfully!")
            return redirect('login')
    else:
        form = UserRegistrationForm()
    context = {'form': form}
    return render(request, 'dashboard/register.html', context)


@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished=False, user=request.user)
    todos = Todo.objects.filter(is_finished=False, user=request.user)
    if len(homeworks) == 0:
        homework_done = True
    else:
        homework_done = False
    if len(todos) == 0:
        todos_done = True
    else:
        todos_done = False
    context = { 'homeworks': homeworks, 'homework_done': homework_done, 'todos': todos, 'todos_done': todos_done}
    return render(request, 'dashboard/profile.html', context)

def logout_view(request):
    logout(request)
    return render(request, 'dashboard/logout.html')

def your_view(request):
    active_urls = ['books', 'wiki', 'dictionary', 'youtube', 'todo', 'homework', 'notes', 'conversion']
    return render(request, 'your_template.html', {'active_urls': active_urls})