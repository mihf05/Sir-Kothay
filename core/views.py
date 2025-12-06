import json
import urllib.request
from bs4 import BeautifulSoup
from django.shortcuts import render

def fetch_contributors():
    contributors_url = "https://api.github.com/repos/UIU-Developers-Hub/Sir-Kothay/contributors"
    contributors = []
    try:
        with urllib.request.urlopen(contributors_url) as response:
            data = json.loads(response.read().decode('utf-8'))
            for user in data:
                login = user['login']
                profile_url = user['html_url']
                image_url = user['avatar_url']
                # Fetch more info
                user_url = f"https://api.github.com/users/{login}"
                try:
                    with urllib.request.urlopen(user_url) as user_response:
                        user_data = json.loads(user_response.read().decode('utf-8'))
                        name = user_data.get('name', login)
                        bio = user_data.get('bio', '')
                        location = user_data.get('location', '')
                        company = user_data.get('company', '')
                        blog = user_data.get('blog', '')
                        followers = user_data.get('followers', 0)
                        public_repos = user_data.get('public_repos', 0)
                except:
                    name = login
                    bio = ''
                    location = ''
                    company = ''
                    blog = ''
                    followers = 0
                    public_repos = 0
                contributors.append({
                    'login': login,
                    'profileUrl': profile_url,
                    'imageUrl': image_url,
                    'name': name,
                    'bio': bio,
                    'location': location,
                    'company': company,
                    'blog': blog,
                    'followers': followers,
                    'public_repos': public_repos
                })
    except:
        contributors = []
    return contributors

def index_view(request):
    contributors = fetch_contributors()
    return render(request, 'index.html', {'contributors': contributors})

def about_view(request):
    contributors = fetch_contributors()
    return render(request, 'about.html', {'contributors': contributors})